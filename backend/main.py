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
from src.agent.seo_generator import generate_seo_metadata
from src.mcp.client import init_mcp_client, close_mcp_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Global lock to prevent parallel generations
    app.state.gen_lock = asyncio.Lock()
    
    # Initialize MCP tools
    print("[setup] Initializing MCP tools...")
    await init_mcp_client()
    
    print("[setup] Backend ready for Custom Video generation")
    yield
    
    # Global Cleanup
    print("[cleanup] Closing MCP tools...")
    await close_mcp_client()


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

class SEORequest(BaseModel):
    manim_code: str
    script: str

@app.post("/generate-seo")
async def generate_seo_endpoint(request: SEORequest):
    print(f"[seo] Receiving request for SEO metadata Generation")
    try:
        # Run in a separate thread to prevent blocking the async event loop
        metadata = await asyncio.to_thread(generate_seo_metadata, request.manim_code, request.script)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "ok"}
