"""
Outer video generation pipeline as a LangGraph StateGraph.

Graph topology:
    split_script → tts → render_scenes → stitch → END

The compiled graph is exposed as `_pipeline_graph` so that
backend/main.py can call get_graph().draw_mermaid_png() at startup.

run_custom_pipeline() remains a synchronous generator that yields the
same JSON log strings as before (for FastAPI StreamingResponse).
"""

import json
from pathlib import Path
from typing import TypedDict, Optional, List, Annotated
import operator

from langgraph.graph import StateGraph, END

from src.agent.progress import get_pipeline_log as _fmt
from src.agent.model_loader import (
    AUDIO_DIR, VIDEO_RESOLUTION, VIDEO_OUTPUT_NAME, MANIM_QUALITY, OUTPUTS_DIR,
)
from src.pipeline.utils import _strip_timestamps, _split_script_into_scenes, _get_audio_duration
from src.tts import _synthesise_tts
from src.pipeline.render import _render_manim_scene
from src.pipeline.stitching import _stitch


# ─── Pipeline State ──────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    # Inputs (set before graph is invoked)
    manim_code: str
    script: str
    tts_provider: str

    # Accumulated log messages — each node appends to this list
    logs: Annotated[List[str], operator.add]

    # Populated by split_script node
    scenes_raw: List[str]
    scenes_for_tts: List[str]

    # Populated by tts node
    audio_files: List[str]

    # Populated by render_scenes node
    rendered_scenes: List[str]

    # Final output
    final_video: Optional[str]
    error: Optional[str]
    failed_node: Optional[str]

    # Control flag — if True, subsequent nodes skip execution gracefully
    aborted: bool


# ─── Node 1: Split Script ────────────────────────────────────────────────────

def _node_split_script(state: PipelineState) -> dict:
    logs: List[str] = []

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀  Pipeline started")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logs.append(json.dumps({"log": _fmt("INIT", "STARTING MODULAR PIPELINE...")}))

    scenes_raw = _split_script_into_scenes(state["script"])
    print(f"🔍  Detected {len(scenes_raw)} scenes in the script")
    logs.append(json.dumps({"log": _fmt("DETECTION", f"MISSION SEGMENTED INTO {len(scenes_raw)} SCENES")}))

    scenes_for_tts = [_strip_timestamps(s) for s in scenes_raw]

    return {
        "logs": logs,
        "scenes_raw": scenes_raw,
        "scenes_for_tts": scenes_for_tts,
    }


# ─── Node 2: TTS Synthesis ───────────────────────────────────────────────────

def _node_tts(state: PipelineState) -> dict:
    # Skip if already aborted by a previous node
    if state.get("aborted"):
        return {"logs": []}

    logs: List[str] = []
    scenes_for_tts = state["scenes_for_tts"]
    tts_provider = state["tts_provider"]
    audio_files: List[str] = []

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    for idx, tts_text in enumerate(scenes_for_tts, start=1):
        print(f"🎙️   Generating audio for scene {idx}/{len(scenes_for_tts)} ({len(tts_text)} chars)")
        logs.append(json.dumps({"log": _fmt("SYNTHESIS", f"TTS SIGNAL: SCENE {idx} ({len(tts_text)} CHARS)")}))
        out_path = AUDIO_DIR / f"custom_scene_{idx}.wav"
        try:
            _synthesise_tts(tts_text, out_path, tts_provider)
            print(f"   ✅ Audio done → {out_path.name}")
            audio_files.append(str(out_path))
        except Exception as exc:
            print(f"   ❌ Audio generation failed for scene {idx}: {exc}")
            err_msg = str(exc)
            logs.append(json.dumps({
                "log": _fmt("ABORT", f"TTS FAILURE: {err_msg}"),
                "error": err_msg,
                "failed_node": "custom_tts",
            }))
            return {
                "logs": logs,
                "audio_files": audio_files,
                "error": err_msg,
                "failed_node": "custom_tts",
                "aborted": True,
            }

    return {
        "logs": logs,
        "audio_files": audio_files,
    }


# ─── Node 3: Manim Rendering ─────────────────────────────────────────────────

