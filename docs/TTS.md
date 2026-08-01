# TTS Engine

Pipeline: **dialogue lines → per-speaker WAV → concat + gaps → fit duration → Rhubarb → mux**

Backends (env `TTS_BACKEND` or `--tts-backend`):

| Backend | Engine | Quality | Needs |
|---------|--------|---------|-------|
| `espeak` (default) | espeak-ng | robotic, fast | `apt install espeak-ng` |
| `qwen` | Qwen3-TTS-12Hz-1.7B-VoiceDesign | natural, designed voices | GPU + `pip install qwen-tts torch soundfile` |

---

## espeak-ng (default)

```bash
sudo apt-get install -y espeak-ng
python tools/build_pilot.py --segment introduction --force-tts
```

Profiles in `domain/tts_config.py` → `PROFILES` (pitch, speed, voice).

---

## Qwen3 VoiceDesign

Natural-language voice design per character (no reference audio).

```bash
pip install -U qwen-tts soundfile torch

export TTS_BACKEND=qwen
# optional: QWEN_TTS_MODEL, QWEN_TTS_DEVICE=cuda:0, QWEN_TTS_DTYPE=bfloat16

python tools/build_pilot.py --segment introduction --tts-backend qwen --force-tts --force-rhubarb
```

### Character instructs (`domain/tts_qwen.py`)

| Speaker | instruct (summary) |
|---------|-------------------|
| mr_pipes | Warm middle-aged American, SW accent, calm tradesman |
| dad | Confident middle-aged Texan, deeper, slightly defensive |
| mom | Warm mother, mid-range, practical |
| teen | Teenage girl, casual, slightly faster |
| mid_child | Young child, higher pitch |
| education | Clear male narrator, patient teaching pace |

Edit `INSTRUCTS` in `domain/tts_qwen.py` to refine personas.

### API used

```python
from qwen_tts import Qwen3TTSModel
model = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", ...)
wavs, sr = model.generate_voice_design(
    text="...", language="English",
    instruct="Warm middle-aged American man, slight Southwest accent...",
)
```

---

## Shared features (both backends)

1. **Per-line synthesis** — each dialogue/VO line uses that speaker’s profile/instruct
2. **Concat + silence gaps** — between lines (`line_pause_ms`)
3. **Duration fit** — pad / mild `atempo` so WAV ≈ `segment.duration_s`
4. **Cache** — `{seg}.meta.json` with text+profile hash (includes backend)

## Build examples

```bash
# espeak (default)
python tools/build_pilot.py --segment scene_1_welcome --fps 8 --force-tts --force-rhubarb

# Qwen VoiceDesign
python tools/build_pilot.py --segment scene_1_welcome --tts-backend qwen --fps 8 --force-tts --force-rhubarb
```
