import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def generate_elevenlabs_tts(text: str, out_path: Path, api_key: str, voice_id: str) -> None:
    """ElevenLabs high-quality TTS."""
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY is not set.")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        # Save mp3 first, then convert (actual conversion happens in node or utility)
        mp3_path = out_path.with_suffix(".mp3")
        mp3_path.write_bytes(response.content)
        
        # Note: Caller is responsible for mp3 -> wav conversion if needed
        # Or we can do it here if pydub is installed. 
        # For now, we write the bytes and let the node handle the pathing.
        print(f"ElevenLabs audio saved to {mp3_path}")
        
    except Exception as e:
        print(f"ElevenLabs TTS Error: {e}")
        raise e
