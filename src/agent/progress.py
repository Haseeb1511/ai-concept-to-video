import json
import datetime


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S")


# ── Structured event builders ──────────────────────────────────────────────
# Each function returns a JSON string ready to yield from the pipeline.

def evt_pipeline_start(n_scenes: int) -> str:
    return json.dumps({"type": "pipeline_start", "n_scenes": n_scenes, "ts": _ts()})

def evt_scene_start(scene_idx: int) -> str:
    return json.dumps({"type": "scene_start", "scene": scene_idx, "ts": _ts()})

def evt_scene_audio_done(scene_idx: int) -> str:
    return json.dumps({"type": "scene_audio_done", "scene": scene_idx, "ts": _ts()})

def evt_scene_render_start(scene_idx: int) -> str:
    return json.dumps({"type": "scene_render_start", "scene": scene_idx, "ts": _ts()})

def evt_scene_render_done(scene_idx: int) -> str:
    return json.dumps({"type": "scene_render_done", "scene": scene_idx, "ts": _ts()})

def evt_scene_error(scene_idx: int, stage: str, msg: str) -> str:
    return json.dumps({"type": "scene_error", "scene": scene_idx, "stage": stage, "msg": msg, "ts": _ts()})

def evt_stitch_start(n_scenes: int) -> str:
    return json.dumps({"type": "stitch_start", "n_scenes": n_scenes, "ts": _ts()})

def evt_stitch_fallback() -> str:
    return json.dumps({"type": "stitch_fallback", "ts": _ts()})

def evt_done(output_path: str) -> str:
    return json.dumps({"type": "done", "path": output_path, "ts": _ts()})

def evt_error(msg: str, node: str = "") -> str:
    return json.dumps({"type": "error", "msg": msg, "node": node, "ts": _ts()})


# ── Legacy helpers kept for any external callers ───────────────────────────

def get_pipeline_log(category: str, message: str) -> str:
    """Kept for backward compatibility – not used by the refactored pipeline."""
    now = _ts()
    return f"[{now}] [{category}] {message}"

def get_military_log(category: str, message: str) -> str:
    return get_pipeline_log(category, message)
