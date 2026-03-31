"""
FastAPI Server for the AI Video Generator
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from src.pipeline.graph import build_pipeline_graph
from src.pipeline.pipeline import run_video_pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize the graph and store in app.state
    print("[setup] Initializing LangGraph state graph...")
    app.state.graph = build_pipeline_graph()
    
    # 2. Save the graph visualization as graph.png in the root
    try:
        print("[setup] Generating graph visualization to graph.png")
        graph_png = app.state.graph.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(graph_png)
        print("Graph image saved to graph.png")
    except Exception as e:
        print(f"Could not save graph image: {e}")
    
    print("Graph + Checkpointer ready")
    yield




app = FastAPI(
    title="AI Video Generator API", 
    version="1.0.0",
    lifespan=lifespan
)



class VideoRequest(BaseModel):
    topic: str
    tts_provider: Optional[str] = "gtts"

class VideoResponse(BaseModel):
    video_path: Optional[str] = None
    error: Optional[str] = None
    failed_node: Optional[str] = None

    

@app.post("/generate-video", response_model=VideoResponse)
async def generate_video_endpoint(request: VideoRequest):
    topic = request.topic
    print(f"Received API request to generate video for: {topic}")
    
    # Since Manim and other tasks are blocking IO, we run this in a threadpool
    # to avoid blocking the async event loop of FastAPI.
    loop = asyncio.get_event_loop()
    try:
        # Use the pre-built graph from app.state
        final_state = await loop.run_in_executor(
            None, 
            run_video_pipeline, 
            topic, 
            request.tts_provider,
            app.state.graph
        )
        
        if final_state.get("error"):
            return VideoResponse(
                error=final_state["error"],
                failed_node=final_state.get("failed_node")
            )
            
        return VideoResponse(video_path=final_state.get("final_video"))
        
    except Exception as e:
        print(f"ERROR: API unhandled exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    return {"status": "ok"}
