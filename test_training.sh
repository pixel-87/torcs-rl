#!/usr/bin/env bash
# Test launcher for TORCS PPO training

set -e

echo "TORCS PPO Training Test"
echo "======================="
echo

# Check if in nix shell
if [ -z "$(which torcs 2>/dev/null)" ]; then
    echo "ERROR: Not in nix develop shell"
    echo "Run: nix develop"
    exit 1
fi

# Start TORCS server in background
echo "Starting TORCS server..."
torcs -nofuel -nolaptime -a 1.0 \
  -raceconfig ~/.venv/lib/python3.13/site-packages/gym_torcs/raceconfigs/default.xml \
  -p 2999 > torcs_server.log 2>&1 &

TORCS_PID=$!
echo "TORCS PID: $TORCS_PID"

# Wait for TORCS to be ready
echo "Waiting for TORCS to start..."
sleep 3

# Run the training script (short run)
echo "Starting PPO training (smoke test)..."
PYTHONUNBUFFERED=1 uv run python train_ppo.py --total-timesteps 100 --num-envs 1 || echo "Training failed with exit code $?"

# Cleanup
echo
echo "Stopping TORCS..."
kill $TORCS_PID 2>/dev/null || true

echo "Done!"
