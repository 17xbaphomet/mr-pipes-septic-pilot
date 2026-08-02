#!/usr/bin/env python3
"""
Mr. Pipes Septic Pilot - FULL PILOT PACKAGE GENERATOR
====================================================
Generates the complete pilot including all audio tracks
using Qwen3-TTS-12Hz-1.7B-VoiceDesign.

Usage:
    python generate_full_pilot_package.py

Requirements:
    pip install torch soundfile pydub qwen-tts
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO_SCRIPT = ROOT / "scripts" / "generate_full_audio_voice_design.py"
OUTPUT_AUDIO = ROOT / "audio_output_voice_design"

def check_assets():
    print("=== Checking core assets ===")
    required = [
        "assets/characters/mr_pipes.svg",
        "assets/characters/dad.svg",
        "assets/characters/mom.svg",
        "assets/characters/teen.svg",
        "assets/characters/mid_child.svg",
        "assets/characters/baby.svg",
        "assets/sets/house_exterior_day.svg",
        "assets/sets/kitchen.svg",
        "assets/sets/bathroom.svg",
        "assets/sets/workshop.svg",
        "assets/sets/garage_new.svg",
        "assets/sets/yard_drainfield.svg",
        "assets/diagrams/diagram_tank.svg",
        "assets/diagrams/diagram_drainfield.svg",
        "assets/diagrams/diagram_healthy_system.svg",
        "assets/props/toilet.svg",
        "assets/props/caustic_bottle.svg",
        "assets/props/clipboard.svg",
        "assets/graphics/title_card.svg",
        "assets/graphics/end_card.svg",
    ]
    missing = [r for r in required if not (ROOT / r).exists()]
    if missing:
        print("Missing assets:")
        for m in missing:
            print(f"  - {m}")
        return False
    print("All core assets present.")
    return True

def generate_audio():
    print("\n=== Generating full audio tracks with Qwen3-TTS-12Hz-1.7B-VoiceDesign ===")
    if not AUDIO_SCRIPT.exists():
        # Fallback to root version if present
        alt = ROOT / "generate_full_audio_voicedesign.py"
        if alt.exists():
            script = alt
        else:
            print(f"Audio script not found: {AUDIO_SCRIPT}")
            return False
    else:
        script = AUDIO_SCRIPT

    result = subprocess.run([sys.executable, str(script)], cwd=str(ROOT))
    return result.returncode == 0

def main():
    print("Mr. Pipes Septic Pilot - Full Package Generator")
    print("=" * 55)

    if not check_assets():
        print("\nPlease ensure all assets are present before generating.")
        return

    success = generate_audio()
    if success:
        print("\n=== Audio generation complete ===")
        print(f"Audio files are in: {OUTPUT_AUDIO}")
        print("\nNext steps:")
        print("1. Review the individual .wav segments")
        print("2. (Optional) Run lipsync: python tools/run_rhubarb.py")
        print("3. Assemble the final video with tools/build_pilot.py or your editor")
        print("4. Render")
    else:
        print("\nAudio generation failed. Check that the TTS model is installed and a GPU is available.")

if __name__ == "__main__":
    main()
