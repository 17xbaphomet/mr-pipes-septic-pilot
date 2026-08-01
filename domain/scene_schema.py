"""Scene / timeline schema for Mr. Pipes septic pilot.

Load content/timeline.json → typed segments for a ScenePlayer.
Same engine family as vector-toon-pipeline; different driver (timeline, not continuous walk).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class SegmentType(str, Enum):
    STORY = "story"
    HOST = "host"
    EDUCATION = "education"


class TransitionType(str, Enum):
    CUT = "cut"
    CUT_TO_BLACK = "cut_to_black"
    FADE_TO_BLACK = "fade_to_black"
    SOFT_WIPE = "soft_wipe"
    FREEZE_SOFT_WIPE = "freeze_soft_wipe"
    QUICK_CUTAWAY = "quick_cutaway"


@dataclass(frozen=True, slots=True)
class Character:
    id: str
    role: str
    display_name: str


@dataclass(frozen=True, slots=True)
class SetRef:
    id: str
    kind: str


@dataclass(frozen=True, slots=True)
class DialogueLine:
    speaker: str
    text: str
    to_camera: bool = False
    tone: str | None = None
    action: str | None = None
    from_location: str | None = None


@dataclass(frozen=True, slots=True)
class VoiceOver:
    speaker: str
    text: str | None = None
    style: str | None = None
    sections: tuple[dict[str, Any], ...] = ()


@dataclass(frozen=True, slots=True)
class SfxCue:
    at_s: float
    id: str


@dataclass(frozen=True, slots=True)
class AnimationCue:
    at_s: float
    action: str


@dataclass(frozen=True, slots=True)
class ChecklistItem:
    at_s: float
    item: str


@dataclass(frozen=True, slots=True)
class Overlay:
    at_s: float
    kind: str
    asset: str
    fields: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Transition:
    type: TransitionType
    duration_s: float = 0.5
    to: str | None = None


@dataclass(frozen=True, slots=True)
class SegmentAudio:
    ambience: tuple[str, ...] = ()
    dialogue: tuple[DialogueLine, ...] = ()
    vo: VoiceOver | None = None
    sfx: tuple[SfxCue, ...] = ()


@dataclass(frozen=True, slots=True)
class Segment:
    id: str
    type: SegmentType
    start_s: float
    end_s: float
    title: str
    set_id: str
    imagery: tuple[str, ...] = ()
    audio: SegmentAudio = field(default_factory=SegmentAudio)
    assets: tuple[str, ...] = ()
    camera: dict[str, Any] = field(default_factory=dict)
    edu_topics: tuple[str, ...] = ()
    animation_cues: tuple[AnimationCue, ...] = ()
    checklist: tuple[ChecklistItem, ...] = ()
    overlays: tuple[Overlay, ...] = ()
    transition_out: Transition | None = None

    @property
    def duration_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)

    def contains(self, t: float) -> bool:
        return self.start_s <= t < self.end_s


@dataclass(frozen=True, slots=True)
class Timeline:
    project: str
    title: str
    target_runtime_s: float
    fps: float
    characters: tuple[Character, ...]
    sets: tuple[SetRef, ...]
    segments: tuple[Segment, ...]
    style: dict[str, Any] = field(default_factory=dict)
    target_runtime_range_s: tuple[float, float] = (840.0, 870.0)

    @property
    def duration_s(self) -> float:
        if not self.segments:
            return 0.0
        return max(s.end_s for s in self.segments)

    def segment_at(self, t: float) -> Segment | None:
        for seg in self.segments:
            if seg.contains(t):
                return seg
        return None

    def segments_of_type(self, kind: SegmentType) -> tuple[Segment, ...]:
        return tuple(s for s in self.segments if s.type == kind)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.segments:
            issues.append("no segments")
            return issues
        ordered = sorted(self.segments, key=lambda s: s.start_s)
        for i, seg in enumerate(ordered):
            if seg.end_s <= seg.start_s:
                issues.append(f"{seg.id}: end_s <= start_s")
            if i > 0:
                prev = ordered[i - 1]
                gap = seg.start_s - prev.end_s
                if gap > 0.05:
                    issues.append(f"gap {gap:.2f}s between {prev.id} and {seg.id}")
                elif gap < -0.05:
                    issues.append(f"overlap {abs(gap):.2f}s between {prev.id} and {seg.id}")
        char_ids = {c.id for c in self.characters}
        set_ids = {s.id for s in self.sets}
        for seg in self.segments:
            if seg.set_id not in set_ids:
                issues.append(f"{seg.id}: unknown set '{seg.set_id}'")
            for line in seg.audio.dialogue:
                if line.speaker not in char_ids:
                    issues.append(f"{seg.id}: unknown speaker '{line.speaker}'")
            if seg.audio.vo and seg.audio.vo.speaker not in char_ids:
                issues.append(f"{seg.id}: unknown VO speaker '{seg.audio.vo.speaker}'")
        lo, hi = self.target_runtime_range_s
        if not (lo <= self.duration_s <= hi + 30):
            issues.append(f"duration {self.duration_s:.1f}s outside target range [{lo}, {hi}]")
        return issues


def _parse_dialogue(raw: list[dict] | None) -> tuple[DialogueLine, ...]:
    if not raw:
        return ()
    out = []
    for d in raw:
        out.append(DialogueLine(
            speaker=d["speaker"], text=d["text"],
            to_camera=bool(d.get("to_camera", False)),
            tone=d.get("tone"), action=d.get("action"), from_location=d.get("from"),
        ))
    return tuple(out)


def _parse_vo(raw: dict | None) -> VoiceOver | None:
    if not raw:
        return None
    return VoiceOver(
        speaker=raw["speaker"], text=raw.get("text"), style=raw.get("style"),
        sections=tuple(raw.get("sections") or ()),
    )


def _parse_transition(raw: dict | None) -> Transition | None:
    if not raw:
        return None
    return Transition(
        type=TransitionType(raw["type"]),
        duration_s=float(raw.get("duration_s", 0.5)),
        to=raw.get("to"),
    )


def _parse_segment(raw: dict) -> Segment:
    audio_raw = raw.get("audio") or {}
    return Segment(
        id=raw["id"],
        type=SegmentType(raw["type"]),
        start_s=float(raw["start_s"]),
        end_s=float(raw["end_s"]),
        title=raw["title"],
        set_id=raw["set"],
        imagery=tuple(raw.get("imagery") or ()),
        audio=SegmentAudio(
            ambience=tuple(audio_raw.get("ambience") or ()),
            dialogue=_parse_dialogue(audio_raw.get("dialogue")),
            vo=_parse_vo(audio_raw.get("vo")),
            sfx=tuple(SfxCue(at_s=float(s["at_s"]), id=s["id"]) for s in (audio_raw.get("sfx") or [])),
        ),
        assets=tuple(raw.get("assets") or ()),
        camera=dict(raw.get("camera") or {}),
        edu_topics=tuple(raw.get("edu_topics") or ()),
        animation_cues=tuple(
            AnimationCue(at_s=float(c["at_s"]), action=c["action"])
            for c in (raw.get("animation_cues") or [])
        ),
        checklist=tuple(
            ChecklistItem(at_s=float(c["at_s"]), item=c["item"])
            for c in (raw.get("checklist") or [])
        ),
        overlays=tuple(
            Overlay(
                at_s=float(o["at_s"]), kind=o["kind"], asset=o["asset"],
                fields=tuple(o.get("fields") or ()),
            )
            for o in (raw.get("overlays") or [])
        ),
        transition_out=_parse_transition(raw.get("transition_out")),
    )


def load_timeline(path: str | Path) -> Timeline:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    characters = tuple(
        Character(id=c["id"], role=c["role"], display_name=c["display_name"])
        for c in data.get("characters", [])
    )
    sets = tuple(SetRef(id=s["id"], kind=s["kind"]) for s in data.get("sets", []))
    segments = tuple(_parse_segment(s) for s in data.get("segments", []))
    rng = data.get("target_runtime_range_s") or [840, 870]
    return Timeline(
        project=data["project"],
        title=data["title"],
        target_runtime_s=float(data.get("target_runtime_s", 855)),
        fps=float(data.get("fps", 24)),
        characters=characters,
        sets=sets,
        segments=segments,
        style=dict(data.get("style") or {}),
        target_runtime_range_s=(float(rng[0]), float(rng[1])),
    )


def default_timeline_path() -> Path:
    return Path(__file__).resolve().parent.parent / "content" / "timeline.json"
