import sys
print(f"Python {sys.version}")

import gym
print(f"gym version: {gym.__version__}")

import stable_baselines3
print(f"stable_baselines3 version: {stable_baselines3.__version__}")

# Mock gym_torcs to prevent it from trying to connect to TORCS or failing due to gym version mismatch
from unittest.mock import MagicMock
sys.modules["gym_torcs"] = MagicMock()
sys.modules["gym_torcs.snakeoil3_gym"] = MagicMock()
print("✓ Mocked gym_torcs for smoke test")

from src.agents.baseline import PurePursuitAgent
print("✓ Agent imports OK")

# These should now be safe to import without triggering execution
from src.train_ppo import *
print("✓ Training imports OK")

from src.eval_agent import *
print("✓ Eval imports OK")

print("✓ All smoke tests passed!")
