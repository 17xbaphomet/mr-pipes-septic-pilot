#!/usr/bin/env python3
"""
Mr. Pipes Septic Pilot - MASTER GENERATION SCRIPT
=================================================
Generates the complete pilot video assets including:
1. Full TTS audio tracks (Qwen3-TTS-12Hz-1.7B-VoiceDesign)
2. Optional lipsync preparation (Rhubarb)
3. Scene assembly placeholders

Usage:
    python scripts/generate_full_pilot.py

Requirements:
    - torch, qwen_tts, soundfile, pydub
    - (optional) rhubarb for lipsync
"""

import os
import sys
import subprocess
from pathlib import Path

# Paths
ROOT = Path(__file__).resolve().parent.parent
AUDIO_SCRIPT = ROOT / "scripts" / "generate_full_audio_voice_design.py"
OUTPUT_AUDIO = ROOT / "audio_output_voice_design"
ASSETS = ROOT / "assets"
CONTENT = ROOT / "content"

def check_assets():
    print("=== Checking assets ===")
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
    missing = []
    for r in required:
        if not (ROOT / r).exists():
            missing.append(r)
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
        print(f"Audio script not found: {AUDIO_SCRIPT}")
        return False
    result = subprocess.run([sys.executable, str(AUDIO_SCRIPT)], cwd=str(ROOT))
    return result.returncode == 0

def main():
    print("Mr. Pipes Septic Pilot - Full Generation Pipeline")
    print("=" * 55)

    if not check_assets():
        print("\nPlease generate missing assets first.")
        return

    success = generate_audio()
    if success:
        print("\n=== Audio generation complete ===")
        print(f"Audio files are in: {OUTPUT_AUDIO}")
        print("\nNext steps:")
        print("1. Review individual .wav segments")
        print("2. Run Rhubarb lipsync if needed: python tools/run_rhubarb.py")
        print("3. Assemble scenes with your preferred editor / tools/build_pilot.py")
        print("4. Final render")
    else:
        print("\nAudio generation failed. Check model installation and GPU availability.")

if __name__ == "__main__":
    main()
