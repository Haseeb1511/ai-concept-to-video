"""
src/voiceover_pipeline/runner.py
─────────────────────────────────────────────────────────────────────────────
Renders a single-file Manim VoiceoverScene script at the chosen resolution.

The script the user pastes MUST inherit from VoiceoverScene and call
set_speech_service() itself.  This runner:
  1. Writes the script to a temp file
  2. Patches in the correct pixel dimensions & quality via config overrides
     injected at the top of the file
  3. Calls `manim` in a subprocess and streams stdout/stderr line-by-line
  4. Returns the path of the rendered MP4

Resolution presets match the existing pipeline in src/pipeline/runner.py.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Generator, Optional

from src.agent.model_loader import BASE_DIR, FINAL_VIDEOS_DIR

# ── Resolution presets ────────────────────────────────────────────────────────
RESOLUTION_PRESETS: dict[str, dict] = {
    "480p  (854x480)":    {"width": 854,  "height": 480,  "quality": "low_quality",        "fps": 15},
    "720p  (1280x720)":   {"width": 1280, "height": 720,  "quality": "medium_quality",     "fps": 30},
    "1080p (1920x1080)":  {"width": 1920, "height": 1080, "quality": "high_quality",       "fps": 60},
    "4K    (3840x2160)":  {"width": 3840, "height": 2160, "quality": "production_quality", "fps": 60},
    "Shorts (1080x1920)": {"width": 1080, "height": 1920, "quality": "high_quality",       "fps": 60},
}

# ── OpenAI voice models available in manim-voiceover ─────────────────────────
OPENAI_VOICES: list[str] = [
    "alloy", "echo", "fable", "onyx", "nova", "shimmer",
]

# ── Quality flag map (manim CLI -q flag) ──────────────────────────────────────
_QUALITY_FLAG: dict[str, str] = {
    "low_quality":        "-ql",
    "medium_quality":     "-qm",
    "high_quality":       "-qh",
    "production_quality": "-qp",
}

# ── Config injection prepended to the user script ────────────────────────────
_CONFIG_PATCH = textwrap.dedent("""\
    from manim import config as _cfg
    _cfg.pixel_width  = {width}
    _cfg.pixel_height = {height}
    _cfg.frame_rate   = {fps}
    _cfg.frame_height = {frame_height:.5f}
    _cfg.frame_width  = _cfg.frame_height * ({width} / {height})
""")

def _compute_frame_height(width: int, height: int) -> float:
    """Keep Manim's default 8-unit wide frame scaled to the pixel ratio."""
    # Standard Manim frame is 8 units wide × 4.5 units tall (16:9).
    # For arbitrary aspect ratios we anchor frame_width = 8.
    base_frame_width = 8.0
    return base_frame_width * height / width


def _detect_scene_class(code: str) -> Optional[str]:
    """Return the first VoiceoverScene subclass name found in the script."""
    # Match:  class Foo(VoiceoverScene):
    m = re.search(r"class\s+(\w+)\s*\(\s*VoiceoverScene\s*\)", code)
    if m:
        return m.group(1)
    # Fallback: class Foo(Scene)
    m = re.search(r"class\s+(\w+)\s*\(\s*Scene\s*\)", code)
    return m.group(1) if m else None


def run_voiceover_pipeline(
    manim_code: str,
    resolution_label: str,
    openai_voice: str,
) -> Generator[str, None, None]:
    """
    Yields log strings (prefixed with 📋 / ✅ / ❌).
    The last yielded string whose prefix is '✅ OUTPUT:' contains the video path.
    """

    # ── 1. Resolve resolution preset ─────────────────────────────────────────
    preset = RESOLUTION_PRESETS.get(resolution_label)
    if preset is None:
        yield f"❌ Unknown resolution: {resolution_label}"
        return

    width, height, quality, fps = (
        preset["width"], preset["height"], preset["quality"], preset["fps"]
    )
    frame_height = _compute_frame_height(width, height)

    yield f"📋 Resolution  : {resolution_label}  →  {width}×{height} @ {fps}fps"
    yield f"📋 Voice model : {openai_voice}"
    yield f"📋 Manim quality flag: {_QUALITY_FLAG[quality]}"

    # ── 2. Detect scene class ─────────────────────────────────────────────────
    scene_class = _detect_scene_class(manim_code)
    if not scene_class:
        yield "❌ Could not detect a VoiceoverScene (or Scene) subclass in the code."
        return
    yield f"📋 Scene class  : {scene_class}"

    # ── 3. Patch the user code ────────────────────────────────────────────────
    # Inject config overrides + voice override right after the imports
    # We replace any OpenAI voice= argument with the chosen one
    patched_code = _CONFIG_PATCH.format(
        width=width, height=height, fps=fps, frame_height=frame_height
    )

    # Replace voice= in OpenAIService(...) calls if present
    user_code = re.sub(
        r'(OpenAIService\s*\([^)]*voice\s*=\s*)["\'][\w]+["\']',
        rf'\g<1>"{openai_voice}"',
        manim_code,
    )
    patched_code += user_code

    # ── 4. Write to a temp file ───────────────────────────────────────────────
    tmp_dir  = BASE_DIR / "manim_animation_result" / "voiceover_temp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_file = tmp_dir / "voiceover_scene.py"
    tmp_file.write_text(patched_code, encoding="utf-8")

    yield f"📋 Temp script  : {tmp_file}"

    # ── 5. Build manim command ────────────────────────────────────────────────
    output_dir = FINAL_VIDEOS_DIR / "voiceover"
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, "-m", "manim",
        _QUALITY_FLAG[quality],
        "--media_dir", str(output_dir),
        str(tmp_file),
        scene_class,
    ]

    yield f"📋 Running: {' '.join(cmd)}"

    # ── 6. Stream subprocess output ───────────────────────────────────────────
    env = os.environ.copy()
    env["OPENAI_VOICE"] = openai_voice  # extra env var for scripts that read it

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(BASE_DIR),
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                yield f"📋 {line}"

        proc.wait()
    except Exception as exc:
        yield f"❌ Subprocess error: {exc}"
        return

    if proc.returncode != 0:
        yield f"❌ Manim exited with code {proc.returncode}"
        return

    # ── 7. Locate the output MP4 ──────────────────────────────────────────────
    # Manim places the file in:
    #   <media_dir>/videos/<script_stem>/<quality_dir>/<SceneName>.mp4
    quality_dir_map = {
        "low_quality":        f"{height}p{fps}",
        "medium_quality":     f"{height}p{fps}",
        "high_quality":       f"{height}p{fps}",
        "production_quality": f"{height}p{fps}",
    }
    quality_dir = quality_dir_map[quality]
    expected_mp4 = (
        output_dir
        / "videos"
        / "voiceover_scene"
        / quality_dir
        / f"{scene_class}.mp4"
    )

    if expected_mp4.exists():
        yield f"✅ OUTPUT:{expected_mp4}"
        return

    # Fallback: search recursively
    found = list(output_dir.rglob(f"{scene_class}.mp4"))
    if found:
        yield f"✅ OUTPUT:{found[-1]}"
    else:
        yield "❌ Render succeeded but could not locate the output MP4."
