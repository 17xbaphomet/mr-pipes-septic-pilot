"""Mini ScenePlayer — play one timeline segment with SVG sets + characters.

Usage:
  python -m application.mini_player
  python -m application.mini_player --segment introduction --out /tmp/intro.mp4
  python -m application.mini_player --list
"""
from __future__ import annotations

import argparse
import io
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from domain.scene_schema import load_timeline, default_timeline_path, Segment
from domain.lipsync import (
    Viseme, sample_viseme_at, cues_from_dialogue_lines, mouth_ellipse,
)


def _find_font(size: int):
    for name in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans-Bold.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def svg_to_pil(path: Path, size: tuple[int, int] | None = None) -> Image.Image:
    path = Path(path)
    if not path.is_file():
        img = Image.new("RGBA", size or (960, 540), (40, 40, 50, 255))
        d = ImageDraw.Draw(img)
        d.text((20, 20), f"missing: {path.name}", fill=(255, 200, 200, 255), font=_find_font(18))
        return img
    try:
        import cairosvg
        kw = {}
        if size:
            kw["output_width"], kw["output_height"] = size
        data = cairosvg.svg2png(url=str(path), **kw)
        return Image.open(io.BytesIO(data)).convert("RGBA")
    except Exception:
        pass
    img = Image.new("RGBA", size or (960, 540), (60, 70, 80, 255))
    d = ImageDraw.Draw(img)
    d.text((24, 24), path.name, fill=(220, 220, 220, 255), font=_find_font(20))
    return img


def load_asset(rel: str, size: tuple[int, int] | None = None) -> Image.Image:
    return svg_to_pil(ROOT / rel, size=size)


def wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_subtitles(canvas: Image.Image, text: str, speaker: str | None = None) -> Image.Image:
    if not text:
        return canvas
    out = canvas.copy()
    draw = ImageDraw.Draw(out)
    font = _find_font(20)
    small = _find_font(14)
    max_w = out.width - 80
    lines = wrap_text(text, font, max_w, draw)
    line_h = 28
    box_h = 24 + line_h * len(lines) + (18 if speaker else 0)
    y0 = out.height - box_h - 24
    overlay = Image.new("RGBA", out.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([20, y0, out.width - 20, out.height - 16], fill=(0, 0, 0, 170))
    out = Image.alpha_composite(out.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(out)
    y = y0 + 10
    if speaker:
        draw.text((40, y), speaker.replace("_", " ").title(), fill=(255, 213, 79, 255), font=small)
        y += 18
    for line in lines:
        draw.text((40, y), line, fill=(255, 255, 255, 255), font=font)
        y += line_h
    return out


def draw_mouth_on_character(
    char_img: Image.Image, viseme: Viseme, intensity: float = 1.0,
    *, head_cx_ratio: float = 0.50, head_cy_ratio: float = 0.22,
) -> Image.Image:
    out = char_img.copy().convert("RGBA")
    draw = ImageDraw.Draw(out)
    w, h = out.size
    hx = int(w * head_cx_ratio)
    hy = int(h * head_cy_ratio)
    scale = h / 480.0
    dx, dy, rx, ry = mouth_ellipse(viseme, intensity)
    cx = hx + int(dx * scale)
    cy = hy + int(dy * scale)
    rx = max(2, int(rx * scale))
    ry = max(1, int(ry * scale))
    pad = max(rx + 4, 12)
    draw.ellipse([cx - pad, cy - pad // 2, cx + pad, cy + pad], fill=(255, 224, 178, 255))
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(93, 64, 55, 255))
    if ry >= 4 and viseme != Viseme.X:
        ix, iy = max(1, rx - 3), max(1, ry - 3)
        draw.ellipse([cx - ix, cy - iy, cx + ix, cy + iy], fill=(40, 20, 20, 255))
        if viseme == Viseme.B:
            draw.rectangle([cx - ix + 1, cy - iy, cx + ix - 1, cy - iy + max(2, iy // 2)], fill=(255, 250, 240, 255))
    return out


def draw_timecode(canvas: Image.Image, t: float, seg_id: str) -> Image.Image:
    out = canvas.copy()
    draw = ImageDraw.Draw(out)
    font = _find_font(14)
    draw.rectangle([8, 8, 220, 32], fill=(0, 0, 0, 160))
    draw.text((14, 12), f"{t:06.1f}s  ·  {seg_id}", fill=(200, 255, 200, 255), font=font)
    return out


class MiniPlayer:
    def __init__(self, timeline_path: Path | None = None, width: int = 960, height: int = 540, fps: float = 12.0):
        self.tl = load_timeline(timeline_path or default_timeline_path())
        self.width = width
        self.height = height
        self.fps = fps
        self.assets_root = ROOT / "assets"
        self._cache: dict[str, Image.Image] = {}
        self._viseme_cache: dict = {}

    def _set_path(self, set_id: str) -> Path:
        candidates = [
            self.assets_root / "sets" / f"{set_id}.svg",
            self.assets_root / "diagrams" / f"{set_id}.svg",
            self.assets_root / "graphics" / f"{set_id}.svg",
        ]
        for p in candidates:
            if p.is_file():
                return p
        return candidates[0]

    def _char_path(self, char_id: str) -> Path:
        return self.assets_root / "characters" / f"{char_id}.svg"

    def _visemes_for_segment(self, seg: Segment) -> dict:
        if seg.id in self._viseme_cache:
            return self._viseme_cache[seg.id]
        lines = [(d.speaker, d.text) for d in seg.audio.dialogue]
        if not lines and seg.audio.vo and seg.audio.vo.text:
            lines = [(seg.audio.vo.speaker, seg.audio.vo.text)]
        if not lines and seg.audio.vo and seg.audio.vo.sections:
            lines = [(seg.audio.vo.speaker, sec.get("text", "")) for sec in seg.audio.vo.sections if sec.get("text")]
        by_speaker = cues_from_dialogue_lines(lines, segment_start_s=seg.start_s, segment_duration_s=seg.duration_s)
        self._viseme_cache[seg.id] = by_speaker
        return by_speaker

    def get_set(self, set_id: str) -> Image.Image:
        key = f"set:{set_id}"
        if key not in self._cache:
            self._cache[key] = load_asset(str(self._set_path(set_id).relative_to(ROOT)), size=(self.width, self.height))
        return self._cache[key].copy()

    def get_character(self, char_id: str, height: int = 380) -> Image.Image:
        key = f"char:{char_id}:{height}"
        if key not in self._cache:
            img = svg_to_pil(self._char_path(char_id))
            if img.height != height:
                ratio = height / max(1, img.height)
                img = img.resize((max(1, int(img.width * ratio)), height), Image.Resampling.LANCZOS)
            self._cache[key] = img
        return self._cache[key].copy()

    def dialogue_at(self, seg: Segment, local_t: float) -> tuple[str | None, str]:
        lines = list(seg.audio.dialogue)
        if not lines and seg.audio.vo and seg.audio.vo.text:
            return seg.audio.vo.speaker, seg.audio.vo.text
        if not lines:
            return None, ""
        slot = seg.duration_s / len(lines)
        idx = min(len(lines) - 1, int(local_t / max(slot, 0.01)))
        line = lines[idx]
        return line.speaker, line.text

    def render_frame(self, seg: Segment, t_global: float) -> Image.Image:
        local_t = t_global - seg.start_s
        canvas = self.get_set(seg.set_id)
        cues_map = self._visemes_for_segment(seg)
        if seg.type.value in ("host", "story", "education"):
            chars = []
            if "mr_pipes" in seg.assets or seg.type.value in ("host", "education"):
                chars.append(("mr_pipes", 0.42))
            if "dad" in seg.assets and seg.id in ("scene_1_welcome", "scene_5_shop"):
                chars.append(("dad", 0.62))
            if not chars and seg.assets:
                for a in seg.assets:
                    if (self.assets_root / "characters" / f"{a}.svg").is_file():
                        chars.append((a, 0.45))
                        break
            for cid, x_frac in chars:
                ch = self.get_character(cid, height=int(self.height * 0.72))
                vis, intensity = Viseme.X, 0.0
                if cid in cues_map:
                    vis, intensity = sample_viseme_at(cues_map[cid], t_global)
                ch = draw_mouth_on_character(ch, vis, intensity)
                x = int(self.width * x_frac - ch.width / 2)
                y = self.height - ch.height - int(self.height * 0.04)
                if canvas.mode != "RGBA":
                    canvas = canvas.convert("RGBA")
                canvas.alpha_composite(ch, (x, y))
        speaker, text = self.dialogue_at(seg, local_t)
        if text:
            canvas = draw_subtitles(canvas, text, speaker)
        canvas = draw_timecode(canvas, t_global, seg.id)
        return canvas.convert("RGB")

    def frames_for_segment(self, seg: Segment):
        dt = 1.0 / max(self.fps, 1.0)
        t = seg.start_s
        while t < seg.end_s - 1e-6:
            yield self.render_frame(seg, t)
            t += dt

    def write_mp4(self, seg: Segment, out_path: Path) -> None:
        import subprocess
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["ffmpeg", "-y", "-f", "image2pipe", "-framerate", str(self.fps), "-i", "-",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", str(out_path)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        assert proc.stdin is not None
        n = 0
        try:
            for frame in self.frames_for_segment(seg):
                buf = io.BytesIO()
                frame.save(buf, format="JPEG", quality=85)
                proc.stdin.write(buf.getvalue())
                n += 1
            proc.stdin.close()
            err = proc.stderr.read() if proc.stderr else b""
            proc.wait(timeout=120)
        except Exception:
            try: proc.kill()
            except Exception: pass
            raise
        if proc.returncode not in (0, None):
            raise RuntimeError((err or b"").decode("utf-8", errors="replace")[-800:])
        print(f"wrote {out_path} ({n} frames, {n / self.fps:.1f}s)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mr. Pipes mini scene player")
    ap.add_argument("--segment", default="introduction")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fps", type=float, default=12.0)
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--still", action="store_true")
    args = ap.parse_args(argv)
    player = MiniPlayer(fps=args.fps)
    if args.list:
        for s in player.tl.segments:
            print(f"{s.id:32} {s.type.value:12} {s.start_s:6.1f}–{s.end_s:5.1f}s  {s.title}")
        return 0
    seg = next((s for s in player.tl.segments if s.id == args.segment), None)
    if seg is None:
        print(f"unknown segment: {args.segment}", file=sys.stderr)
        return 1
    print(f"segment: {seg.id}  {seg.start_s:.0f}–{seg.end_s:.0f}s  set={seg.set_id}")
    if args.still or not args.out:
        mid = (seg.start_s + seg.end_s) / 2
        frame = player.render_frame(seg, mid)
        out = ROOT / "artifacts" / f"still_{seg.id}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        frame.save(out)
        print(f"still → {out}")
        return 0
    if args.out:
        player.write_mp4(seg, Path(args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
