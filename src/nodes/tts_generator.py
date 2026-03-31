"""
Node 2 — TTS Generation
───────────────────────
Converts each scene's narration text into a WAV audio file.
Supports three providers:
  • gtts       — free, no API key required (default fallback)
  • elevenlabs — high-quality neural voice
  • coqui      — local open-source TTS
"""

import os
from pathlib import Path

from src.agent.model_loader import (
    TTS_PROVIDER,
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    AUDIO_DIR,
)

# Import new providers
from src.tts.elevenlabs_provider import generate_elevenlabs_tts
from src.tts.coqui_provider import generate_coqui_tts
from src.tts.open_ai import text_to_speech_bytes # Note: This one returns bytes

def _gtts(text: str, out_path: Path) -> None:
    """Google Text-to-Speech (free, requires internet)."""
    from gtts import gTTS
    tts = gTTS(text=text, lang="en", slow=False)
    # gTTS saves to mp3; we convert to wav via pydub
    mp3_path = out_path.with_suffix(".mp3")
    tts.save(str(mp3_path))
    _mp3_to_wav(mp3_path, out_path)
    mp3_path.unlink(missing_ok=True)

def _openai_adapter(text: str, out_path: Path) -> None:
    """Adapter for OpenAI TTS bytes-based function."""
    import asyncio
    # We need to run the async function in a sync context
    audio_bytes = asyncio.run(text_to_speech_bytes(text))
    mp3_path = out_path.with_suffix(".mp3")
    mp3_path.write_bytes(audio_bytes)
    _mp3_to_wav(mp3_path, out_path)
    mp3_path.unlink(missing_ok=True)

def _elevenlabs_adapter(text: str, out_path: Path) -> None:
    generate_elevenlabs_tts(text, out_path, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID)
    mp3_path = out_path.with_suffix(".mp3")
    if mp3_path.exists():
        _mp3_to_wav(mp3_path, out_path)
        mp3_path.unlink(missing_ok=True)

def _mp3_to_wav(mp3: Path, wav: Path) -> None:
    from pydub import AudioSegment
    audio = AudioSegment.from_mp3(str(mp3))
    audio.export(str(wav), format="wav")

# ─────────────────────────────────────────────
# DISPATCH TABLE
# ─────────────────────────────────────────────
_PROVIDERS = {
    "gtts": _gtts,
    "elevenlabs": _elevenlabs_adapter,
    "coqui": generate_coqui_tts,
    "openai": _openai_adapter,
}


def _synthesise(text: str, out_path: Path, provider: str) -> None:
    provider_fn = _PROVIDERS.get(provider)
    if provider_fn is None:
        raise ValueError(f"Unknown TTS provider: '{provider}'. Choose from {list(_PROVIDERS)}")
    provider_fn(text, out_path)


# ─────────────────────────────────────────────
# NODE FUNCTION
# ─────────────────────────────────────────────
def tts_generation_node(state: dict) -> dict:
    script = state.get("script", {})
    scenes = script.get("scenes", [])

    if not scenes:
        return {"error": "No scenes found in script.", "failed_node": "tts_generation"}

    print(f"[tts_generator] Synthesising audio for {len(scenes)} scenes using '{TTS_PROVIDER}'")

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_files: list[str] = []

    for idx, scene in enumerate(scenes, start=1):
        text = scene.get("text", "").strip()
        if not text:
            print(f"WARNING: [tts_generator] Scene {idx} has empty text — skipping.")
            continue

        out_path = AUDIO_DIR / f"scene_{idx}.wav"
        try:
            _synthesise(text, out_path, state.get("tts_provider", "gtts"))
            audio_files.append(str(out_path))
            print(f"[tts_generator] Scene {idx} → {out_path.name} (using {state.get('tts_provider')})")
        except Exception as exc:
            print(f"ERROR: [tts_generator] Scene {idx} TTS failed: {exc}")
            return {"error": str(exc), "failed_node": "tts_generation"}

    return {"audio_files": audio_files}
