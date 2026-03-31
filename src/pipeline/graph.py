from langgraph.graph import StateGraph, START, END

from src.pipeline.state import VideoGenerationState
from src.nodes.script_generator import script_generator_node
from src.nodes.tts_generator import tts_generation_node
from src.nodes.audio_duration import audio_duration_node
from src.nodes.scene_planner import scene_planner_node
from src.nodes.manim_renderer import manim_render_node
from src.nodes.video_stitcher import video_stitch_node


def _route_errors(state: VideoGenerationState):
    """Router function to stop execution if an error occurred in any node."""
    if state.get("error"):
        print(f"Routing to END due to error in {state.get('failed_node')}: {state.get('error')}")
        return END
    return "next"


def build_pipeline_graph():
    """Builds and returns the LangGraph application."""
    print("[graph] Building LangGraph state graph")
    
    # 1. Initialize Graph
    workflow = StateGraph(VideoGenerationState)
    
    # 2. Add Nodes
    workflow.add_node("script_generator", script_generator_node)
    workflow.add_node("tts_generation", tts_generation_node)
    workflow.add_node("audio_duration", audio_duration_node)
    workflow.add_node("scene_planner", scene_planner_node)
    workflow.add_node("manim_render", manim_render_node)
    workflow.add_node("video_stitch", video_stitch_node)
    
    # 3. Add Edges (linear flow with error checking)
    workflow.add_edge(START, "script_generator")
    
    # If thier is error we end the graph if thier is no error we pass the information to the next node
    # After each step, we can use conditional routing to check for errors
    def route_after_script(state): return END if state.get("error") else "tts_generation"
    workflow.add_conditional_edges("script_generator", route_after_script, {END: END, "tts_generation": "tts_generation"})
    
    def route_after_tts(state): return END if state.get("error") else "audio_duration"
    workflow.add_conditional_edges("tts_generation", route_after_tts, {END: END, "audio_duration": "audio_duration"})
    
    def route_after_audio(state): return END if state.get("error") else "scene_planner"
    workflow.add_conditional_edges("audio_duration", route_after_audio, {END: END, "scene_planner": "scene_planner"})
    
    def route_after_planner(state): return END if state.get("error") else "manim_render"
    workflow.add_conditional_edges("scene_planner", route_after_planner, {END: END, "manim_render": "manim_render"})
    
    def route_after_render(state): return END if state.get("error") else "video_stitch"
    workflow.add_conditional_edges("manim_render", route_after_render, {END: END, "video_stitch": "video_stitch"})
    
    workflow.add_edge("video_stitch", END)
    
    # 4. Compile the graph
    app = workflow.compile()
    return app
