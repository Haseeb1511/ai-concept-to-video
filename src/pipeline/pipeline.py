"""
Entry point for running the entire video generator pipeline.
"""
from src.pipeline.graph import build_pipeline_graph

def run_video_pipeline(topic: str, tts_provider: str = "gtts", app_graph=None) -> dict:
    """
    Executes the video pipeline synchronously.
    
    Args:
        topic (str): The subject of the video to create.
        app_graph: The pre-compiled LangGraph application (optional).
        
    Returns:
        dict: The final state, including final_video path or error details.
    """
    if app_graph is None:
        app_graph = build_pipeline_graph()
    
    app = app_graph
    
    initial_state = {"topic": topic, "tts_provider": tts_provider}
    print(f"=== Starting pipeline for topic: '{topic}' ===")
    
    final_state = app.invoke(initial_state)
    
    if final_state.get("error"):
        print(f"ERROR: Pipeline failed at node '{final_state.get('failed_node')}': {final_state.get('error')}")
    else:
        print(f"=== Pipeline succeeded! Output at: {final_state.get('final_video')} ===")
        
    return final_state
