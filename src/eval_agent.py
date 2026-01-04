#!/usr/bin/env python3
"""
Run agent - assumes TORCS is already running manually
"""
import sys
import subprocess
import numpy as np

# Fix numpy compatibility with old gym
if not hasattr(np, 'bool8'):
    np.bool8 = np.bool_

# Save original sys.argv before gym_torcs reads it
original_argv = sys.argv.copy()
sys.argv = [sys.argv[0]]

try:
    import gym
    import gym_torcs
    import gym_torcs.torcs_env as torcs_env
except ImportError:
    gym = None
    gym_torcs = None
    torcs_env = None

# Restore sys.argv
sys.argv = original_argv

from src.agents.baseline import PurePursuitAgent

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

def main():
    print("Connecting to TORCS (should already be running on port 3001)...")
    if gym is None:
        print("ERROR: gym or gym_torcs is not available. Please ensure both 'gym' and 'gym_torcs' are installed and importable.")
        sys.exit(1)
    env = gym.make('Torcs-v0', vision=False, rendering=True, throttle=True, gear_change=False, rank=1)

    agent = PurePursuitAgent()
    print("Running 1 episode...\n")

    obs = env.reset()
    done = False
    reward_sum = 0.0
    steps = 0

    while not done and steps < 1000:
        action = agent.predict(obs)
        obs, reward, done, info = env.step(action)
        reward_sum += reward
        steps += 1
        
        if steps % 100 == 0:
            print(f"Step {steps}, reward: {reward_sum:.2f}")

    print(f"\n✓ SUCCESS!")
    print(f"Total reward: {reward_sum:.2f}, Steps: {steps}")
    env.close()

if __name__ == "__main__":
    main()
