"""
FastAPI Server for the AI Video Generator
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
from typing import Optional, List
from contextlib import asynccontextmanager
import json

from src.pipeline import run_custom_pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Global lock to prevent parallel generations
    app.state.gen_lock = asyncio.Lock()
    
    print("[setup] Backend ready for Custom Video generation")
    yield

app = FastAPI(
    title="AI Video Generator API", 
    version="1.1.0",
    lifespan=lifespan
)

class CustomVideoRequest(BaseModel):
    manim_code: str
    script: str
    tts_provider: Optional[str] = "gtts"

@app.post("/generate-custom-video")
async def generate_custom_video_endpoint(request: CustomVideoRequest):
    if app.state.gen_lock.locked():
        raise HTTPException(status_code=409, detail="A custom video generation is already in progress. Please wait for it to finish.")

    print(f"[custom] Received custom video request ({len(request.script)} chars script, {len(request.manim_code)} chars manim)")
    
    async def stream_generator():
        async with app.state.gen_lock:
            import queue
            import threading

            q = queue.Queue()

            def producer():
                try:
                    for chunk in run_custom_pipeline(request.manim_code, request.script, request.tts_provider):
                        q.put(chunk)
                except Exception as e:
                    q.put(json.dumps({"error": str(e)}))
                finally:
                    q.put(None)

            threading.Thread(target=producer).start()

            while True:
                chunk = await asyncio.to_thread(q.get)
                if chunk is None:
                    break
                yield chunk + "\n"

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")


@app.get("/health")
def health_check():
    return {"status": "ok"}
