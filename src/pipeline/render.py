import os
import re
import subprocess
import json
from pathlib import Path
from src.agent.model_loader import (
    MANIM_SCENES_DIR, VIDEOS_DIR, VIDEO_FPS, call_llm,
)
from src.pipeline.utils import _get_quality_flag

# ─── constants ──────────────────────────────────────────────────────────────
MAX_FIX_RETRIES = 3

MANIM_IMPORTS = """\
from manim import *
import json
import os
import textwrap

# Set resolution and FPS
config.pixel_width = {width}
config.pixel_height = {height}
config.frame_rate = {fps}
"""

MANIM_FIX_SYSTEM_PROMPT = """You are an expert Manim Community Edition debugger.
You will receive:
1. The FULL Manim Python code that FAILED to render.
2. The EXACT error traceback from the Manim renderer.

Your job:
- Analyse the error carefully.
- Fix ONLY the broken part of the code. Do NOT rewrite unrelated sections.
- Return ONLY the COMPLETE fixed Python code — no explanation, no markdown fences, no comments about what you changed.
- The code must be valid Python that Manim can render.
- Preserve the class name exactly as-is (e.g. RenderScene).
- Do NOT add `from manim import *` or config lines — those are injected separately.

Common fixes:
- `interpolate_color` needs ManimColor objects, not strings → wrap with ManimColor()
- MathTex indexing errors → use len() checks or try/except
- Wrong number of arguments → check Manim docs signatures
- Missing imports → add any missing stdlib/manim imports
- Polygon/3D points → ensure 3D tuples [x, y, z]
"""

def _ask_llm_to_fix_manim(broken_code: str, error_text: str) -> str:
    """Send broken code to LLM for auto-fix."""
    user_prompt = f"""## BROKEN MANIM CODE:
```python
{broken_code}
```

## ERROR TRACEBACK:
```
{error_text}
```

Return ONLY the fixed Python code. No markdown fences, no explanation."""

    fixed_code = call_llm(MANIM_FIX_SYSTEM_PROMPT, user_prompt)
    fixed_code = fixed_code.strip()
    if fixed_code.startswith("```"):
        lines = fixed_code.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        fixed_code = "\n".join(lines)
    return fixed_code.strip()

def _generate_fallback_scene(scene_id: int, text: str, duration: float) -> str:
    """Minimal safe scene as last resort."""
    safe_text = text.replace('"', '\\"').replace("'", "\\'")
    if len(safe_text) > 200:
        safe_text = safe_text[:197] + "..."
    return f'''
class RenderScene(Scene):
    def construct(self):
        self.camera.background_color = "#0A0A14"
        text = Text(
            """{safe_text}""",
            font_size=28,
            color=WHITE,
            line_spacing=1.4,
        ).scale_to_fit_width(config.pixel_width * 0.006)
        text.move_to(ORIGIN)
        self.play(FadeIn(text), run_time=1.0)
        self.wait({max(duration - 2, 1)})
        self.play(FadeOut(text), run_time=0.5)
'''

def _render_manim_scene(
    scene_id: int,
    manim_code: str,
    scene_data: dict,
    width: int,
    height: int,
    quality: str,
    log_callback=None,
) -> str | None:
    """Agentic Manim renderer with self-healing."""
    MANIM_SCENES_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    def _log(category, msg):
        if log_callback:
            log_callback(category, msg)
        print(f"[pipeline.render] [{category}] {msg}")

    def _clean_code(code: str) -> str:
        _strip_prefixes = (
            "from manim import", "import manim",
            "config.pixel_width", "config.pixel_height",
            "config.frame_width", "config.frame_height", "config.frame_rate",
        )
        cleaned_lines = []
        for line in code.splitlines():
            if any(line.strip().startswith(p) for p in _strip_prefixes):
                continue
            cleaned_lines.append(line)
        return "\n".join(cleaned_lines)

    def _ensure_class_name(code: str) -> str:
        return re.sub(r"\bclass\s+\w+\s*\(\s*Scene\s*\)\s*:", "class RenderScene(Scene):", code, count=1)

    def _try_render(code: str, attempt: int) -> tuple[str | None, str]:
        cleaned = _ensure_class_name(_clean_code(code))
        script_code = MANIM_IMPORTS.format(width=width, height=height, fps=VIDEO_FPS)
        script_code += "\n" + cleaned
        script_path = MANIM_SCENES_DIR / f"custom_scene_{scene_id}.py"
        script_path.write_text(script_code, encoding="utf-8")

        quality_flag = _get_quality_flag(quality)
        output_name = f"custom_scene_{scene_id}_render.mp4"

        cmd = [
            "manim", "render", str(script_path), "RenderScene",
            quality_flag, "-o", output_name,
            "--media_dir", str(MANIM_SCENES_DIR / "media"),
        ]
        env = os.environ.copy()
        env["SCENE_DATA"] = json.dumps(scene_data)

        _log("RENDER", f"Attempt {attempt} for scene {scene_id}")
        try:
            subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            video_files = list((MANIM_SCENES_DIR / "media" / "videos").rglob(output_name))
            if not video_files:
                return None, f"Manim completed but '{output_name}' not found."
            
            final_path = VIDEOS_DIR / f"custom_scene_{scene_id}.mp4"
            if final_path.exists():
                final_path.unlink()
            video_files[0].replace(final_path)
            _log("RENDER", f"Scene {scene_id} rendered OK.")
            return str(final_path), ""
        except subprocess.CalledProcessError as exc:
            return None, (exc.stderr or "") + "\n" + (exc.stdout or "")
        except Exception as exc:
            return None, str(exc)

    current_code = manim_code
    for attempt in range(1, MAX_FIX_RETRIES + 2):
        result, error = _try_render(current_code, attempt)
        if result: return result

        _log("ERROR", f"Scene {scene_id} attempt {attempt} failed.")
        if attempt <= MAX_FIX_RETRIES:
            _log("AGENT", "🤖 Auto-fixing...")
            try:
                fixed_code = _ask_llm_to_fix_manim(current_code, error)
                if fixed_code and fixed_code.strip() != current_code.strip():
                    current_code = fixed_code
            except Exception as fix_exc:
                _log("AGENT", f"⚠️ Fix failed: {fix_exc}")

    _log("FALLBACK", "Generating fallback scene...")
    fallback = _generate_fallback_scene(scene_id, scene_data.get("text", ""), scene_data.get("duration", 5.0))
    result, _ = _try_render(fallback, 0)
    return result
