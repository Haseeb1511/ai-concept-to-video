"""
LangGraph State definition for the video generation pipeline.
TypedDict keeps state fully serialisable and inspectable.
"""

from typing import TypedDict, Optional


class VideoGenerationState(TypedDict, total=False):
    # Input 
    topic: str                      # "Explain Attention Mechanism"
    tts_provider: str               # "gtts", "elevenlabs", "openai", "coqui"

    # Script Generator output 
    script: dict                    # {"scenes": [{"text": ..., "visual_hint": ...}]}

    # TTS output 
    audio_files: list[str]          # ["audio/scene_1.wav", ...]

    # Audio Duration output 
    audio_durations: list[float]    # [3.2, 4.1, 2.8]

    # Scene Planner output 
    scene_plans: list[dict]         # [{scene_id, animation_type, text, duration}]

    # Manim Renderer output 
    rendered_scenes: list[str]      # ["videos/scene_1.mp4", ...]

    # Final output 
    final_video: str                # "outputs/final_video.mp4"

    # Error tracking 
    error: Optional[str]
    failed_node: Optional[str]