def _node_render_scenes(state: PipelineState) -> dict:
    if state.get("aborted"):
        return {"logs": []}

    logs: List[str] = []
    scenes_raw = state["scenes_raw"]
    audio_files = state["audio_files"]
    manim_code = state["manim_code"]
    width, height = map(int, VIDEO_RESOLUTION.split("x"))
    rendered_scenes: List[str] = []

    for idx, (raw_text, audio_path) in enumerate(zip(scenes_raw, audio_files), start=1):
        duration = _get_audio_duration(audio_path)
        print(f"\n🎬  Rendering scene {idx}/{len(scenes_raw)} (duration: {duration:.2f}s)")
        logs.append(json.dumps({"log": _fmt("RENDER", f"MANIM SECTOR: {idx} [DURATION: {duration:.2f}S]")}))

        scene_data = {
            "scene_id": idx,
            "text": _strip_timestamps(raw_text),
            "duration": duration,
        }

        def _make_log_callback(scene_idx):
            def _cb(category, msg):
                icon = {"AGENT": "🤖", "COMPLETE": "✅", "FALLBACK": "⚠️", "FATAL": "❌"}.get(category.upper(), "  ")
                print(f"   {icon} [{category}] {msg}")
            return _cb

        rendered = _render_manim_scene(
            idx, manim_code, scene_data, width, height, MANIM_QUALITY,
            log_callback=_make_log_callback(idx)
        )

        if not rendered:
            print(f"   ❌ Scene {idx} could not be rendered after all attempts")
            err_msg = f"Manim rendering failed on scene {idx}"
            logs.append(json.dumps({
                "log": _fmt("CRITICAL", f"RENDER FAILED: SECTOR {idx}"),
                "error": err_msg,
                "failed_node": "custom_manim",
            }))
            return {
                "logs": logs,
                "rendered_scenes": rendered_scenes,
                "error": err_msg,
                "failed_node": "custom_manim",
                "aborted": True,
            }

        print(f"   ✅ Scene {idx} rendered successfully")
        rendered_scenes.append(rendered)

    return {
        "logs": logs,
        "rendered_scenes": rendered_scenes,
    }


# ─── Node 4: Stitching ───────────────────────────────────────────────────────

def _node_stitch(state: PipelineState) -> dict:
    if state.get("aborted"):
        return {"logs": []}

    logs: List[str] = []
    rendered_scenes = state["rendered_scenes"]
    audio_files = state["audio_files"]

    print(f"\n🔗  Stitching {len(rendered_scenes)} scenes together...")
    logs.append(json.dumps({"log": _fmt("ASSEMBLY", "STITCHING MISSION CLIPS...")}))

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(OUTPUTS_DIR / f"custom_{VIDEO_OUTPUT_NAME}")

    success = _stitch(rendered_scenes, audio_files, output_path)

    if not success:
        # MoviePy fallback (legacy support)
        print("   ⚠️  FFmpeg failed, trying MoviePy fallback...")
        logs.append(json.dumps({"log": _fmt("RETRY", "FFMPEG FAILED. ATTEMPTING MOVIEPY FALLBACK...")}))
        try:
            from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
            clips = []
            for vf, af in zip(rendered_scenes, audio_files):
                vid = VideoFileClip(vf).set_audio(AudioFileClip(af))
                clips.append(vid)
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(
                output_path, fps=30, codec="libx264",
                audio_codec="aac", preset="ultrafast", logger=None
            )
            success = True
            print("   ✅ MoviePy stitch succeeded")
        except Exception as exc:
            print(f"   ❌ MoviePy stitch also failed: {exc}")
            logs.append(json.dumps({"log": _fmt("ABORT", f"STITCHING FAILED: {exc}")}))

    if not success:
        err_msg = "All stitching methods failed."
        logs.append(json.dumps({"error": err_msg, "failed_node": "custom_stitch"}))
        return {
            "logs": logs,
            "error": err_msg,
            "failed_node": "custom_stitch",
            "aborted": True,
        }

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅  Video ready → {output_path}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    logs.append(json.dumps({"log": _fmt("COMPLETE", f"FINAL VIDEO ARCHIVED: {output_path}")}))
    logs.append(json.dumps({"final_video": output_path}))

    return {
        "logs": logs,
        "final_video": output_path,
    }


# ─── Build & compile graph (module-level singleton) ───────────────────────────

def _build_pipeline_graph():
    workflow = StateGraph(PipelineState)

    workflow.add_node("split_script", _node_split_script)
    workflow.add_node("tts", _node_tts)
    workflow.add_node("render_scenes", _node_render_scenes)
    workflow.add_node("stitch", _node_stitch)

    workflow.set_entry_point("split_script")
    workflow.add_edge("split_script", "tts")
    workflow.add_edge("tts", "render_scenes")
    workflow.add_edge("render_scenes", "stitch")
    workflow.add_edge("stitch", END)

    return workflow.compile()


# Exposed for backend/main.py → get_graph().draw_mermaid_png()
_pipeline_graph = _build_pipeline_graph()


# ─── Public generator (unchanged interface for FastAPI) ───────────────────────

def run_custom_pipeline(
    manim_code: str,
    script: str,
    tts_provider: str = "gtts",
):
    """
    Modularized video generation pipeline backed by a LangGraph StateGraph.
    Yields log strings (same format as before), finally yields a JSON with
    'final_video' or 'error'.
    """
    initial_state: PipelineState = {
        "manim_code": manim_code,
        "script": script,
        "tts_provider": tts_provider,
        "logs": [],
        "scenes_raw": [],
        "scenes_for_tts": [],
        "audio_files": [],
        "rendered_scenes": [],
        "final_video": None,
        "error": None,
        "failed_node": None,
        "aborted": False,
    }

    # stream() yields {node_name: state_delta} dicts after each node completes
    for event in _pipeline_graph.stream(initial_state):
        for _node_name, state_delta in event.items():
            # Re-emit every log chunk collected by this node
            for log_chunk in state_delta.get("logs", []):
                yield log_chunk

            # If this node signalled an abort, stop streaming — the error
            # log was already emitted as part of its logs list above.
            if state_delta.get("aborted"):
                return
