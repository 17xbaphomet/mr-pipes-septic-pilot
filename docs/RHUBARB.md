# Rhubarb Lip Sync + espeak-ng

Pipeline: **Text → espeak-ng WAV → Rhubarb mouth cues → MiniPlayer**

## Install

```bash
sudo apt-get install -y espeak-ng
bash tools/setup_rhubarb.sh
source .env.rhubarb
rhubarb --version
espeak-ng --version
```

| Path | Role |
|------|------|
| `/usr/bin/espeak-ng` | TTS |
| `/opt/rhubarb/rhubarb` | Lip-sync CLI |
| `/opt/rhubarb/res/` | Acoustic models |

Override: `export ESPEAK_BIN=...` / `export RHUBARB_BIN=...`

## Voice profiles (`domain/tts_config.py`)

| Role | Voice | Speed | Pitch |
|------|-------|-------|-------|
| mr_pipes / host | en-us | 138 | 38 |
| education | en-us | 132 | 40 |
| dad | en-us | 145 | 35 |
| mom | en-us+f3 | 145 | 55 |
| teen | en-us | 155 | 48 |

## Full pilot build

```bash
python tools/build_pilot.py --segment introduction --fps 8 --force-tts --force-rhubarb
python tools/build_pilot.py --preview --fps 6
python tools/build_pilot.py --all --fps 8
```

Outputs: `artifacts/audio/{seg}.wav`, `{seg}.rhubarb.json`, `segments/{seg}.mp4`, `pilot_full.mp4`, `pilot_script.txt`

## Fallback

1. Rhubarb (WAV + binary)
2. Text grapheme heuristics
3. Closed mouth (X)
