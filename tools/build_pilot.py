#!/usr/bin/env python3
"""Build a finished Mr. Pipes pilot version: text + lip-sync + video.

Pipeline:
  1. Load content/timeline.json
  2. Extract timed dialogue → artifacts/pilot_script.txt (+ .md)
  3. Optional: espeak-ng TTS per segment → artifacts/audio/{seg_id}.wav
  4. Optional: Rhubarb lip-sync cues → artifacts/audio/{seg_id}.rhubarb.json
  5. Render each segment MP4 via MiniPlayer (subtitles + mouth)
  6. ffmpeg concat → artifacts/pilot_full.mp4

Examples:
  python tools/build_pilot.py --preview
  python tools/build_pilot.py --segment introduction
  python tools/build_pilot.py --all --fps 8
  python tools/build_pilot.py --script-only
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from domain.scene_schema import load_timeline, default_timeline_path, Segment, Timeline
from domain.lipsync import cues_from_rhubarb
from domain.rhubarb_config import rhubarb_available
from application.mini_player import MiniPlayer

AUDIO_DIR = ROOT / "artifacts" / "audio"
SEG_DIR = ROOT / "artifacts" / "segments"
OUT_DIR = ROOT / "artifacts"


def _segment_spoken_text(seg: Segment) -> str:
    parts: list[str] = []
    for line in seg.audio.dialogue:
        parts.append(line.text.strip())
    if seg.audio.vo:
        if seg.audio.vo.text:
            parts.append(seg.audio.vo.text.strip())
        for sec in seg.audio.vo.sections:
            t = (sec.get("text") or "").strip()
            if t:
                parts.append(t)
    return " ".join(p for p in parts if p)


def _segment_lines(seg: Segment) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    for d in seg.audio.dialogue:
        lines.append((d.speaker, d.text.strip()))
    if seg.audio.vo:
        if seg.audio.vo.text:
            lines.append((seg.audio.vo.speaker, seg.audio.vo.text.strip()))
        for sec in seg.audio.vo.sections:
            t = (sec.get("text") or "").strip()
            if t:
                lines.append((seg.audio.vo.speaker, t))
    return [(s, t) for s, t in lines if t]


def write_pilot_script(tl: Timeline, out_txt: Path, out_md: Path) -> None:
    lines_txt: list[str] = []
    lines_md: list[str] = [
        f"# {tl.title}", "",
        f"**Runtime:** {tl.duration_s:.0f}s ({tl.duration_s / 60:.1f} min)  ",
        f"**Segments:** {len(tl.segments)}  ", "", "---", "",
    ]
    lines_txt.append(tl.title)
    lines_txt.append("=" * len(tl.title))
    lines_txt.append(f"Runtime: {tl.duration_s:.0f}s | Segments: {len(tl.segments)}")
    lines_txt.append("")
    for seg in tl.segments:
        header = f"[{seg.start_s:06.1f}–{seg.end_s:06.1f}]  {seg.id}  ({seg.type.value})  {seg.title}"
        lines_txt.append(header)
        lines_txt.append("-" * min(80, len(header)))
        lines_md.append(f"## {seg.title}")
        lines_md.append(f"`{seg.start_s:.0f}s–{seg.end_s:.0f}s` · **{seg.type.value}** · set `{seg.set_id}`")
        lines_md.append("")
        for speaker, text in _segment_lines(seg):
            lines_txt.append(f"  {speaker}: {text}")
            lines_md.append(f"**{speaker.replace('_', ' ').title()}:** {text}")
            lines_md.append("")
        if not _segment_lines(seg):
            lines_txt.append("  (no dialogue)")
            lines_md.append("_no dialogue_")
            lines_md.append("")
        if seg.edu_topics:
            lines_txt.append(f"  edu: {', '.join(seg.edu_topics)}")
            lines_md.append(f"*Topics: {', '.join(seg.edu_topics)}*")
            lines_md.append("")
        lines_txt.append("")
        lines_md.append("---")
        lines_md.append("")
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    out_txt.write_text("\n".join(lines_txt) + "\n", encoding="utf-8")
    out_md.write_text("\n".join(lines_md) + "\n", encoding="utf-8")
    print(f"script → {out_txt}")
    print(f"script → {out_md}")


def tts_espeak(text: str, wav_path: Path, *, voice: str = "en-us", speed: int = 150) -> bool:
    if not text.strip():
        return False
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak:
        print("  warn: espeak-ng not found — skip TTS")
        return False
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [espeak, "-v", voice, "-s", str(speed), "-w", str(wav_path), text]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return wav_path.is_file() and wav_path.stat().st_size > 44
    except subprocess.CalledProcessError as e:
        print(f"  TTS fail: {e}")
        return False


def ensure_segment_audio(seg: Segment, *, force: bool = False) -> Path | None:
    wav = AUDIO_DIR / f"{seg.id}.wav"
    if wav.is_file() and not force:
        return wav
    text = _segment_spoken_text(seg)
    if not text:
        return None
    speed = 140 if seg.type.value == "host" else 135 if seg.type.value == "education" else 145
    print(f"  TTS {seg.id} ({len(text)} chars)…")
    ok = tts_espeak(text, wav, speed=speed)
    return wav if ok else None


def ensure_rhubarb_cues(seg: Segment, wav: Path | None, *, force: bool = False) -> Path | None:
    if wav is None or not wav.is_file() or not rhubarb_available():
        return None
    out_json = AUDIO_DIR / f"{seg.id}.rhubarb.json"
    if out_json.is_file() and not force:
        return out_json
    text = _segment_spoken_text(seg)
    if text:
        (AUDIO_DIR / f"{seg.id}.dialog.txt").write_text(text, encoding="utf-8")
    print(f"  Rhubarb {seg.id}…")
    try:
        cues_from_rhubarb(wav, transcript=text or None, work_dir=AUDIO_DIR)
        return out_json if out_json.is_file() else None
    except Exception as e:
        print(f"  Rhubarb fail {seg.id}: {e}")
        return None


def render_segment_mp4(player: MiniPlayer, seg: Segment, out_mp4: Path, *, wav: Path | None = None) -> Path:
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    if wav and wav.is_file() and rhubarb_available():
        try:
            text = _segment_spoken_text(seg)
            cues = cues_from_rhubarb(wav, transcript=text or None, work_dir=AUDIO_DIR)
            shifted = [
                type(c)(
                    timing=type(c.timing)(c.timing.start + seg.start_s, c.timing.end + seg.start_s),
                    value=c.value, intensity=c.intensity,
                )
                for c in cues
            ]
            lines = _segment_lines(seg)
            speaker = lines[0][0] if lines else "mr_pipes"
            if not hasattr(player, "_viseme_cache"):
                player._viseme_cache = {}
            player._viseme_cache[seg.id] = {speaker: shifted}
            print(f"  lip-sync: {len(shifted)} Rhubarb cues → {speaker}")
        except Exception as e:
            print(f"  lip-sync fallback text: {e}")
    player.write_mp4(seg, out_mp4)
    return out_mp4


def concat_mp4s(paths: list[Path], out: Path) -> None:
    if not paths:
        raise SystemExit("no segment videos to concat")
    out.parent.mkdir(parents=True, exist_ok=True)
    list_file = out.parent / "_concat_list.txt"
    lines = [f"file '{p.resolve().as_posix().replace(chr(39), chr(39)+chr(92)+chr(39)+chr(39))}'" for p in paths]
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", str(out)],
            check=True, capture_output=True,
        )
    print(f"full → {out}")


def select_segments(tl: Timeline, *, segment: str | None, preview: int | None) -> list[Segment]:
    if segment:
        seg = next((s for s in tl.segments if s.id == segment), None)
        if not seg:
            raise SystemExit(f"unknown segment: {segment}")
        return [seg]
    if preview is not None:
        return list(tl.segments[: max(1, preview)])
    return list(tl.segments)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build finished Mr. Pipes pilot (text + video)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--segment", type=str, default=None)
    ap.add_argument("--preview", type=int, nargs="?", const=2, default=None)
    ap.add_argument("--fps", type=float, default=8.0)
    ap.add_argument("--script-only", action="store_true")
    ap.add_argument("--skip-tts", action="store_true")
    ap.add_argument("--skip-rhubarb", action="store_true")
    ap.add_argument("--skip-video", action="store_true")
    ap.add_argument("--force-tts", action="store_true")
    ap.add_argument("--force-rhubarb", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT_DIR / "pilot_full.mp4")
    args = ap.parse_args(argv)

    tl = load_timeline(default_timeline_path())
    print(f"timeline: {tl.project}  {len(tl.segments)} segs  {tl.duration_s:.0f}s")
    write_pilot_script(tl, OUT_DIR / "pilot_script.txt", OUT_DIR / "pilot_script.md")
    if args.script_only:
        return 0

    if not args.all and not args.segment and args.preview is None:
        args.preview = 2
        print("default: --preview 2 (use --all for full pilot)")

    segs = select_segments(tl, segment=args.segment, preview=args.preview)
    print(f"build: {[s.id for s in segs]}")
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    SEG_DIR.mkdir(parents=True, exist_ok=True)

    wavs: list[Path | None] = []
    for seg in segs:
        wav = None
        if not args.skip_tts:
            wav = ensure_segment_audio(seg, force=args.force_tts)
        else:
            candidate = AUDIO_DIR / f"{seg.id}.wav"
            wav = candidate if candidate.is_file() else None
        wavs.append(wav)
        if not args.skip_rhubarb:
            ensure_rhubarb_cues(seg, wav, force=args.force_rhubarb)

    if args.skip_video:
        print("skip video")
        return 0

    player = MiniPlayer(fps=args.fps)
    mp4s: list[Path] = []
    for seg, wav in zip(segs, wavs):
        out_mp4 = SEG_DIR / f"{seg.id}.mp4"
        print(f"render {seg.id} ({seg.duration_s:.0f}s) → {out_mp4.name}")
        render_segment_mp4(player, seg, out_mp4, wav=wav)
        mp4s.append(out_mp4)

    out = args.out
    if len(mp4s) == 1:
        shutil.copy(mp4s[0], out)
        print(f"full → {out}")
    else:
        concat_mp4s(mp4s, out)

    manifest = {
        "project": tl.project,
        "segments": [s.id for s in segs],
        "fps": args.fps,
        "out": str(out),
        "script": str(OUT_DIR / "pilot_script.txt"),
        "rhubarb": rhubarb_available(),
    }
    man_path = OUT_DIR / "pilot_build.json"
    man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"manifest → {man_path}")
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
