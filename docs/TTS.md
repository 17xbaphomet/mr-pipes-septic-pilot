# TTS Engine (espeak-ng)

Pipeline: **dialogue lines → per-speaker WAV → concat + gaps → fit duration → Rhubarb → mux**

## Install

```bash
sudo apt-get install -y espeak-ng
```

## API (`domain/tts_config.py`)

```python
from domain.tts_config import synthesize, synthesize_segment_from_schema

synthesize("Afternoon!", Path("out.wav"), speaker="mr_pipes")
synthesize_segment_from_schema(seg, Path("artifacts/audio/scene_1_welcome.wav"), force=True)
```

## Voice profiles

| Speaker | Voice | Speed | Pitch |
|---------|-------|-------|-------|
| mr_pipes / host | en-us | 136 | 36 |
| education | en-us | 130 | 38 |
| dad | en-us | 142 | 32 |
| mom | en-us+f3 | 140 | 55 |
| teen | en-us | 155 | 50 |
| mid_child | en-us | 150 | 58 |
| baby | en-us | 120 | 70 |

## Features

1. Per-line synthesis (speaker profile)
2. Concat + silence gaps between lines
3. Duration fit to `segment.duration_s` (pad / mild atempo)
4. Cache via `{seg}.meta.json` text+profile hash

## Build

```bash
python tools/build_pilot.py --segment scene_1_welcome --fps 8 --force-tts --force-rhubarb
```
