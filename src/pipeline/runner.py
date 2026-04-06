import json
from pathlib import Path
from typing import TypedDict, Optional, List, Annotated, Tuple
import operator

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from src.agent.progress import get_pipeline_log as _fmt
from src.agent.model_loader import (
    AUDIO_DIR, VIDEO_RESOLUTION, VIDEO_OUTPUT_NAME, MANIM_QUALITY, OUTPUTS_DIR,
)
from src.pipeline.utils import _strip_timestamps, _split_script_into_scenes, _get_audio_duration
from src.tts import _synthesise_tts
from src.pipeline.render import _render_manim_scene
from src.pipeline.stitching import _stitch

# ─── Reducers ───────────────────────────────────────────────────────────────

def _reduce_error(left: Optional[str], right: Optional[str]) -> Optional[str]:
    return left if left else right

def _reduce_bool(left: bool, right: bool) -> bool:
    return left or right

def _reduce_list_of_tuples(
    left: List[Tuple[int, str]], right: List[Tuple[int, str]]
) -> List[Tuple[int, str]]:
    # Merge two lists (LangGraph operator.add does this, but we explicitly type it)
    return left + right

# ─── Pipeline State ──────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    # Inputs
    manim_code: str
    script: str
    tts_provider: str

    # Accumulated logs
    logs: Annotated[List[str], operator.add]

    # Populated by split_script node
    scenes_raw: List[str]
    scenes_for_tts: List[str]

    # Populated by process_scene mapped nodes
    # We store (scene_id, path) so we can sort them correctly in stitching phase
    audio_files: Annotated[List[Tuple[int, str]], operator.add]
    rendered_scenes: Annotated[List[Tuple[int, str]], operator.add]

    # Final output
    final_video: Optional[str]
    
    # Error management with reducers
    error: Annotated[Optional[str], _reduce_error]
    failed_node: Annotated[Optional[str], _reduce_error]
    aborted: Annotated[bool, _reduce_bool]


class SceneState(TypedDict):
    scene_idx: int
    raw_text: str
    tts_text: str
    tts_provider: str
    manim_code: str


# ─── Node 1: Split Script ────────────────────────────────────────────────────

def _node_split_script(state: PipelineState) -> dict:
    logs: List[str] = []

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🚀  Pipeline started (Parallel Mode)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logs.append(json.dumps({"log": _fmt("INIT", "STARTING PARALLEL PIPELINE...")}))

    scenes_raw = _split_script_into_scenes(state["script"])
    print(f"🔍  Detected {len(scenes_raw)} scenes in the script")
    logs.append(json.dumps({"log": _fmt("DETECTION", f"MISSION SEGMENTED INTO {len(scenes_raw)} SCENES")}))

    scenes_for_tts = [_strip_timestamps(s) for s in scenes_raw]

    return {
        "logs": logs,
        "scenes_raw": scenes_raw,
        "scenes_for_tts": scenes_for_tts,
    }


# ─── Router: Map to Scenes ───────────────────────────────────────────────────

def _map_scenes(state: PipelineState):
    """Router that returns a Send object for each scene to run them in parallel."""
    if state.get("aborted"):
        return ["stitch"]
    
    sends = []
    for idx, (raw_text, tts_text) in enumerate(zip(state["scenes_raw"], state["scenes_for_tts"]), start=1):
        sends.append(Send("process_scene", {
            "scene_idx": idx,
            "raw_text": raw_text,
            "tts_text": tts_text,
            "tts_provider": state["tts_provider"],
            "manim_code": state["manim_code"],
        }))
    return sends


# ─── Node 2: Process Scene (TTS & Render in parallel) ─────────────────────────

