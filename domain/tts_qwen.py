"""Qwen3-TTS-12Hz-1.7B-VoiceDesign backend for Mr. Pipes pilot.

Natural-language voice design per character. Drop-in alternative to espeak-ng.

Requires:
  pip install -U qwen-tts soundfile torch
  NVIDIA GPU recommended (~4–8 GB VRAM with bfloat16)

Env:
  TTS_BACKEND=qwen
  QWEN_TTS_MODEL=Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign
  QWEN_TTS_DEVICE=cuda:0
  QWEN_TTS_DTYPE=bfloat16
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Natural-language voice design prompts (Southwest U.S. cast)
INSTRUCTS: dict[str, str] = {
    "mr_pipes": (
        "Warm middle-aged American man, slight Southwest accent, "
        "calm friendly tradesman, steady moderate pace, natural and practical"
    ),
    "host": (
        "Warm middle-aged American man, slight Southwest accent, "
        "calm friendly tradesman, steady moderate pace, natural and practical"
    ),
    "education": (
        "Clear American male narrator, patient explanatory tone, "
        "steady teaching pace, warm and professional"
    ),
    "dad": (
        "Confident middle-aged Texan homeowner, deeper voice, "
        "slightly defensive when challenged, casual jeans-and-boots energy"
    ),
    "mom": (
        "Warm American mother in her forties, clear mid-range voice, "
        "practical and caring, moderate pace"
    ),
    "teen": (
        "American teenage girl, natural and casual, "
        "slightly faster speech, informal tone"
    ),
    "mid_child": (
        "Young American child, light higher pitch, "
        "simple clear delivery, natural kid energy"
    ),
    "baby": (
        "Very young toddler voice, soft and light, "
        "short simple sounds, high pitch"
    ),
    "default": (
        "Neutral American adult voice, clear and natural, moderate pace"
    ),
}


_model: Any = None
_load_error: str | None = None


def qwen_available() -> bool:
    """True if qwen_tts + torch can be imported (model load deferred)."""
    try:
        import qwen_tts  # noqa: F401
        import torch  # noqa: F401
        import soundfile  # noqa: F401
        return True
    except Exception:
        return False


def instruct_for(speaker: str | None) -> str:
    if speaker and speaker in INSTRUCTS:
        return INSTRUCTS[speaker]
    return INSTRUCTS["default"]


def get_model():
    """Lazy-load VoiceDesign model once per process."""
    global _model, _load_error
    if _model is not None:
        return _model
    if _load_error is not None:
        raise RuntimeError(_load_error)
    try:
        import torch
        from qwen_tts import Qwen3TTSModel
    except Exception as e:
        _load_error = f"qwen-tts not importable: {e}"
        raise RuntimeError(_load_error) from e

    model_id = os.environ.get(
        "QWEN_TTS_MODEL", "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
    )
    device = os.environ.get("QWEN_TTS_DEVICE", "cuda:0")
    dtype_name = os.environ.get("QWEN_TTS_DTYPE", "bfloat16").lower()
    dtype = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }.get(dtype_name, torch.bfloat16)

    kwargs: dict[str, Any] = {
        "device_map": device,
        "dtype": dtype,
    }
    if os.environ.get("QWEN_TTS_FLASH_ATTN", "0") in ("1", "true", "yes"):
        kwargs["attn_implementation"] = "flash_attention_2"

    try:
        _model = Qwen3TTSModel.from_pretrained(model_id, **kwargs)
    except Exception as e:
        try:
            kwargs.pop("attn_implementation", None)
            if not torch.cuda.is_available():
                kwargs["device_map"] = "cpu"
                kwargs["dtype"] = torch.float32
            _model = Qwen3TTSModel.from_pretrained(model_id, **kwargs)
        except Exception as e2:
            _load_error = f"failed to load Qwen TTS: {e2}"
            raise RuntimeError(_load_error) from e2
    return _model


def synthesize_qwen(
    text: str,
    wav_path: Path,
    *,
    speaker: str | None = None,
    language: str = "English",
    instruct: str | None = None,
) -> bool:
    """Generate one line with VoiceDesign → mono WAV. Returns True on success."""
    text = (text or "").strip()
    if not text:
        return False
    try:
        import soundfile as sf
        model = get_model()
        desc = instruct or instruct_for(speaker)
        wavs, sr = model.generate_voice_design(
            text=text,
            language=language,
            instruct=desc,
        )
        wav_path = Path(wav_path)
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        audio = wavs[0]
        sf.write(str(wav_path), audio, sr)
        return wav_path.is_file() and wav_path.stat().st_size > 44
    except Exception as e:
        print(f"  qwen synthesize fail ({speaker}): {e}")
        return False
