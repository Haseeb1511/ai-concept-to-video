import requests
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def generate_deepgram_tts(text: str, out_path: Path, api_key: str, voice_id: str) -> None:
    """Deepgram high-quality TTS."""
    if not api_key:
        raise ValueError("DEEPGRAM_API_KEY is not set.")
    
    url = f"https://api.deepgram.com/v1/speak?model={voice_id}"
    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        # Save mp3 first, then convert (actual conversion happens in factory)
        mp3_path = out_path.with_suffix(".mp3")
        mp3_path.write_bytes(response.content)
        
        print(f"Deepgram audio saved to {mp3_path}")
        
    except requests.exceptions.HTTPError as e:
        print(f"Deepgram HTTP Error: {e}")
        try:
            print(f"Details: {e.response.json()}")
        except Exception:
            pass
        raise e
    except Exception as e:
        print(f"Deepgram TTS Error: {e}")
        raise e
