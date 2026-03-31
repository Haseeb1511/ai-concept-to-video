from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
load_dotenv()

client = AsyncOpenAI()

async def text_to_speech_bytes(text: str) -> bytes:
    if not text:
        raise ValueError("Text cannot be empty")
    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response.content
    except Exception as e:
        print(f"OpenAI TTS Error: {e}")
        raise e


# tts-1
# 1,000,000 characters → $15
# $0.06 per 4096 characters of speech