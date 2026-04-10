import json
from pathlib import Path
from typing import TypedDict, Optional, List, Annotated, Tuple
import operator

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from src.agent.progress import (
    evt_pipeline_start, evt_scene_start,
    evt_scene_audio_done, evt_scene_render_done, evt_scene_error,
    evt_stitch_start, evt_stitch_fallback, evt_done, evt_error,
    evt_scene_render_start,
)
from src.agent.model_loader import (
    AUDIO_DIR, VIDEO_RESOLUTION, VIDEO_OUTPUT_NAME, MANIM_QUALITY, FINAL_VIDEOS_DIR,
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
    return left + right

# ─── Pipeline State ──────────────────────────────────────────────────────────

class PipelineState(TypedDict):
    manim_code: str
    script: str
    tts_provider: str

    # Accumulated event JSON strings
    logs: Annotated[List[str], operator.add]

    scenes_raw: List[str]
    scenes_for_tts: List[str]

    audio_files: Annotated[List[Tuple[int, str]], operator.add]
    rendered_scenes: Annotated[List[Tuple[int, str]], operator.add]

    final_video: Optional[str]

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
    scenes_raw = _split_script_into_scenes(state["script"])
    n = len(scenes_raw)

    print(f"\n{'━'*40}")
    print(f"🚀  Pipeline started  —  {n} scene{'s' if n != 1 else ''} detected")
    print(f"{'━'*40}")

    scenes_for_tts = [_strip_timestamps(s) for s in scenes_raw]

    return {
        "logs": [evt_pipeline_start(n)],
        "scenes_raw": scenes_raw,
        "scenes_for_tts": scenes_for_tts,
    }


# ─── Router: Map to Scenes ───────────────────────────────────────────────────

def _map_scenes(state: PipelineState):
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


# ─── Node 2: Process Scene (TTS & Render) ────────────────────────────────────

def _node_process_scene(state: SceneState) -> dict:
    logs: List[str] = []
    idx = state["scene_idx"]
    tts_text = state["tts_text"]
    raw_text = state["raw_text"]
    tts_provider = state["tts_provider"]
    manim_code = state["manim_code"]

    logs.append(evt_scene_start(idx))
    print(f"  ▶  Scene {idx}  — starting audio")

    # 1. TTS Synthesis ──────────────────────────────────────────────────────
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out_path = AUDIO_DIR / f"custom_scene_{idx}.wav"

    try:
        _synthesise_tts(tts_text, out_path, tts_provider)
        logs.append(evt_scene_audio_done(idx))
        print(f"  ✅  Scene {idx}  — audio done")
    except Exception as exc:
        err_msg = str(exc)
        print(f"  ❌  Scene {idx}  — audio FAILED: {err_msg}")
        logs.append(evt_scene_error(idx, "audio", err_msg))
        return {
            "logs": logs,
            "error": err_msg,
            "failed_node": "custom_tts",
            "aborted": True,
        }

    # 2. Manim Rendering ────────────────────────────────────────────────────
    duration = _get_audio_duration(str(out_path))
    logs.append(evt_scene_render_start(idx))
    print(f"  ▶  Scene {idx}  — starting render ({duration:.1f}s)")

    scene_data = {
        "scene_id": idx,
        "text": _strip_timestamps(raw_text),
        "duration": duration,
    }

    def _make_log_callback(scene_idx):
        def _cb(category, msg):
            # Suppress verbose agent sub-logs from terminal; they aren't useful
            if category.upper() not in ("AGENT",):
                print(f"        [{category}] Scene {scene_idx}: {msg}")
        return _cb

    width, height = map(int, VIDEO_RESOLUTION.split("x"))

    rendered = _render_manim_scene(
        idx, manim_code, scene_data, width, height, MANIM_QUALITY,
        log_callback=_make_log_callback(idx)
    )

    if not rendered:
        err_msg = f"Manim rendering failed on scene {idx}"
        print(f"  ❌  Scene {idx}  — render FAILED")
        logs.append(evt_scene_error(idx, "render", err_msg))
        return {
            "logs": logs,
            "error": err_msg,
            "failed_node": "custom_manim",
            "aborted": True,
        }

    logs.append(evt_scene_render_done(idx))
    print(f"  ✅  Scene {idx}  — render done")

    return {
        "logs": logs,
        "audio_files": [(idx, str(out_path))],
        "rendered_scenes": [(idx, rendered)],
    }


# ─── Node 3: Stitching ───────────────────────────────────────────────────────

def _node_stitch(state: PipelineState) -> dict:
    if state.get("aborted"):
        return {"logs": []}

    logs: List[str] = []

    sorted_rendered = sorted(state.get("rendered_scenes", []), key=lambda x: x[0])
    rendered_scenes = [path for _, path in sorted_rendered]

    sorted_audio = sorted(state.get("audio_files", []), key=lambda x: x[0])
    audio_files = [path for _, path in sorted_audio]

    if not rendered_scenes or not audio_files:
        err_msg = "Critical error: Missing rendered scenes or audio files for stitching."
        logs.append(evt_error(err_msg, "custom_stitch"))
        return {"logs": logs, "error": err_msg, "failed_node": "custom_stitch", "aborted": True}

    n = len(rendered_scenes)
    print(f"\n  🔗  Stitching {n} scene{'s' if n != 1 else ''} together…")
    logs.append(evt_stitch_start(n))

    FINAL_VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(FINAL_VIDEOS_DIR / f"custom_{VIDEO_OUTPUT_NAME}")

    success = _stitch(rendered_scenes, audio_files, output_path)

    if not success:
        print("     ⚠️  FFmpeg failed — trying MoviePy fallback…")
        logs.append(evt_stitch_fallback())
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
            print("     ✅  MoviePy fallback succeeded")
        except Exception as exc:
            print(f"     ❌  MoviePy also failed: {exc}")
            logs.append(evt_error(f"Stitching failed: {exc}", "custom_stitch"))

    if not success:
        err_msg = "All stitching methods failed."
        logs.append(evt_error(err_msg, "custom_stitch"))
        return {"logs": logs, "error": err_msg, "failed_node": "custom_stitch", "aborted": True}

    print(f"\n{'━'*40}")
    print(f"✅  Video ready  →  {output_path}")
    print(f"{'━'*40}\n")

    logs.append(evt_done(output_path))
    # Also signal the final_video for the FastAPI layer
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
    Yields structured JSON event strings consumed by the Streamlit frontend.
    Event types: pipeline_start, scene_start, scene_audio_done, scene_render_done,
                 scene_error, stitch_start, stitch_fallback, done, error, final_video.
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

            # Forward pipeline-level errors
            if state_delta.get("error") and state_delta.get("aborted"):
                yield evt_error(
                    state_delta["error"],
                    state_delta.get("failed_node", ""),
                )
                return
