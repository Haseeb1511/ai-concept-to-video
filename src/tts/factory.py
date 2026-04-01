import os
from pathlib import Path

def _synthesise_tts(text: str, out_path: Path, provider: str) -> None:
    """Entry point for all TTS synthesis."""
    if provider == "gtts":
        from gtts import gTTS
        from pydub import AudioSegment
        mp3_path = out_path.with_suffix(".mp3")
        gTTS(text=text, lang="en", slow=False).save(str(mp3_path))
        AudioSegment.from_mp3(str(mp3_path)).export(str(out_path), format="wav")
        mp3_path.unlink(missing_ok=True)

    elif provider == "elevenlabs":
        from src.tts.elevenlabs_provider import generate_elevenlabs_tts
        from src.agent.model_loader import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID
        from pydub import AudioSegment
        generate_elevenlabs_tts(text, out_path, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID)
        mp3_path = out_path.with_suffix(".mp3")
        if mp3_path.exists():
            AudioSegment.from_mp3(str(mp3_path)).export(str(out_path), format="wav")
            mp3_path.unlink(missing_ok=True)

    elif provider == "openai":
        import asyncio
        from src.tts.open_ai import text_to_speech_bytes
        from pydub import AudioSegment
        audio_bytes = asyncio.run(text_to_speech_bytes(text))
        mp3_path = out_path.with_suffix(".mp3")
        mp3_path.write_bytes(audio_bytes)
        AudioSegment.from_mp3(str(mp3_path)).export(str(out_path), format="wav")
        mp3_path.unlink(missing_ok=True)

    elif provider == "coqui":
        from src.tts.coqui_provider import generate_coqui_tts
        generate_coqui_tts(text, out_path)

    else:
        # Default fallback to gTTS
        _synthesise_tts(text, out_path, "gtts")
