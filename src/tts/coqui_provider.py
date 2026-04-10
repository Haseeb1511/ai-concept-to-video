from TTS.api import TTS as CoquiTTS
import os
from pathlib import Path

def generate_coqui_tts(text: str, out_path: Path) -> None:
    """Coqui TTS (local, no API key)."""
    try:
        # Load the default model
        tts = CoquiTTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", gpu=False)
        tts.tts_to_file(text=text, file_path=str(out_path))
        print(f"Coqui audio saved to {out_path}")
    except Exception as e:
        print(f"Coqui TTS Error: {e}")
        raise e
