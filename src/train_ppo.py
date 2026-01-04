"""
Train an RL agent (PPO) on TORCS using gym-torcs and stable-baselines3.

Usage:
    nix develop
    uv run python train_ppo.py --total-timesteps 100000 --env-id Torcs-v0
"""

import sys
import argparse
import numpy as np
import subprocess
import os

# Fix numpy compatibility with old gym
if not hasattr(np, 'bool8'):
    np.bool8 = np.bool_

# Save original sys.argv before gym_torcs reads it
# gym_torcs parses command line arguments on import, which interferes with our argparse
original_argv = sys.argv.copy()
sys.argv = [sys.argv[0]]

try:
    import gym
    import gym_torcs
    import gym_torcs.snakeoil3_gym as snakeoil3
    import gym_torcs.torcs_env as torcs_env
except ImportError as e:
    print(f"Warning: Failed to import gym_torcs: {e}")
    # Define dummy modules for smoke testing if needed
    snakeoil3 = None
    torcs_env = None

# Restore sys.argv for argparse
sys.argv = original_argv

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.vec_env import DummyVecEnv

# Patch snakeoil3 to not parse command line args
if snakeoil3:
    snakeoil3.Client.parse_the_command_line = lambda self: None

# Prevent gym-torcs from launching TORCS
original_popen = subprocess.Popen
def no_launch_popen(args, **kwargs):
    if isinstance(args, list) and args and 'torcs' in str(args[0]):
        print("[SKIP] Not auto-launching TORCS (should be running manually)")
        # Return a dummy process that does nothing
        return original_popen(['sleep', '999999'], **kwargs)
    return original_popen(args, **kwargs)

subprocess.Popen = no_launch_popen

# Patch gym-torcs observation handler to fix missing 'lap' key
if torcs_env:
    original_make_obs = torcs_env.TorcsEnv.make_observaton

    def patched_make_obs(self, raw_obs):
        """Add missing keys with defaults"""
        if 'lap' not in raw_obs:
            raw_obs['lap'] = 0
        if 'racePos' not in raw_obs:
            raw_obs['racePos'] = 1
        return original_make_obs(self, raw_obs)

    torcs_env.TorcsEnv.make_observaton = patched_make_obs


def observation_preprocessor(dict_obs):
    """Preprocess gym_torcs dict observation to flat array for RL."""
    return np.hstack((
        dict_obs['angle'],
        dict_obs['track'],           # 19 sensors
        dict_obs['trackPos'],
        dict_obs['speedX'],
        dict_obs['speedY'],
        dict_obs['speedZ'],
        dict_obs['wheelSpinVel'],    # 4 wheels
        dict_obs['rpm'],
        dict_obs['opponents'],       # 36 sensors
    )).astype(np.float32)


def reward_shaper(reward, info):
    """
    Shape the reward signal.
    
    Base reward from gym_torcs is negative lap time (lower = better).
    Add bonuses for staying on track, and penalties for crashing.
    """
    # Encourage staying centered on track
    track_penalty = abs(info.get('trackPos', 0.0)) * 0.1 if 'trackPos' in info else 0.0
    
    # Penalize spinning or damage
    damage = info.get('damage', 0.0) if 'damage' in info else 0.0
    
    shaped_reward = reward - track_penalty - damage * 0.01
    return shaped_reward


def make_env(env_id, rank=0, seed=None):
    """Create a single environment."""
    def _init():
        # Clear sys.argv before gym.make() since gym_torcs parses it
        saved_argv = sys.argv.copy()
        sys.argv = [sys.argv[0]]
        
        env = gym.make(
            env_id,
            vision=False,
            rendering=False,  # Try disabling rendering with -T flag
            obs_preprocess_fn=observation_preprocessor,
            obs_vars=[
                'angle', 'track', 'trackPos', 'speedX', 'speedY', 'speedZ',
                'wheelSpinVel', 'rpm', 'opponents'
            ],
            throttle=True,
            gear_change=True,
            rank=rank,
            hard_reset_interval=999999,  # Avoid restarting TORCS during training
        )
        
        # Restore sys.argv
        sys.argv = saved_argv
        if seed is not None:
            env.seed(seed + rank)
        return env
    
    return _init


def main(args):
    # Setup
    os.makedirs(args.log_dir, exist_ok=True)
    
    print(f"Training PPO on {args.env_id} for {args.total_timesteps} steps...")
    
    # Create vectorized environment
    env = DummyVecEnv([
        make_env(args.env_id, rank=1, seed=args.seed)
        for i in range(args.num_envs)
    ])
    
    # Create PPO agent
    model = PPO(
        'MlpPolicy',
        env,
        learning_rate=args.lr,
        n_steps=max(2, min(2048, args.total_timesteps)),  # Must be at least 2 for PPO
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.0,
        verbose=1,
        tensorboard_log=args.log_dir,
    )
    
    # Checkpointing callback
    checkpoint_callback = CheckpointCallback(
        save_freq=max(1, args.total_timesteps // args.num_checkpoints),
        save_path=args.log_dir,
        name_prefix='ppo_torcs',
    )
    
    # Train
    model.learn(
        total_timesteps=args.total_timesteps,
        callback=checkpoint_callback,
    )
    
    # Save final model
    final_path = os.path.join(args.log_dir, 'ppo_torcs_final')
    model.save(final_path)
    print(f"\nTraining complete! Model saved to {final_path}")
    
    env.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train PPO on TORCS')
    parser.add_argument('--env-id', default='Torcs-v0', help='Gym environment ID')
    parser.add_argument('--total-timesteps', type=int, default=100000, help='Total training steps')
    parser.add_argument('--num-envs', type=int, default=1, help='Number of parallel environments')
    parser.add_argument('--num-checkpoints', type=int, default=5, help='Number of checkpoints to save')
    parser.add_argument('--lr', type=float, default=3e-4, help='Learning rate')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--log-dir', default='./logs', help='Logging directory')
    
    args = parser.parse_args()
    main(args)
