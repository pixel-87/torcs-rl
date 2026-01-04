#!/usr/bin/env python3
"""
Generate a valid TORCS race config that avoids category mismatches.

The problem: gym-torcs uses a hardcoded default.xml that specifies
car1-trb1 (category: trb1) with g-track-1 (category: road), which TORCS rejects.

Solution: Generate a minimal valid config using components we know work together.
"""

import os
import sys

def generate_working_config():
    """Generate a race config that actually works with TORCS."""
    
    config = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE params SYSTEM "params.dtd">

<params name="Practice_RL">
  <section name="Header">
    <attstr name="name" val="Practice RL"/>
    <attstr name="description" val="Practice mode for RL training"/>
    <attnum name="priority" val="100"/>
  </section>

  <section name="Tracks">
    <attnum name="maximum number" val="1"/>
    <section name="1">
      <attstr name="name" val="forza"/>
      <attstr name="category" val="road"/>
    </section>
  </section>

  <section name="Races">
    <section name="1">
      <attstr name="name" val="Practice_RL"/>
    </section>
  </section>

  <section name="Practice_RL">
    <attnum name="laps" val="10"/>
    <attstr name="type" val="practice"/>
    <attstr name="starting order" val="drivers list"/>
    <attstr name="restart" val="yes"/>
    <attstr name="display mode" val="normal"/>
    <attstr name="display results" val="yes"/>
    <attnum name="distance" unit="km" val="0"/>
    <section name="Starting Grid">
      <attnum name="rows" val="1"/>
      <attnum name="distance to start" val="100"/>
      <attnum name="distance between columns" val="20"/>
      <attnum name="offset within a column" val="10"/>
      <attnum name="initial speed" unit="km/h" val="0"/>
      <attnum name="initial height" unit="m" val="0.2"/>
    </section>
  </section>

  <section name="Drivers">
    <attnum name="maximum number" val="2"/>
    <attstr name="focused module" val="scr_server"/>
    <attnum name="focused idx" val="1"/>
    <section name="1">
      <attnum name="idx" val="0"/>
      <attstr name="module" val="scr_server"/>
    </section>
    <section name="2">
      <attnum name="idx" val="0"/>
      <attstr name="module" val="inferno"/>
    </section>
  </section>

  <section name="Configuration">
    <attnum name="current configuration" val="2"/>
    <section name="1">
      <attstr name="type" val="track select"/>
    </section>
    <section name="2">
      <attstr name="type" val="drivers select"/>
    </section>
  </section>
</params>
'''
    
    return config

if __name__ == "__main__":
    config = generate_working_config()
    
    # Save to both standard gym-torcs location and our custom path
    output_paths = [
        os.path.expanduser("~/.venv/lib/python3.13/site-packages/gym_torcs/raceconfigs/default.xml"),
        "/tmp/torcs_rl.xml"
    ]
    
    for path in output_paths:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w') as f:
                f.write(config)
            print(f"[+] Wrote working race config to: {path}")
        except Exception as e:
            print(f"[-] Failed to write {path}: {e}")
    
    print("\n[*] Configuration generated. Key points:")
    print("    - Track: forza (road category)")
    print("    - Drivers: scr_server (for your agent) + inferno (opponent)")
    print("    - This avoids the car category mismatch issue")
