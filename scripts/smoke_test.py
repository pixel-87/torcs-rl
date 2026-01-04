import sys
print(f"Python {sys.version}")

import gym
print(f"gym version: {gym.__version__}")

import stable_baselines3
print(f"stable_baselines3 version: {stable_baselines3.__version__}")

from src.agents.baseline import PurePursuitAgent
print("✓ Agent imports OK")

# These should now be safe to import without triggering execution
from src.train_ppo import *
print("✓ Training imports OK")

from src.eval_agent import *
print("✓ Eval imports OK")

print("✓ All smoke tests passed!")
