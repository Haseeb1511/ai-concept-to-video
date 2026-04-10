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






# to check differnt voice smaple
# client = OpenAI()

# voices = [
#     "alloy","ash","ballad","coral","echo",
#     "fable","nova","onyx","sage","shimmer",
#     "verse","marin","cedar"
# ]

# text = "Hello, this is a test of OpenAI text to speech voices."

# for v in voices:
#     out_file = Path(f"{v}.mp3")
    
#     with client.audio.speech.with_streaming_response.create(
#         model="gpt-4o-mini-tts",
#         voice=v,
#         input=text
#     ) as response:
#         response.stream_to_file(out_file)

#     print(f"Generated voice: {v}")


# onyx
# fable
# echo