"""
Simple baseline agents for TORCS using gym-torcs.

Includes:
1. PurePursuitAgent - Rule-based steering using track sensors
2. RandomAgent - Sanity check agent
3. StableBaselines3 wrapper - Template for RL algorithms
"""

import sys
import numpy as np
from typing import Dict, Tuple

# Save original sys.argv before gym_torcs reads it
original_argv = sys.argv.copy()
sys.argv = [sys.argv[0]]

import gym  # gym-torcs uses old gym API
import gym_torcs

# Restore sys.argv
sys.argv = original_argv


class PurePursuitAgent:
    """
    Rule-based pure pursuit steering controller for TORCS.
    
    Based on: http://www.wayneparrott.com/coding-a-pure-pursuit-steering-controller-for-a-torcs-racing-bot/
    
    The pure pursuit algorithm:
    1. Look ahead using track sensor data (LIDAR)
    2. Find the furthest sensor reading (variable lookahead distance)
    3. Compute steering angle toward that point
    4. Apply speed control via PD controller
    """
    
    def __init__(
        self,
        max_steering_angle: float = 0.366519,  # ~21 degrees in radians
        max_speed: float = 250.0,  # km/h
        min_speed: float = 30.0,   # km/h
        speed_kp: float = 0.5,     # PD controller proportional gain
        speed_kd: float = 0.1,     # PD controller derivative gain
        track_edge_safety: float = 0.5,  # Safety margin for track edges
    ):
        self.max_steering_angle = max_steering_angle
        self.max_speed = max_speed
        self.min_speed = min_speed
        self.speed_kp = speed_kp
        self.speed_kd = speed_kd
        self.track_edge_safety = track_edge_safety
        
        self.prev_speed_error = 0.0
    
    def predict(self, obs: Dict) -> np.ndarray:
        """
        Predict steering, acceleration/brake, and gear from observation.
        
        Args:
            obs: Dictionary of sensor observations from gym_torcs
                 Keys: 'angle', 'track', 'trackPos', 'speedX', 'speedY', 'speedZ',
                       'wheelSpinVel', 'rpm', 'opponents', 'damage', 'fuel', 'gear'
        
        Returns:
            action: np.array [steering, accel_or_brake, gear]
                   steering: [-1, 1] (-1=full right, 1=full left)
                   accel_or_brake: [-1, 1] (negative=brake, positive=accel)
                   gear: -1 to 6 (0=neutral)
        """
        
        # Pure pursuit steering: use furthest track sensor to determine goal point
        track_sensors = obs['track']  # 19 range finder sensors in front
        max_sensor_idx = np.argmax(track_sensors)
        max_sensor_dist = track_sensors[max_sensor_idx]
        
        # Map sensor index to angle ([-90, 90] degrees w.r.t car axis)
        # 19 sensors spanning -90 to +90 degrees (every ~10 degrees)
        sensor_angle = -90 + (max_sensor_idx * 180 / 18)  # degrees
        sensor_angle_rad = np.radians(sensor_angle)
        
        # Compute steering angle using pure pursuit
        # Goal point in front of car; steering angle inversely proportional to lookahead distance
        lookahead_dist = max(max_sensor_dist, 10.0)  # Minimum lookahead
        steering_angle = np.arctan(2.0 * np.sin(sensor_angle_rad) / lookahead_dist)
        
        # Normalize steering to [-1, 1]
        steering = np.clip(steering_angle / self.max_steering_angle, -1.0, 1.0)
        
        # Apply damping correction based on track position to avoid drift
        # trackPos: 0=on centerline, -1=right edge, +1=left edge
        track_pos = obs['trackPos']
        if abs(track_pos) > self.track_edge_safety:
            # Car is drifting toward edge; correct toward centerline
            correction = np.sign(track_pos) * 0.1
            steering = np.clip(steering + correction, -1.0, 1.0)
        
        # Speed control using PD controller
        current_speed = obs['speedX']  # km/h
        
        # Braking zone: reduce target speed based on how close we are to obstacles
        # If max sensor reading is small, we're approaching a turn
        braking_zone = max_sensor_dist < current_speed / 1.5
        target_speed = (
            max(self.min_speed, max_sensor_dist)
            if braking_zone
            else self.max_speed
        )
        
        # PD controller for speed
        speed_error = target_speed - current_speed
        speed_diff = speed_error - self.prev_speed_error
        self.prev_speed_error = speed_error
        
        # Compute acceleration (positive) or braking (negative)
        accel_brake = self.speed_kp * speed_error + self.speed_kd * speed_diff
        accel_brake = np.clip(accel_brake / 100.0, -1.0, 1.0)  # Normalize
        
        # Gear selection: simple heuristic
        gear = self._select_gear(current_speed, obs['rpm'])
        
        return np.array([steering, accel_brake, gear], dtype=np.float32)
    
    def _select_gear(self, speed: float, rpm: float) -> int:
        """Simple gear selection heuristic."""
        if speed < 10:
            return 1  # First gear for low speeds
        elif speed < 50:
            return 2
        elif speed < 100:
            return 3
        elif speed < 150:
            return 4
        elif speed < 200:
            return 5
        else:
            return 6  # Top gear


class RandomAgent:
    """Sanity check agent that outputs random actions."""
    
    def predict(self, obs: Dict) -> np.ndarray:
        # Random steering, accel/brake, gear
        steering = np.random.uniform(-1, 1)
        accel_brake = np.random.uniform(-1, 1)
        gear = np.random.randint(-1, 7)
        return np.array([steering, accel_brake, gear], dtype=np.float32)


def observation_preprocessor(dict_obs: Dict) -> np.ndarray:
    """
    Preprocess gym_torcs dictionary observation into a flat array.
    
    Useful for RL algorithms that expect flat state vectors.
    """
    return np.hstack((
        dict_obs['angle'],
        dict_obs['track'],           # 19-dim
        dict_obs['trackPos'],
        dict_obs['speedX'],
        dict_obs['speedY'],
        dict_obs['speedZ'],
        dict_obs['wheelSpinVel'],    # 4-dim
        dict_obs['rpm'],
        dict_obs['opponents'],       # 36-dim
    )).astype(np.float32)


def main():
    """Example: run pure pursuit agent in TORCS via gym_torcs."""
    
    # Create environment
    env = gym.make(
        'Torcs-v0',
        vision=False,
        rendering=True,
        obs_preprocess_fn=observation_preprocessor,
    )
    
    agent = PurePursuitAgent()
    
    # Run one episode
    obs = env.reset()
    done = False
    total_reward = 0.0
    step_count = 0
    max_steps = 3000  # ~60 seconds at 50 FPS
    
    print("Starting pure pursuit episode...")
    while not done and step_count < max_steps:
        # Get action from agent
        action = agent.predict(obs)
        
        # Step environment
        obs, reward, done, info = env.step(action)
        
        total_reward += reward
        step_count += 1
        
        if step_count % 500 == 0:
            print(f"Step {step_count}: reward={total_reward:.1f}, speed={obs['speedX']:.1f} km/h")
    
    print(f"\nEpisode finished!")
    print(f"Total steps: {step_count}")
    print(f"Total reward: {total_reward:.2f}")
    
    env.close()


if __name__ == '__main__':
    main()
