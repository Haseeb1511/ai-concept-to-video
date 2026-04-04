import os
import requests
import base64
from pathlib import Path
from collections import deque
from dotenv import load_dotenv
import time

load_dotenv()

# ---------------------------------------------------------------------------
# Module-level token bucket rate limiter
# Free tier: 3 requests per 60 seconds
# ---------------------------------------------------------------------------
_request_times: deque = deque()
_RATE_LIMIT = 3
_RATE_WINDOW = 62  # slightly over 60s to be safe


def _throttle_google_tts():
    """Block until we are safely under the 3 req/min free-tier limit."""
    now = time.time()

    # Drop timestamps that have aged out of the window
    while _request_times and now - _request_times[0] > _RATE_WINDOW:
        _request_times.popleft()

    if len(_request_times) >= _RATE_LIMIT:
        oldest = _request_times[0]
        wait = _RATE_WINDOW - (now - oldest) + 0.5  # 0.5s safety margin
        print(
            f"⏳  Rate limiter: {len(_request_times)}/{_RATE_LIMIT} requests used "
            f"in window — sleeping {wait:.1f}s ..."
        )
        time.sleep(wait)

    # Record this request
    _request_times.append(time.time())


# ---------------------------------------------------------------------------
# Main TTS function
# ---------------------------------------------------------------------------

def generate_google_tts(
    text: str,
    out_path: Path,
    api_key: str,
    voice_id: str = "Charon",
) -> None:
    """Generate TTS using Google's Gemini Text-To-Speech API
    (gemini-2.5-flash-preview-tts).

    Automatically respects the free-tier limit of 3 requests/minute via a
    token-bucket throttle.  Retries up to 5 times on 429 errors as a
    secondary safety net.
    """
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
    )
    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [
            {
                "parts": [{"text": text}]
            }
        ],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_id
                    }
                }
            },
        },
    }

    max_retries = 5

    for attempt in range(max_retries):
        # ── throttle BEFORE every attempt (including retries) ──────────────
        _throttle_google_tts()

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=60
            )
            response.raise_for_status()

            data = response.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError(
                    f"No candidates returned from Google TTS. Response: {data}"
                )

            parts = candidates[0].get("content", {}).get("parts", [])
            audio_data_b64 = None
            for part in parts:
                inline_data = part.get("inlineData")
                if inline_data:
                    audio_data_b64 = inline_data.get("data")
                    break

            if not audio_data_b64:
                raise ValueError(
                    "Could not find inlineData in Google TTS response."
                )

            audio_bytes = base64.b64decode(audio_data_b64)

            # Audio from Gemini TTS is PCM 16-bit 24 kHz mono (L16)
            from pydub import AudioSegment

            try:
                audio_segment = AudioSegment(
                    data=audio_bytes,
                    sample_width=2,   # 16-bit
                    frame_rate=24000,
                    channels=1,
                )
                audio_segment.export(str(out_path), format="wav")
                print(f"✅  Google TTS audio saved → {out_path}")

            except Exception as e:
                print(
                    f"⚠️  Error parsing Gemini audio buffer natively: {e}. "
                    "Trying fallback mp3 path ..."
                )
                mp3_path = out_path.with_suffix(".mp3")
                mp3_path.write_bytes(audio_bytes)
                try:
                    AudioSegment.from_file(str(mp3_path)).export(
                        str(out_path), format="wav"
                    )
                except Exception:
                    # Last resort: write raw bytes and let downstream handle it
                    out_path.write_bytes(audio_bytes)
                mp3_path.unlink(missing_ok=True)
                print(f"✅  Google TTS audio saved (fallback) → {out_path}")

            # Success — exit
            return

        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                # The throttle should have prevented this, but handle it anyway
                backoff = 65 * (attempt + 1)  # progressive back-off
                print(
                    f"🚫  429 received despite throttle "
                    f"(attempt {attempt + 1}/{max_retries}). "
                    f"Backing off {backoff}s ..."
                )
                time.sleep(backoff)
                continue
            else:
                print(f"❌  Google TTS HTTP Error: {e}")
                try:
                    print(f"    Details: {e.response.json()}")
                except Exception:
                    pass
                raise

        except Exception as e:
            print(f"❌  Google TTS System Error: {e}")
            raise

    raise RuntimeError(
        "Google TTS failed after maximum retries due to rate limits."
    )