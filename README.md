# Mr. Pipes — Septic System Pilot

~14:30 educational cartoon: family story + technical cutaways (same engine family as vector-toon-pipeline).

## Layout

```
content/timeline.json      # full pilot timeline (15 segments)
content/assets_manifest.json
domain/scene_schema.py     # typed Timeline / Segment loader
domain/lipsync.py          # Preston Blair visemes, text/energy/Rhubarb
domain/rhubarb_config.py
application/mini_player.py # segment renderer (SVG + subtitles + mouth)
assets/characters/         # mr_pipes, dad
assets/sets/               # workshop, house_exterior_day
assets/diagrams/           # septic tank cross-section
tools/setup_rhubarb.sh     # install Rhubarb Lip Sync 1.14.0
tools/run_rhubarb.py
docs/RHUBARB.md
```

## Quick start

```bash
# Rhubarb (optional, for production lip-sync)
bash tools/setup_rhubarb.sh
source .env.rhubarb

# List timeline segments
python3 -m application.mini_player --list

# Render intro stills
python3 -m application.mini_player --segment introduction

# MP4
python3 -m application.mini_player --segment introduction --out artifacts/intro.mp4 --fps 8
```

Requires: Python 3.11+, Pillow, cairosvg, ffmpeg. Rhubarb binary is **not** in git (download via setup script).

## License

Project assets and code: private pilot content. Rhubarb Lip Sync is third-party (see its LICENSE).
