# Rhubarb Lip Sync

## Install

```bash
# project helper (downloads v1.14.0 Linux if needed)
bash tools/setup_rhubarb.sh

# or use already installed system binary
source .env.rhubarb
rhubarb --version   # → Rhubarb Lip Sync version 1.14.0
```

Binary location (this environment):

| Path | Role |
|------|------|
| `/opt/rhubarb/rhubarb` | Executable (workdir is noexec) |
| `/opt/rhubarb/res/` | Acoustic models (required) |
| `/usr/local/bin/rhubarb` | Symlink on PATH |
| `tools/rhubarb/` | Project copy of binary + res |

Override: `export RHUBARB_BIN=/path/to/rhubarb`

## CLI usage

```bash
rhubarb -f json -o out.rhubarb.json --dialogFile dialog.txt audio.wav
```

Helper:

```bash
python tools/run_rhubarb.py --check
python tools/run_rhubarb.py artifacts/audio/intro_mr_pipes.wav \
  --dialog-file artifacts/audio/intro_mr_pipes.dialog.txt
```

## Python API

```python
from domain.lipsync import cues_from_rhubarb, sample_viseme_at
from pathlib import Path

cues = cues_from_rhubarb(
    Path("artifacts/audio/intro_mr_pipes.wav"),
    transcript="I'm Mr. Pipes...",
)
viseme, intensity = sample_viseme_at(cues, t=1.5)
```

Fallback order in `extract_visemes()`:

1. Rhubarb (if binary + audio)
2. Energy-based from WAV
3. Text-driven grapheme heuristics

## Test assets

- `artifacts/audio/intro_mr_pipes.wav` — espeak-ng TTS for intro line
- `artifacts/audio/intro_mr_pipes.dialog.txt`
- `artifacts/audio/intro_mr_pipes.rhubarb.json` — 35 mouth cues, ~10.4s
