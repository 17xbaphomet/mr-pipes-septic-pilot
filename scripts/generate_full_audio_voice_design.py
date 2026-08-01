#!/usr/bin/env python3
"""
Mr. Pipes Septic Pilot - Full Audio Generation Script
Model: Qwen3-TTS-12Hz-1.7B-VoiceDesign

Generates the complete ~14-15 minute narration + character dialogue
using natural language voice design instructions.
"""

import os
import torch
import soundfile as sf
from pathlib import Path
from qwen_tts import Qwen3TTSModel
from pydub import AudioSegment  # optional: for final concatenation

# ====================== CONFIG ======================
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
OUTPUT_DIR = Path("audio_output_voice_design")
OUTPUT_DIR.mkdir(exist_ok=True)

DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
DTYPE = torch.bfloat16 if torch.cuda.is_available() else torch.float32

# ====================== VOICE DESIGNS ======================
# Optimized for Southwest US market - calm, trustworthy, practical male voice

MR_PIPES_INSTRUCT = (
    "A calm, friendly, middle-aged American man from the Southwest United States. "
    "Warm, slightly gravelly voice, clear diction, relaxed pace, trustworthy and "
    "practical tone like a local expert who has been doing septic work for 20 years. "
    "Speak naturally, with mild Texas/Arizona inflection but not exaggerated."
)

HOMEOWNER_INSTRUCT = (
    "Confident, broad-shouldered American man in his 40s, proud homeowner. "
    "Slightly louder and more assertive than Mr. Pipes, friendly but stubborn, "
    "natural Southwest accent."
)

WIFE_INSTRUCT = (
    "Warm, practical American woman in her late 30s / early 40s. "
    "Calm and caring tone, clear modern American English, Southwest region."
)

# ====================== FULL SCRIPT SEGMENTS ======================
# Each segment: (filename, text, language, instruct)