def _node_process_scene(state: SceneState) -> dict:
    logs: List[str] = []
    idx = state["scene_idx"]
    tts_text = state["tts_text"]
    raw_text = state["raw_text"]
    tts_provider = state["tts_provider"]
    manim_code = state["manim_code"]

    # 1. TTS Synthesis
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = AUDIO_DIR / f"custom_scene_{idx}.wav"

    print(f"\n🎙️   Generating audio for scene {idx} ({len(tts_text)} chars)")
    logs.append(json.dumps({"log": _fmt("SYNTHESIS", f"TTS SIGNAL: SCENE {idx} ({len(tts_text)} CHARS)")}))
    
    try:
        _synthesise_tts(tts_text, out_path, tts_provider)
        print(f"   ✅ Audio done → {out_path.name}")
    except Exception as exc:
        print(f"   ❌ Audio generation failed for scene {idx}: {exc}")
        err_msg = str(exc)
        logs.append(json.dumps({
            "log": _fmt("ABORT", f"TTS FAILURE (SCENE {idx}): {err_msg}"),
            "error": err_msg,
            "failed_node": "custom_tts",
        }))
        return {
            "logs": logs,
            "error": err_msg,
            "failed_node": "custom_tts",
            "aborted": True,
        }

    # 2. Manim Rendering
    duration = _get_audio_duration(str(out_path))
    print(f"\n🎬  Rendering scene {idx} (duration: {duration:.2f}s)")
    logs.append(json.dumps({"log": _fmt("RENDER", f"MANIM SECTOR: {idx} [DURATION: {duration:.2f}S]")}))

    scene_data = {
        "scene_id": idx,
        "text": _strip_timestamps(raw_text),
        "duration": duration,
    }

    def _make_log_callback(scene_idx):
        def _cb(category, msg):
            icon = {"AGENT": "🤖", "COMPLETE": "✅", "FALLBACK": "⚠️", "FATAL": "❌"}.get(category.upper(), "  ")
            print(f"   {icon} [Scn {scene_idx}] [{category}] {msg}")
        return _cb

    width, height = map(int, VIDEO_RESOLUTION.split("x"))
    
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
            "error": err_msg,
            "failed_node": "custom_manim",
            "aborted": True,
        }

    print(f"   ✅ Scene {idx} rendered successfully")
    return {
        "logs": logs,
        "audio_files": [(idx, str(out_path))],
        "rendered_scenes": [(idx, rendered)],
    }


# ─── Node 4: Stitching ───────────────────────────────────────────────────────

def _node_stitch(state: PipelineState) -> dict:
    if state.get("aborted"):
        return {"logs": []}

    logs: List[str] = []
    
    # Sort files by scene index to maintain chronological order
    sorted_rendered = sorted(state.get("rendered_scenes", []), key=lambda x: x[0])
    rendered_scenes = [path for _, path in sorted_rendered]
    
    sorted_audio = sorted(state.get("audio_files", []), key=lambda x: x[0])
    audio_files = [path for _, path in sorted_audio]

    if not rendered_scenes or not audio_files:
        err_msg = "Critical error: Missing rendered scenes or audio files for stitching."
        logs.append(json.dumps({"error": err_msg, "failed_node": "custom_stitch"}))
        return {"logs": logs, "error": err_msg, "failed_node": "custom_stitch", "aborted": True}

    print(f"\n🔗  Stitching {len(rendered_scenes)} scenes together...")
    logs.append(json.dumps({"log": _fmt("ASSEMBLY", "STITCHING MISSION CLIPS...")}))

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(OUTPUTS_DIR / f"custom_{VIDEO_OUTPUT_NAME}")

    success = _stitch(rendered_scenes, audio_files, output_path)

    if not success:
        # MoviePy fallback
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
    workflow.add_node("process_scene", _node_process_scene)
    workflow.add_node("stitch", _node_stitch)

    workflow.set_entry_point("split_script")
    workflow.add_conditional_edges("split_script", _map_scenes, ["process_scene", "stitch"])
    
    workflow.add_edge("process_scene", "stitch")
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

    for event in _pipeline_graph.stream(initial_state):
        for _node_name, state_delta in event.items():
            for log_chunk in state_delta.get("logs", []):
                yield log_chunk

            if state_delta.get("aborted"):
                return
