#!/usr/bin/env python3
"""
Mr. Pipes Septic Pilot – Full Audio Generation Script
Model: Qwen3-TTS-12Hz-1.7B-VoiceDesign
Target: Complete ~14-15 minute educational cartoon narration
Market: Southwest US (Texas / Arizona / New Mexico style)
"""

import os
import torch
import soundfile as sf
from pathlib import Path
from qwen_tts import Qwen3TTSModel

# ====================== CONFIG ======================
OUTPUT_DIR = Path("audio_output_voicedesign")
OUTPUT_DIR.mkdir(exist_ok=True)

DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
DTYPE = torch.bfloat16 if torch.cuda.is_available() else torch.float32

# Strong voice description for Mr. Pipes (Southwest-friendly)
MR_PIPES_VOICE = (
    "A warm, friendly, middle-aged American man in his late 40s to mid 50s. "
    "Slightly deep, calm and trustworthy voice with a mild Southwestern US accent "
    "(Texas / Arizona style – relaxed, clear, not heavy Southern). "
    "Speaks at a natural, measured pace, slightly folksy but professional. "
    "Sounds like a competent local tradesman who knows his stuff and cares about the customer. "
    "Warm, reassuring, and never condescending."
)

# ====================== FULL SCRIPT SEGMENTS ======================
# Split into logical segments for better quality & memory

