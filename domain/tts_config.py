"""espeak-ng TTS engine for Mr. Pipes pilot.

Per-character profiles, multi-speaker line synth, ffmpeg concat,
duration fit, text-hash cache.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class VoiceProfile:
    voice: str = "en-us"
    speed_wpm: int = 140
    pitch: int = 40
    amplitude: int = 100
    gap_ms: int = 8
    line_pause_ms: int = 280


PROFILES: dict[str, VoiceProfile] = {
    "mr_pipes": VoiceProfile(voice="en-us", speed_wpm=136, pitch=36, amplitude=105, gap_ms=10, line_pause_ms=320),
    "host": VoiceProfile(voice="en-us", speed_wpm=136, pitch=36, amplitude=105, gap_ms=10, line_pause_ms=320),
    "education": VoiceProfile(voice="en-us", speed_wpm=130, pitch=38, amplitude=100, gap_ms=12, line_pause_ms=350),
    "dad": VoiceProfile(voice="en-us", speed_wpm=142, pitch=32, amplitude=110, gap_ms=8, line_pause_ms=250),
    "mom": VoiceProfile(voice="en-us+f3", speed_wpm=140, pitch=55, amplitude=100, gap_ms=8, line_pause_ms=260),
    "teen": VoiceProfile(voice="en-us", speed_wpm=155, pitch=50, amplitude=100, gap_ms=6, line_pause_ms=220),
    "mid_child": VoiceProfile(voice="en-us", speed_wpm=150, pitch=58, amplitude=95, gap_ms=7, line_pause_ms=220),
    "baby": VoiceProfile(voice="en-us", speed_wpm=120, pitch=70, amplitude=80, gap_ms=15, line_pause_ms=200),
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


def _text_hash(text: str, profile: VoiceProfile) -> str:
    payload = text.strip() + "|" + json.dumps(asdict(profile), sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]


def wav_duration_s(path: Path) -> float:
    path = Path(path)
    if not path.is_file():
        return 0.0
    try:
        with wave.open(str(path), "rb") as w:
            return w.getnframes() / float(w.getframerate() or 1)
    except Exception:
        try:
            r = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                capture_output=True, text=True, check=True,
            )
            return float(r.stdout.strip())
        except Exception:
            return 0.0


def synthesize(
    text: str, wav_path: Path, *,
    speaker: str | None = None, segment_type: str | None = None,
    profile: VoiceProfile | None = None,
) -> bool:
    text = (text or "").strip()
    if not text:
        return False
    bin_path = espeak_bin()
    if not bin_path:
        return False
    p = profile or profile_for(speaker, segment_type)
    wav_path = Path(wav_path)
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [bin_path, "-v", p.voice, "-s", str(p.speed_wpm), "-p", str(p.pitch),
           "-a", str(p.amplitude), "-g", str(p.gap_ms), "-w", str(wav_path), text]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return wav_path.is_file() and wav_path.stat().st_size > 44
    except (subprocess.CalledProcessError, OSError):
        return False


def _write_silence_wav(path: Path, duration_s: float, *, rate: int = 22050) -> None:
    n = max(1, int(rate * duration_s))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * n)


def concat_wavs(parts: Sequence[Path], out: Path, *, gap_ms: int = 280) -> bool:
    parts = [Path(p) for p in parts if Path(p).is_file()]
    if not parts:
        return False
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if len(parts) == 1 and gap_ms <= 0:
        shutil.copy(parts[0], out)
        return True
    silence = out.parent / f"_{out.stem}_gap.wav"
    if gap_ms > 0:
        _write_silence_wav(silence, gap_ms / 1000.0)
    inputs: list[str] = []
    filter_parts: list[str] = []
    idx = 0
    for i, p in enumerate(parts):
        inputs.extend(["-i", str(p)])
        filter_parts.append(f"[{idx}:a]")
        idx += 1
        if gap_ms > 0 and i < len(parts) - 1:
            inputs.extend(["-i", str(silence)])
            filter_parts.append(f"[{idx}:a]")
            idx += 1
    filt = "".join(filter_parts) + f"concat=n={idx}:v=0:a=1[aout]"
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filt, "-map", "[aout]", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if silence.is_file():
        silence.unlink(missing_ok=True)
    return r.returncode == 0 and out.is_file()


def fit_duration(wav_path: Path, target_s: float, *, max_stretch: float = 1.15) -> bool:
    wav_path = Path(wav_path)
    if not wav_path.is_file() or target_s <= 0.05:
        return False
    dur = wav_duration_s(wav_path)
    if dur <= 0:
        return False
    tmp = wav_path.with_suffix(".fit.wav")
    if dur < target_s - 0.05:
        pad = target_s - dur
        cmd = ["ffmpeg", "-y", "-i", str(wav_path), "-af", f"apad=pad_dur={pad:.3f}",
               "-t", f"{target_s:.3f}", str(tmp)]
    elif dur > target_s * max_stretch:
        cmd = ["ffmpeg", "-y", "-i", str(wav_path), "-t", f"{target_s:.3f}", str(tmp)]
    elif dur > target_s + 0.05:
        ratio = min(max_stretch, dur / target_s)
        tempo = max(0.5, min(2.0, 1.0 / ratio))
        cmd = ["ffmpeg", "-y", "-i", str(wav_path), "-af", f"atempo={tempo:.4f}",
               "-t", f"{target_s:.3f}", str(tmp)]
    else:
        return True
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0 and tmp.is_file():
        tmp.replace(wav_path)
        return True
    tmp.unlink(missing_ok=True)
    return False


def synthesize_segment_lines(
    lines: Sequence[tuple[str, str]], out_wav: Path, *,
    segment_type: str | None = None, target_duration_s: float | None = None,
    force: bool = False, work_dir: Path | None = None,
) -> Path | None:
    lines = [(s, t.strip()) for s, t in lines if (t or "").strip()]
    if not lines or not espeak_available():
        return None
    out_wav = Path(out_wav)
    work = Path(work_dir) if work_dir else out_wav.parent
    work.mkdir(parents=True, exist_ok=True)
    meta_path = out_wav.with_suffix(".meta.json")
    blob = []
    for sp, tx in lines:
        p = profile_for(sp, segment_type)
        blob.append({"speaker": sp, "text": tx, "hash": _text_hash(tx, p)})
    cache_key = hashlib.sha1(json.dumps(blob, sort_keys=True).encode()).hexdigest()[:16]
    if out_wav.is_file() and meta_path.is_file() and not force:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("cache_key") == cache_key:
                return out_wav
        except Exception:
            pass
    part_paths: list[Path] = []
    for i, (sp, tx) in enumerate(lines):
        part = work / f"{out_wav.stem}_line{i:02d}_{sp}.wav"
        if synthesize(tx, part, speaker=sp, segment_type=segment_type):
            part_paths.append(part)
    if not part_paths:
        return None
    gap = profile_for(lines[0][0], segment_type).line_pause_ms
    if not concat_wavs(part_paths, out_wav, gap_ms=gap):
        shutil.copy(part_paths[0], out_wav)
    for p in part_paths:
        p.unlink(missing_ok=True)
    if target_duration_s and target_duration_s > 0:
        fit_duration(out_wav, target_duration_s)
    meta = {
        "cache_key": cache_key, "lines": blob,
        "duration_s": wav_duration_s(out_wav),
        "target_duration_s": target_duration_s, "engine": espeak_bin(),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return out_wav if out_wav.is_file() else None


def synthesize_segment_from_schema(seg, out_wav: Path, *, force: bool = False) -> Path | None:
    lines: list[tuple[str, str]] = []
    for d in getattr(seg.audio, "dialogue", []) or []:
        if d.text and d.text.strip():
            lines.append((d.speaker, d.text.strip()))
    vo = getattr(seg.audio, "vo", None)
    if vo:
        if vo.text and vo.text.strip():
            lines.append((vo.speaker, vo.text.strip()))
        for sec in getattr(vo, "sections", []) or []:
            t = (sec.get("text") if isinstance(sec, dict) else None) or ""
            if t.strip():
                lines.append((vo.speaker, t.strip()))
    if not lines:
        return None
    return synthesize_segment_lines(
        lines, out_wav,
        segment_type=getattr(getattr(seg, "type", None), "value", None),
        target_duration_s=getattr(seg, "duration_s", None),
        force=force, work_dir=out_wav.parent,
    )
