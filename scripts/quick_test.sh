#!/usr/bin/env bash
# Simple launcher for TORCS RL experiments

set -e

echo "TORCS RL Launcher"
echo "================="
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
  -p 2999 &

TORCS_PID=$!
echo "TORCS PID: $TORCS_PID"

# Wait for TORCS to be ready
echo "Waiting for TORCS to start..."
sleep 3

# Run the agent
echo "Starting agent..."
PYTHONUNBUFFERED=1 uv run python src/eval_agent.py

# Cleanup
echo
echo "Stopping TORCS..."
kill $TORCS_PID 2>/dev/null || true

echo "Done!"