SEGMENTS = [
    {
        "id": "01_cold_open",
        "text": (
            "Most folks only figure out how their septic system really works… "
            "once it stops working."
        ),
        "instruct": MR_PIPES_VOICE + " Soft, slightly serious, reflective tone."
    },
    {
        "id": "02_intro",
        "text": (
            "Hey there, I’m Mr. Pipes. I install and service septic systems and heating around this part of the country. "
            "Today I want to tell you a story I run into more often than you’d think. "
            "A good family who tried to do everything right… and still managed to get almost everything wrong without even realizing it. "
            "We’re gonna walk through what happened, and I’ll explain along the way why each little decision mattered."
        ),
        "instruct": MR_PIPES_VOICE + " Friendly, welcoming, conversational."
    },
    {
        "id": "03_welcome_scene",
        "text": (
            "Afternoon! Name’s Pipes. The county’s running sewer lines out this way. "
            "Just wanted to see if y’all were interested in a quote to hook up.\n\n"
            "Appreciate the offer, but this place has been handling things the old-fashioned way for a hundred years. "
            "All natural. Self-contained. No monthly bills, no city nonsense. Already saved us a few thousand bucks right there.\n\n"
            "Fair enough. You know where to find me if anything ever comes up."
        ),
        "instruct": MR_PIPES_VOICE + " Natural dialogue pace, friendly."
    },
    {
        "id": "04_education_garbage_disposal",
        "text": (
            "A garbage disposal feels handy, but every time you grind up food scraps, you’re sending solid material straight into the septic tank. "
            "That tank is built to let solids settle out. Food waste piles a lot more sludge in there than the system was designed for. "
            "Over time that sludge layer gets higher and higher. Once it reaches the outlet, it starts heading into the drainfield. "
            "And once solids get into the soil, they clog it for good. That’s why most of us in the business say: use the disposal as little as possible… or better yet, not at all."
        ),
        "instruct": MR_PIPES_VOICE + " Clear, educational, calm and practical."
    },
    {
        "id": "05_education_diapers_chemicals",
        "text": (
            "Only two things should ever go down a toilet on a septic system: human waste and toilet paper. "
            "Diapers, wipes, paper towels — even the ones that say ‘flushable’ — don’t break down the way regular toilet paper does. "
            "They stay in one piece, catch on the baffles, and create blockages. "
            "What looks like it flushed is often still sitting in the tank or starting to slow everything down.\n\n"
            "When the water starts draining slow, a lot of folks reach for a strong drain cleaner. "
            "Those products are made for regular house plumbing. In a septic tank they kill the good bacteria that break down the waste. "
            "A septic system is a living biological process. When you hit it with caustic chemicals, that process slows way down or stops."
        ),
        "instruct": MR_PIPES_VOICE + " Calm explanatory tone, slightly more serious."
    },
    {
        "id": "06_morning_problem_and_shop",
        "text": (
            "The next morning the toilet won’t flush right. Mom suggests more drain cleaner. "
            "Dad says no — this is a living system, it needs the right bacteria, not more chemicals. "
            "He heads over to my shop looking for additives.\n\n"
            "I tell him: Sure, I carry those. But before we go that route… mind if I take a quick look at the system first? "
            "Sometimes it’s easier to see what’s actually going on."
        ),
        "instruct": MR_PIPES_VOICE + " Narrative storytelling style, natural."
    },
    {
        "id": "07_questions_and_green_grass",
        "text": (
            "Back at the house I start asking simple questions. "
            "When was the tank last pumped? Do you know exactly where the tank and the drainfield are? "
            "Has anybody built or driven over the field area?\n\n"
            "Dad gets more defensive with every answer he doesn’t have. "
            "Finally he points to the new garage and says the deep green grass means the system is feeding the lawn — that it’s healthy."
        ),
        "instruct": MR_PIPES_VOICE + " Calm, slightly concerned storytelling."
    },
    {
        "id": "08_education_additives_building_grass",
        "text": (
            "Additives can’t remove the sludge that’s already sitting in the tank. "
            "The only way to get that material out is to pump it. "
            "Relying on additives usually just puts off the day the tank finally overflows into the drainfield.\n\n"
            "Heavy weight — whether it’s a building or vehicles — compacts the soil. "
            "Once that soil is packed down, water can’t move through it the way it’s supposed to. "
            "Pipes can get crushed too. And when the field fails, the building is sitting right on top of the problem.\n\n"
            "Really lush, deep-green grass in one specific area isn’t a sign the system is fertilizing the lawn. "
            "Most of the time it means effluent is rising up close to the surface instead of being properly absorbed and treated underground."
        ),
        "instruct": MR_PIPES_VOICE + " Clear, serious educational tone."
    },
    {
        "id": "09_reveal",
        "text": (
            "We walk over to the new garage as the light starts fading. "
            "The grass around it is glowing an unnatural bright green in a perfect rectangular shape that matches a drainfield. "
            "Long quiet moment.\n\n"
            "That’s not fertilizer."
        ),
        "instruct": MR_PIPES_VOICE + " Soft, quiet, impactful delivery."
    },
    {
        "id": "10_healthy_approach",
        "text": (
            "None of these problems happen overnight. They build up from a bunch of little everyday decisions that feel harmless at the time. "
            "Good news is, most of them are completely avoidable once you understand how the system actually works.\n\n"
            "Here’s what a healthy approach looks like:\n"
            "Know exactly where your tank and drainfield are.\n"
            "Get the tank pumped on a regular schedule.\n"
            "Keep the surface of the drainfield clear and protected.\n"
            "Be careful what goes down the drains.\n"
            "Call a pro when something feels off.\n\n"
            "A septic system is tough and can last decades… if you treat it like the living system it is."
        ),
        "instruct": MR_PIPES_VOICE + " Warm, positive, reassuring."
    },
    {
        "id": "11_closing",
        "text": (
            "If you’re not sure where your system is, or if the grass is looking a little too healthy in one spot — it’s worth a conversation. "
            "I’m local. Happy to help."
        ),
        "instruct": MR_PIPES_VOICE + " Warm, friendly closing."
    },
]

def main():
    print("Loading Qwen3-TTS-12Hz-1.7B-VoiceDesign…")
    model = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        device_map=DEVICE,
        dtype=DTYPE,
        attn_implementation="flash_attention_2" if torch.cuda.is_available() else None,
    )

    all_wavs = []
    sample_rate = None

    for i, seg in enumerate(SEGMENTS, 1):
        print(f"\n[{i}/{len(SEGMENTS)}] Generating: {seg['id']}")
        print(f"Text preview: {seg['text'][:80]}…")

        wavs, sr = model.generate_voice_design(
            text=seg["text"],
            language="English",
            instruct=seg["instruct"],
        )

        out_path = OUTPUT_DIR / f"{seg['id']}.wav"
        sf.write(str(out_path), wavs[0], sr)
        print(f"Saved → {out_path}")

        all_wavs.append(wavs[0])
        sample_rate = sr

    # Optional: concatenate everything into one full track
    print("\nConcatenating full audio…")
    import numpy as np
    full_audio = np.concatenate(all_wavs)
    full_path = OUTPUT_DIR / "00_FULL_NARRATION_Mr_Pipes.wav"
    sf.write(str(full_path), full_audio, sample_rate)
    print(f"Full narration saved → {full_path}")
    print("\nDone!")

if __name__ == "__main__":
    main()
