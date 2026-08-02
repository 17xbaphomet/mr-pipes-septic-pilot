# Mr. Pipes Septic Pilot

Educational cartoon pilot video for the Southwest US market about common septic system mistakes.

## Final Character Cast (unified soft cartoon style)

- **Mr. Pipes** – Orange high-vis work suit, hard hat with headlamp, friendly expert
- **Dad** – Cowboy hat, flannel shirt, proud homeowner
- **Mom** – Modest dress, warm practical mother
- **Teen daughter** – Long hair, casual outfit
- **Mid-child** – Big headphones, blue shirt
- **Baby** – Soft onesie

## Quick Start – Full Generation with Audio

```bash
# 1. Install dependencies
pip install torch soundfile pydub qwen-tts

# 2. Generate all audio tracks (Qwen3-TTS-12Hz-1.7B-VoiceDesign)
python scripts/generate_full_audio_voice_design.py

# 3. Or run the master pipeline
python scripts/generate_full_pilot.py
```

Audio output will be written to `audio_output_voice_design/`.

## Project Structure

- `assets/characters/` – Final SVG characters
- `assets/sets/` – Scene backgrounds
- `assets/props/` – Interactive objects
- `assets/diagrams/` – Educational graphics
- `assets/graphics/` – Title / end cards
- `content/timeline.json` – Full scene timing & dialogue
- `scripts/generate_full_audio_voice_design.py` – Complete TTS pipeline
- `scripts/generate_full_pilot.py` – Master generation entry point

## Voice Design

All voices use natural-language instructions optimized for a calm, trustworthy Southwest-US tone.

## Status

- Characters: **Final & approved**
- Core sets & props: Present
- Full dialogue script + TTS pipeline: Ready
- Ready for scene assembly and final render
