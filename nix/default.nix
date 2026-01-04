# Nix-managed tooling for the project.
# Python packages are managed by uv, not nix.
{ lib, pkgs, python3Packages, ... }:
let
  # Custom TORCS 1.3.7 with SCR patch
  torcs-scr = pkgs.callPackage ./torcs.nix { };

  # Dev tooling - nix provides the infra, uv manages Python deps
  devTooling = {
    packages = [
      pkgs.python3
      pkgs.uv
      torcs-scr
      pkgs.xorg.xorgserver  # Provides Xvfb for headless rendering
      pkgs.xvfb-run         # Wrapper to run apps with virtual display
    ];

    env = {
      # Prevent uv from downloading its own Python; use the nix-provided one.
      UV_PYTHON_DOWNLOADS = "never";
    };
  };
in
python3Packages.buildPythonApplication {
  pname = "torcs-rl";
  version = "0.0.1";

  src = ./..;
  pyproject = true;

  build-system = [ python3Packages.setuptools python3Packages.wheel ];

  # Runtime deps managed by uv, not nix - leave empty
  dependencies = [ ];

  # Skip the runtime deps check since we use uv for Python packages
  dontCheckRuntimeDeps = true;
  
  nativeCheckInputs = [ python3Packages.pytestCheckHook ];

  passthru = { inherit devTooling; };

  meta = {
    description = "TORCS Reinforcement Learning";
    homepage = "https://github.com/";
    license = lib.licenses.mit;
    maintainers = with lib.maintainers; [ ];
    mainProgram = "torcs-rl";
  };
}
