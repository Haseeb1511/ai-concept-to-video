"""
FastAPI Server for the AI Short Generator
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
from typing import Optional, List
from contextlib import asynccontextmanager
import json
import uuid

from src.pipeline import run_custom_pipeline
from src.pipeline.runner import _pipeline_graph
from src.agent.seo_generator import generate_seo_metadata
from src.mcp.client import init_mcp_client, close_mcp_client
from src.chatbot.graph.chat_graph import chat_graph
from langchain_core.messages import HumanMessage

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Global lock to prevent parallel generations
    app.state.gen_lock = asyncio.Lock()
    
    # Initialize MCP tools
    print("[setup] Initializing MCP tools...")
    await init_mcp_client()

    # Save graph visualization as PNG in project root
    try:
        graph_png = _pipeline_graph.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(graph_png)
        print("Graph image saved to graph.png")
    except Exception as e:
        print(f"Could not save graph image: {e}")

    print("Graph + Checkpointer ready")
    yield
    
    # Global Cleanup
    print("[cleanup] Closing MCP tools...")
    await close_mcp_client()


app = FastAPI(
    title="AI Short Generator API", 
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


# ─── Chat Endpoint ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None   # Pass None to start a new conversation


@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Stream a chatbot response using the LangGraph YouTube channel chatbot.
    Returns NDJSON with:
      {"token": "..."} — streamed tokens
      {"tool_call": "tool_name"} — when a tool is invoked
      {"done": true, "thread_id": "..."} — final signal
      {"error": "..."} — on failure
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    async def stream_chat():
        try:
            input_state = {"messages": [HumanMessage(content=request.message)]}
            async for event in chat_graph.astream_events(
                input_state, config=config, version="v2"
            ):
                kind = event.get("event", "")
                name = event.get("name", "")

                # Stream LLM tokens
                if kind == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    if chunk and hasattr(chunk, "content") and chunk.content:
                        yield json.dumps({"token": chunk.content}) + "\n"

                # Notify when a tool is called
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown_tool")
                    yield json.dumps({"tool_call": tool_name}) + "\n"

            yield json.dumps({"done": True, "thread_id": thread_id}) + "\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield json.dumps({"error": str(e)}) + "\n"

    return StreamingResponse(stream_chat(), media_type="application/x-ndjson")


@app.get("/health")
def health_check():
    return {"status": "ok"}
