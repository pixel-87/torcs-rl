# TORCS RL Setup with UV and Nix

## Architecture

This project uses a **two-layer dependency management** strategy:

- **Nix** (`flake.nix`, `nix/default.nix`, `nix/shell.nix`): Manages infrastructure
  - Python 3.x runtime
  - `uv` package manager
  - TORCS 1.3.7 with SCR patch (compiled from source)
  - Build dependencies (X11, OpenGL, etc.)

- **UV** (`pyproject.toml`, `uv.lock`): Manages Python packages
  - RL libraries (gymnasium, stable-baselines3, etc.)
  - Testing, linting, formatting tools

## For Nix Users

```bash
nix develop        # Enter dev shell with TORCS + Python + uv
uv sync            # Install Python dependencies into .venv/
uv run python eval_agent.py --baseline --num-episodes 2  # Test setup
```

## For Non-Nix Users

Install dependencies manually:
```bash
# Install UV: https://docs.astral.sh/uv/getting-started/installation/
# Install system deps (Ubuntu 20.04+):
sudo apt-get install libglib2.0-dev libgl1-mesa-dev libglu1-mesa-dev freeglut3-dev libplib-dev libopenal-dev libalut-dev libxi-dev libxmu-dev libxrender-dev libxrandr-dev libpng-dev libvorbis-dev

# Then:
uv venv            # Create local virtualenv
uv sync            # Install Python dependencies
# Build TORCS 1.3.7 manually per https://github.com/fmirus/torcs-1.3.7
```

## Running Experiments

1. Start TORCS server:
   ```bash
   torcs -r race_config.xml
   ```

2. In another terminal, run your RL agent:
   ```bash
   uv run python agents/my_agent.py
   ```

## File Structure

```
├── flake.nix                 # Nix flake entry point
├── nix/
│   ├── default.nix          # Package definition + dev tooling
│   ├── shell.nix            # Dev shell configuration
│   └── torcs.nix            # Custom TORCS derivation (1.3.7 + SCR)
├── pyproject.toml           # Python project config + dependencies
├── uv.lock                  # Locked Python dependencies (commit this)
└── agents/                  # Your RL agent code
```

## SCR (Simulated Car Racing) Protocol

TORCS with SCR provides a UDP interface for external agents:
- **20ms game tick**: Server sends sensor data
- **10ms timeout**: Client must respond with actions
- **Ports**: 3001-3010 (one per agent)

See `torcs-udp.md` for full sensor/actuator documentation.
