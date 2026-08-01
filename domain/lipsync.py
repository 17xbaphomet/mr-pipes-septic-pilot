"""Lip-sync for Mr. Pipes pilot.

Preston Blair visemes (Rhubarb-compatible: X, A-H),
text-driven cues, Rhubarb CLI adapter.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Sequence

try:
    from domain.rhubarb_config import rhubarb_bin as _default_rhubarb_bin
except Exception:
    def _default_rhubarb_bin() -> str:
        return "rhubarb"


class Viseme(str, Enum):
    X = "X"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"


@dataclass(frozen=True, slots=True)
class Timing:
    start: float
    end: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def contains(self, t: float) -> bool:
        return self.start <= t < self.end


@dataclass(frozen=True, slots=True)
class VisemeCue:
    timing: Timing
    value: Viseme
    intensity: float = 1.0


_LETTER_VISEME: dict[str, Viseme] = {
    "a": Viseme.A, "e": Viseme.D, "i": Viseme.D, "o": Viseme.C, "u": Viseme.F, "y": Viseme.D,
    "b": Viseme.B, "p": Viseme.B, "m": Viseme.B,
    "c": Viseme.C, "k": Viseme.C, "g": Viseme.C, "q": Viseme.C,
    "d": Viseme.A, "t": Viseme.A, "n": Viseme.A,
    "f": Viseme.G, "v": Viseme.G, "l": Viseme.H,
    "w": Viseme.F, "r": Viseme.F, "s": Viseme.D, "z": Viseme.D,
    "h": Viseme.C, "j": Viseme.C, "x": Viseme.C,
}


def sample_viseme_at(cues: Sequence[VisemeCue], t: float) -> tuple[Viseme, float]:
    for cue in cues:
        if cue.timing.contains(t):
            return cue.value, cue.intensity
    return Viseme.X, 0.0


def cues_from_text(
    text: str, *, start_s: float = 0.0, duration_s: float | None = None, wpm: float = 140.0,
) -> list[VisemeCue]:
    text = (text or "").strip()
    if not text:
        return [VisemeCue(Timing(start_s, start_s + 0.15), Viseme.X)]
    tokens: list[tuple[str, Viseme | None]] = []
    for ch in text.lower():
        if ch.isalpha():
            tokens.append((ch, _LETTER_VISEME.get(ch, Viseme.C)))
        elif ch in ".!?",:
            tokens.append((ch, Viseme.X))
        elif ch in ",;:":
            tokens.append((ch, Viseme.X))
        elif ch.isspace():
            tokens.append((" ", Viseme.X))
    if not tokens:
        return [VisemeCue(Timing(start_s, start_s + 0.15), Viseme.X)]
    if duration_s is None or duration_s <= 0:
        words = max(1, len(re.findall(r"[A-Za-z]+", text)))
        duration_s = max(0.4, words / max(wpm, 60.0) * 60.0)
    weights: list[float] = []
    for ch, vis in tokens:
        if ch in ".!?":
            weights.append(2.5)
        elif ch in ",;:":
            weights.append(1.5)
        elif ch == " ":
            weights.append(0.8)
        elif ch in "aeiou":
            weights.append(1.4)
        else:
            weights.append(1.0)
    total_w = sum(weights) or 1.0
    cues: list[VisemeCue] = []
    t = start_s
    for (ch, vis), w in zip(tokens, weights):
        if vis is None:
            continue
        dur = duration_s * (w / total_w)
        if cues and cues[-1].value == vis and abs(cues[-1].timing.end - t) < 1e-6:
            prev = cues[-1]
            cues[-1] = VisemeCue(Timing(prev.timing.start, t + dur), vis, prev.intensity)
        else:
            intensity = 0.35 if vis == Viseme.X else 1.0
            cues.append(VisemeCue(Timing(t, t + dur), vis, intensity))
        t += dur
    if cues:
        last = cues[-1]
        cues[-1] = VisemeCue(Timing(last.timing.start, start_s + duration_s), last.value, last.intensity)
    return cues


def cues_from_dialogue_lines(
    lines: Sequence[tuple[str, str]], *, segment_start_s: float, segment_duration_s: float,
) -> dict[str, list[VisemeCue]]:
    if not lines or segment_duration_s <= 0:
        return {}
    slot = segment_duration_s / len(lines)
    by_speaker: dict[str, list[VisemeCue]] = {}
    for i, (speaker, text) in enumerate(lines):
        start = segment_start_s + i * slot
        dur = max(0.3, slot * 0.92)
        by_speaker.setdefault(speaker, []).extend(cues_from_text(text, start_s=start, duration_s=dur))
    return by_speaker


def cues_from_rhubarb(
    audio_path: Path, transcript: str | None = None, *,
    rhubarb_bin: str | None = None, work_dir: Path | None = None,
) -> list[VisemeCue]:
    if rhubarb_bin is None:
        rhubarb_bin = _default_rhubarb_bin()
    audio_path = Path(audio_path).resolve()
    if not audio_path.is_file():
        raise FileNotFoundError(audio_path)
    out_dir = Path(work_dir) if work_dir else audio_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / f"{audio_path.stem}.rhubarb.json"
    cmd = [rhubarb_bin, "-f", "json", "-o", str(out_json)]
    if transcript:
        dialog = out_dir / f"{audio_path.stem}.dialog.txt"
        dialog.write_text(transcript, encoding="utf-8")
        cmd.extend(["--dialogFile", str(dialog)])
    cmd.append(str(audio_path))
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    data = json.loads(out_json.read_text(encoding="utf-8"))
    cues: list[VisemeCue] = []
    for cue in data.get("mouthCues", []):
        try:
            vis = Viseme(cue["value"])
        except ValueError:
            vis = Viseme.X
        cues.append(VisemeCue(Timing(float(cue["start"]), float(cue["end"])), vis, 1.0))
    return cues


def extract_visemes(
    *, text: str | None = None, audio_path: Path | None = None,
    start_s: float = 0.0, duration_s: float | None = None, prefer_rhubarb: bool = True,
) -> list[VisemeCue]:
    if audio_path and Path(audio_path).is_file() and prefer_rhubarb:
        try:
            cues = cues_from_rhubarb(Path(audio_path), transcript=text)
            if start_s:
                cues = [
                    VisemeCue(Timing(c.timing.start + start_s, c.timing.end + start_s), c.value, c.intensity)
                    for c in cues
                ]
            return cues
        except Exception:
            pass
    if text:
        return cues_from_text(text, start_s=start_s, duration_s=duration_s)
    return [VisemeCue(Timing(start_s, start_s + 0.1), Viseme.X)]


_MOUTH_SHAPES: dict[Viseme, tuple[float, float, float, float]] = {
    Viseme.X: (0.0, 38.0, 14.0, 4.0),
    Viseme.A: (0.0, 40.0, 16.0, 18.0),
    Viseme.B: (0.0, 38.0, 20.0, 6.0),
    Viseme.C: (0.0, 40.0, 15.0, 14.0),
    Viseme.D: (0.0, 38.0, 12.0, 8.0),
    Viseme.E: (0.0, 39.0, 13.0, 10.0),
    Viseme.F: (0.0, 38.0, 10.0, 10.0),
    Viseme.G: (0.0, 36.0, 16.0, 5.0),
    Viseme.H: (0.0, 40.0, 14.0, 9.0),
}


def mouth_ellipse(viseme: Viseme, intensity: float = 1.0) -> tuple[float, float, float, float]:
    dx, dy, rx, ry = _MOUTH_SHAPES.get(viseme, _MOUTH_SHAPES[Viseme.X])
    intensity = max(0.0, min(1.0, intensity))
    if viseme == Viseme.X:
        return dx, dy, rx, ry
    ry = ry * (0.35 + 0.65 * intensity)
    rx = rx * (0.85 + 0.15 * intensity)
    return dx, dy, rx, ry