SEGMENTS = [
    # Cold Open
    (
        "00_cold_open",
        "Most folks only figure out how their septic system really works… once it stops working.",
        "English",
        MR_PIPES_INSTRUCT + " Speak softly and seriously, almost like a quiet warning."
    ),

    # Introduction
    (
        "01_introduction",
        "Hey there, I’m Mr. Pipes. I install and service septic systems and heating around this part of the country. "
        "Today I want to tell you a story I run into more often than you’d think. A good family who tried to do everything right… "
        "and still managed to get almost everything wrong without even realizing it. "
        "We’re gonna walk through what happened, and I’ll explain along the way why each little decision mattered.",
        "English",
        MR_PIPES_INSTRUCT
    ),

    # Scene 1 - Welcome
    (
        "02_welcome_mr_pipes",
        "Afternoon! Name’s Pipes. The county’s running sewer lines out this way. Just wanted to see if y’all were interested in a quote to hook up.",
        "English",
        MR_PIPES_INSTRUCT + " Friendly and professional."
    ),
    (
        "03_welcome_homeowner",
        "Appreciate the offer, but this place has been handling things the old-fashioned way for a hundred years. "
        "All natural. Self-contained. No monthly bills, no city nonsense. Already saved us a few thousand bucks right there.",
        "English",
        HOMEOWNER_INSTRUCT + " Proud and confident, with a satisfied laugh at the end."
    ),
    (
        "04_welcome_mr_pipes_reply",
        "Fair enough. You know where to find me if anything ever comes up.",
        "English",
        MR_PIPES_INSTRUCT + " Polite and easygoing."
    ),

    # Education 1 - Garbage Disposal
    (
        "05_education_garbage_disposal",
        "A garbage disposal feels handy, but every time you grind up food scraps, you’re sending solid material straight into the septic tank. "
        "That tank is built to let solids settle out. Food waste piles a lot more sludge in there than the system was designed for. "
        "Over time that sludge layer gets higher and higher. Once it reaches the outlet, it starts heading into the drainfield. "
        "And once solids get into the soil, they clog it for good. That’s why most of us in the business say: use the disposal as little as possible… or better yet, not at all.",
        "English",
        MR_PIPES_INSTRUCT + " Clear, patient teaching tone."
    ),

    # Education 2 - Diapers
    (
        "06_education_diapers",
        "Only two things should ever go down a toilet on a septic system: human waste and toilet paper. "
        "Diapers, wipes, paper towels — even the ones that say ‘flushable’ — don’t break down the way regular toilet paper does. "
        "They stay in one piece, catch on the baffles, and create blockages. "
        "What looks like it flushed is often still sitting in the tank or starting to slow everything down.",
        "English",
        MR_PIPES_INSTRUCT
    ),

    # Education 3 - Chemicals
    (
        "07_education_chemicals",
        "When the water starts draining slow, a lot of folks reach for a strong drain cleaner. "
        "Those products are made for regular house plumbing. In a septic tank they kill the good bacteria that break down the waste. "
        "A septic system is a living biological process. When you hit it with caustic chemicals, that process slows way down or stops.",
        "English",
        MR_PIPES_INSTRUCT + " Slightly more serious tone."
    ),

    # Scene - Morning problem + additives
    (
        "08_morning_problem",
        "No way. This is a living system. It needs the right bacteria, not more chemicals. I’m going to get some proper additives.",
        "English",
        HOMEOWNER_INSTRUCT + " Frustrated and determined."
    ),
    (
        "09_shop_request",
        "I need those septic additives. Something to get the digestion going again.",
        "English",
        HOMEOWNER_INSTRUCT
    ),
    (
        "10_shop_reply",
        "Sure, I carry those. But before we go that route… mind if I take a quick look at the system first? "
        "Sometimes it’s easier to see what’s actually going on.",
        "English",
        MR_PIPES_INSTRUCT + " Calm and helpful."
    ),

    # Education 4 - Additives myth
    (
        "11_education_additives",
        "Additives can’t remove the sludge that’s already sitting in the tank. "
        "The only way to get that material out is to pump it. "
        "Relying on additives usually just puts off the day the tank finally overflows into the drainfield.",
        "English",
        MR_PIPES_INSTRUCT
    ),

    # Education 5 - Building over drainfield
    (
        "12_education_building",
        "Heavy weight — whether it’s a building or vehicles — compacts the soil. "
        "Once that soil is packed down, water can’t move through it the way it’s supposed to. "
        "Pipes can get crushed too. And when the field fails, the building is sitting right on top of the problem.",
        "English",
        MR_PIPES_INSTRUCT + " Serious, cautionary tone."
    ),

    # Education 6 - Green grass
    (
        "13_education_green_grass",
        "Really lush, deep-green grass in one specific area isn’t a sign the system is fertilizing the lawn. "
        "Most of the time it means effluent is rising up close to the surface instead of being properly absorbed and treated underground.",
        "English",
        MR_PIPES_INSTRUCT
    ),

    # Reveal
    (
        "14_reveal",
        "That’s not fertilizer.",
        "English",
        MR_PIPES_INSTRUCT + " Soft, quiet, no judgment."
    ),

    # Positive section
    (
        "15_healthy_approach",
        "None of these problems happen overnight. They build up from a bunch of little everyday decisions that feel harmless at the time. "
        "Good news is, most of them are completely avoidable once you understand how the system actually works.\n\n"
        "Here’s what a healthy approach looks like:\n"
        "Know exactly where your tank and drainfield are.\n"
        "Get the tank pumped on a regular schedule.\n"
        "Keep the surface of the drainfield clear and protected.\n"
        "Be careful what goes down the drains.\n"
        "Call a pro when something feels off.\n\n"
        "A septic system is tough and can last decades… if you treat it like the living system it is.",
        "English",
        MR_PIPES_INSTRUCT + " Warm, encouraging, clear teaching style."
    ),

    # Closing
    (
        "16_closing",
        "If you’re not sure where your system is, or if the grass is looking a little too healthy in one spot — it’s worth a conversation. "
        "I’m local. Happy to help.",
        "English",
        MR_PIPES_INSTRUCT + " Friendly and inviting."
    ),
]


def main():
    print(f"Loading model: {MODEL_ID}")
    model = Qwen3TTSModel.from_pretrained(
        MODEL_ID,
        device_map=DEVICE,
        dtype=DTYPE,
        attn_implementation="flash_attention_2" if torch.cuda.is_available() else None,
    )
    print("Model loaded successfully.\n")

    generated_files = []

    for i, (filename, text, language, instruct) in enumerate(SEGMENTS, 1):
        print(f"[{i}/{len(SEGMENTS)}] Generating: {filename}")
        print(f"  Instruct: {instruct[:80]}...")

        wavs, sr = model.generate_voice_design(
            text=text,
            language=language,
            instruct=instruct,
            max_new_tokens=4096,
        )

        out_path = OUTPUT_DIR / f"{filename}.wav"
        sf.write(str(out_path), wavs[0], sr)
        generated_files.append(out_path)
        print(f"  → Saved: {out_path}\n")

    print("\nAll segments generated.")
    print(f"Output directory: {OUTPUT_DIR.resolve()}")

    # Optional: concatenate everything into one long file
    try:
        print("\nAttempting to concatenate all segments into full_audio.wav ...")
        combined = AudioSegment.empty()
        for f in generated_files:
            combined += AudioSegment.from_wav(f)
            combined += AudioSegment.silent(duration=400)  # short pause between segments

        full_path = OUTPUT_DIR / "full_pilot_audio.wav"
        combined.export(str(full_path), format="wav")
        print(f"Full combined audio saved to: {full_path}")
    except Exception as e:
        print(f"Concatenation skipped (pydub not available or error): {e}")
        print("You can concatenate the individual .wav files later with ffmpeg or Audacity.")


if __name__ == "__main__":
    main()
