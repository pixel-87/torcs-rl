import sys
import subprocess
import numpy as np
from contextlib import contextmanager

def patch_numpy():
    """Fix numpy compatibility with old gym/gym_torcs."""
    if not hasattr(np, 'bool8'):
        np.bool8 = np.bool_

@contextmanager
def patch_sys_argv():
    """
    Context manager to temporarily clear sys.argv.
    gym_torcs parses command line arguments on import, which interferes with argparse.
    """
    original_argv = sys.argv.copy()
    sys.argv = [sys.argv[0]]
    try:
        yield
    finally:
        sys.argv = original_argv

def patch_subprocess():
    """
    Patch subprocess.Popen to prevent gym-torcs from auto-launching TORCS.
    """
    original_popen = subprocess.Popen
    
    def no_launch_popen(args, **kwargs):
        # Check if args is a list and contains 'torcs'
        # The original check was: if isinstance(args, list) and args and 'torcs' in str(args[0]):
        # We'll make it slightly more robust but keep the spirit
        if isinstance(args, list) and args and len(args) > 0 and 'torcs' in str(args[0]):
            print("[SKIP] Not auto-launching TORCS (should be running manually)")
            # Return a dummy process that does nothing
            # Using sleep 999999 as in original code to keep the process "alive" if something waits on it?
            # Or maybe just a short sleep. Original code used 999999.
            return original_popen(['sleep', '999999'], **kwargs)
        return original_popen(args, **kwargs)

    subprocess.Popen = no_launch_popen

def patch_torcs_env_observation(torcs_env_module):
    """
    Patch gym-torcs observation handler to fix missing keys.
    """
    if not torcs_env_module:
        return

    # Note: The method name in gym_torcs is misspelled as 'make_observaton'
    if hasattr(torcs_env_module.TorcsEnv, 'make_observaton'):
        original_make_obs = torcs_env_module.TorcsEnv.make_observaton

        def patched_make_obs(self, raw_obs):
            """Add missing keys with defaults"""
            if 'lap' not in raw_obs:
                raw_obs['lap'] = 0
            if 'racePos' not in raw_obs:
                raw_obs['racePos'] = 1
            return original_make_obs(self, raw_obs)

        torcs_env_module.TorcsEnv.make_observaton = patched_make_obs

def patch_snakeoil(snakeoil_module):
    """
    Patch snakeoil3 to not parse command line args.
    """
    if snakeoil_module:
        snakeoil_module.Client.parse_the_command_line = lambda self: None

