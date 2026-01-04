# TORCS Reinforcement Learning

Training RL agents on the TORCS racing simulator using gym-torcs and stable-baselines3.

## Quick Start

```bash
nix develop # Optional! Install deps manually otherwise
uv sync # Python deps
uv run python eval_agent.py --baseline --num-episodes 2
```

## Features

- **Pure Pursuit Baseline**: Rule-based steering controller
- **PPO Training**: Stable-Baselines3 integration
- **Gym-Standard API**: Compatible with any RL algorithm
- **Reproducible**: Nix + UV for exact dependency control

## Files

- `gym_torcs/`: Vendored and patched TORCS environment wrapper
- `agents/baseline.py`: Pure pursuit and random agents
- `train_ppo.py`: PPO training script
- `eval_agent.py`: Evaluation script
- `SETUP.md`: Full documentation

## Resources

- [GymTorcs](https://github.com/dosssman/GymTorcs)
- [Stable-Baselines3](https://stable-baselines3.readthedocs.io/)
- [Pure Pursuit Algorithm](http://www.wayneparrott.com/coding-a-pure-pursuit-steering-controller-for-a-torcs-racing-bot/)
