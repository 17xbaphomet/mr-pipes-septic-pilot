"""espeak-ng / espeak TTS configuration for Mr. Pipes lip-sync pipeline.

Used by tools/build_pilot.py to generate WAVs that feed Rhubarb.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class VoiceProfile:
    """Per-character / role speaking style."""
    voice: str = "en-us"
    speed_wpm: int = 140
    pitch: int = 40
    amplitude: int = 100
    gap_ms: int = 8


PROFILES: dict[str, VoiceProfile] = {
    "mr_pipes": VoiceProfile(voice="en-us", speed_wpm=138, pitch=38, amplitude=100, gap_ms=10),
    "host": VoiceProfile(voice="en-us", speed_wpm=138, pitch=38, amplitude=100, gap_ms=10),
    "education": VoiceProfile(voice="en-us", speed_wpm=132, pitch=40, amplitude=100, gap_ms=12),
    "dad": VoiceProfile(voice="en-us", speed_wpm=145, pitch=35, amplitude=100, gap_ms=8),
    "mom": VoiceProfile(voice="en-us+f3", speed_wpm=145, pitch=55, amplitude=100, gap_ms=8),
    "teen": VoiceProfile(voice="en-us", speed_wpm=155, pitch=48, amplitude=100, gap_ms=6),
    "default": VoiceProfile(),
}


def espeak_bin() -> str | None:
    env = os.environ.get("ESPEAK_BIN")
    if env and Path(env).is_file():
        return env
    return shutil.which("espeak-ng") or shutil.which("espeak")


def espeak_available() -> bool:
    return espeak_bin() is not None


def profile_for(speaker: str | None = None, segment_type: str | None = None) -> VoiceProfile:
    if speaker and speaker in PROFILES:
        return PROFILES[speaker]
    if segment_type and segment_type in PROFILES:
        return PROFILES[segment_type]
    return PROFILES["default"]


def synthesize(
    text: str,
    wav_path: Path,
    *,
    speaker: str | None = None,
    segment_type: str | None = None,
    profile: VoiceProfile | None = None,
) -> bool:
    """Write mono WAV via espeak-ng. Returns True on success."""
    text = (text or "").strip()
    if not text:
        return False
    bin_path = espeak_bin()
    if not bin_path:
        return False
    p = profile or profile_for(speaker, segment_type)
    wav_path = Path(wav_path)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        bin_path,
        "-v", p.voice,
        "-s", str(p.speed_wpm),
        "-p", str(p.pitch),
        "-a", str(p.amplitude),
        "-g", str(p.gap_ms),
        "-w", str(wav_path),
        text,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return wav_path.is_file() and wav_path.stat().st_size > 44
    except (subprocess.CalledProcessError, OSError):
        return False
