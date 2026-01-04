#!/usr/bin/env python3
"""
Run agent - assumes TORCS is already running manually
"""
import sys
import numpy as np
from typing import Optional

# Import patches
from src.torcs_patches import (
    patch_numpy,
    patch_sys_argv,
    patch_subprocess,
    patch_torcs_env_observation
)

# Apply patches
patch_numpy()
patch_subprocess()

# Import gym and gym_torcs with sys.argv patch
with patch_sys_argv():
    try:
        import gym
        import gym_torcs.torcs_env as torcs_env
    except ImportError:
        gym = None
        torcs_env = None

from src.agents.baseline import PurePursuitAgent

# Patch observation
if torcs_env:
    patch_torcs_env_observation(torcs_env)

def main():
    print("Connecting to TORCS (should already be running on port 3001)...")
    if gym is None or torcs_env is None:
        print("ERROR: gym or gym_torcs is not available. Please ensure both 'gym' and 'gym_torcs' are installed and importable.")
        sys.exit(1)
        
    try:
        env = gym.make('Torcs-v0', vision=False, rendering=True, throttle=True, gear_change=False, rank=1)
    except Exception as e:
        print(f"Failed to create environment: {e}")
        sys.exit(1)

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
