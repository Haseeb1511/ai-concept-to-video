import os
import re
import ast
import subprocess
import json
import textwrap
from pathlib import Path
from src.agent.model_loader import (
    MANIM_SCENES_DIR, VIDEOS_DIR, VIDEO_FPS, call_llm,
)
from src.pipeline.utils import _get_quality_flag

# ─── constants ──────────────────────────────────────────────────────────────
MAX_FIX_RETRIES = 4   # increased from 3

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

# ─── error taxonomy ─────────────────────────────────────────────────────────
# Each entry: (label, hint sent to LLM)
_ERROR_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    (
        re.compile(r"interpolate_color", re.I),
        "COLOR_INTERP",
        "interpolate_color() requires ManimColor objects. Replace bare hex strings or color names with ManimColor('#RRGGBB') or ManimColor(WHITE).",
    ),
    (
        re.compile(r"IndexError|index out of range", re.I),
        "INDEX",
        "An index is out of range. Add bounds checks (len() guards or try/except) before accessing list/VGroup/MathTex sub-elements.",
    ),
    (
        re.compile(r"TypeError.*argument", re.I),
        "TYPE_ARG",
        "A function received wrong argument types or count. Check the Manim CE API signatures; do NOT pass keyword arguments positionally.",
    ),
    (
        re.compile(r"AttributeError", re.I),
        "ATTR",
        "An object does not have the accessed attribute. Verify the Manim CE class name and method — it may have been renamed or removed in newer versions.",
    ),
    (
        re.compile(r"NameError", re.I),
        "NAME",
        "A name is not defined. Add the missing import, or fix a typo in a variable or class name.",
    ),
    (
        re.compile(r"SyntaxError|invalid syntax|unexpected indent", re.I),
        "SYNTAX",
        "Python syntax error. Fix indentation, missing colons, unmatched brackets, or invalid f-strings.",
    ),
    (
        re.compile(r"ValueError", re.I),
        "VALUE",
        "A function received a bad value. Common in Manim: Polygon/3D points must be 3-tuples [x,y,z], colors must be valid, durations must be positive.",
    ),
    (
        re.compile(r"ZeroDivisionError|division by zero", re.I),
        "ZERO_DIV",
        "Division by zero. Guard any division with a max() or conditional check.",
    ),
    (
        re.compile(r"FileNotFoundError|No such file", re.I),
        "FILE",
        "A file path is missing. Use only bundled Manim assets; do not reference external files.",
    ),
    (
        re.compile(r"could not broadcast|shape mismatch", re.I),
        "NUMPY",
        "NumPy shape mismatch. Ensure all vectors/arrays passed to Manim are shape (3,) for 3-D coordinates.",
    ),
    (
        re.compile(r"Latex.*error|pdflatex|xelatex|LaTeX", re.I),
        "LATEX",
        "LaTeX compilation failed. Switch MathTex/Tex to Text() for non-math content, or simplify the LaTeX expression. Avoid unusual LaTeX packages.",
    ),
    (
        re.compile(r"OpenGL|shader|GLFW|display|xcb", re.I),
        "DISPLAY",
        "OpenGL/display error. Ensure the render command uses --renderer=cairo (not OpenGL). Do NOT call any 3-D camera methods.",
    ),
]


def _categorize_error(error_text: str) -> tuple[str, str]:
    """Return (error_label, hint) for the most relevant pattern."""
    for pattern, label, hint in _ERROR_PATTERNS:
        if pattern.search(error_text):
            return label, hint
    return "UNKNOWN", "Carefully read the full traceback and fix the root cause."


def _extract_traceback_tail(error_text: str, lines: int = 30) -> str:
    """Keep only the most informative tail of the traceback."""
    tail = "\n".join(error_text.strip().splitlines()[-lines:])
    return tail


def _syntax_check(code: str) -> str | None:
    """Return a syntax error message, or None if code parses OK."""
    try:
        ast.parse(code)
        return None
    except SyntaxError as exc:
        return f"SyntaxError on line {exc.lineno}: {exc.msg}"


# ─── LLM system prompts ─────────────────────────────────────────────────────

_BASE_FIX_SYSTEM = """\
You are an expert Manim Community Edition (v0.18+) debugger and animator.

RULES — FOLLOW EXACTLY:
1. Return ONLY the complete fixed Python class body (everything after the imports).
   - Do NOT include `from manim import *`, config lines, or markdown fences.
   - Preserve the class name `RenderScene` exactly.
2. Fix ONLY what is broken. Preserve all working animation logic.
3. The code must pass `python -c "import ast; ast.parse(open('file').read())"`.

MANIM CE COMMON PITFALLS:
- `interpolate_color(c1, c2, t)` → c1/c2 must be ManimColor objects, not strings.
- All 3-D coordinate tuples must be length-3: `np.array([x, y, 0])`.
- MathTex sub-element indexing can fail on complex expressions — use try/except.
- `Text` does NOT accept a `t2c` kwarg if the substring is not present.
- `VGroup.arrange()` default direction is RIGHT; pass `DOWN` explicitly for vertical.
- `self.wait()` duration must be > 0.
- `Polygon(*points)` — each point is a length-3 array/tuple.
- Avoid `FadeToColor` on non-VMobject types.
- Use `Write` only on VMobjects; use `FadeIn` for Images/SVG.
- `Create` (not `ShowCreation`) is the correct animation in CE v0.18+.
- `rate_func=smooth` is valid; `rate_func=rush_into` etc. are also valid.
"""

_SIMPLIFY_SYSTEM = """\
You are an expert Manim Community Edition animator.

The previous fix attempts all FAILED. Your job now is to produce a SIMPLIFIED but
visually correct version of the scene that WILL render without errors.

RULES:
1. Return ONLY the Python class body — no imports, no config, no markdown.
2. Class name must be `RenderScene`.
3. Strip out any complex or risky animations and replace with simple FadeIn/FadeOut/Write.
4. Use only: Text, MathTex (simple), Rectangle, Circle, Arrow, Dot, VGroup, NumberPlane.
5. Ensure all animations play for the required duration (use self.wait() generously).
6. No LaTeX beyond basic math. No 3D. No external files. No OpenGL.
"""


def _ask_llm_to_fix_manim(
    broken_code: str,
    error_text: str,
    attempt: int,
    scene_description: str = "",
) -> str:
    """Send broken code + categorised error to LLM for auto-fix."""
    error_label, hint = _categorize_error(error_text)
    tail = _extract_traceback_tail(error_text)

    # On later attempts, switch to a "simplify" strategy
    if attempt >= 3:
        system = _SIMPLIFY_SYSTEM
        user_prompt = f"""\
SCENE DESCRIPTION (what the scene should show):
{scene_description or "A Manim animation scene."}

FAILED CODE:
```python
{broken_code}
```

LAST ERROR ({error_label}):
```
{tail}
```

Produce a simplified, guaranteed-to-render version that preserves the core message."""
    else:
        system = _BASE_FIX_SYSTEM
        user_prompt = f"""\
ERROR CATEGORY: {error_label}
TARGETED HINT: {hint}

FAILED CODE:
```python
{broken_code}
```

EXACT ERROR (last 30 lines):
```
{tail}
```

Return ONLY the fixed Python code (no imports, no config, no markdown fences).
Fix attempt #{attempt} — be precise and targeted."""

    fixed_code = call_llm(system, user_prompt)
    return _strip_markdown_fences(fixed_code)


def _strip_markdown_fences(code: str) -> str:
    code = code.strip()
    if code.startswith("```"):
        lines = code.splitlines()
        lines = lines[1:]  # drop opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)
    return code.strip()


# ─── fallback scene generator ───────────────────────────────────────────────

def _generate_fallback_scene(scene_id: int, text: str, duration: float) -> str:
    """
    Two-tier fallback:
    - Tries to render a reasonably styled card.
    - Guaranteed no LaTeX, no external assets, no 3-D.
    """
    # Wrap long text
    wrapped_lines = textwrap.wrap(text, width=46) if text else ["(scene unavailable)"]
    # Escape for Python string
    safe_lines = [line.replace("\\", "\\\\").replace('"', '\\"') for line in wrapped_lines[:8]]
    lines_code = "\n".join(
        f'        lines.append(Text("{ln}", font_size=28, color=WHITE))' for ln in safe_lines
    )
    wait_time = max(duration - 2.5, 0.5)
    return f'''
class RenderScene(Scene):
    def construct(self):
        self.camera.background_color = "#0A0A14"

        lines = VGroup()
        raw_lines = []
{lines_code}
        for ln in lines:
            raw_lines.append(ln)
        lines = VGroup(*raw_lines).arrange(DOWN, buff=0.35)
        lines.move_to(ORIGIN)
        lines.scale_to_fit_width(min(lines.width, config.frame_width * 0.85))

        bg = Rectangle(
            width=lines.width + 0.8,
            height=lines.height + 0.6,
            fill_color="#1A1A2E",
            fill_opacity=0.9,
            stroke_color="#3A3A5C",
            stroke_width=2,
        ).move_to(ORIGIN)

        self.play(FadeIn(bg), run_time=0.4)
        self.play(FadeIn(lines), run_time=0.8)
        self.wait({wait_time})
        self.play(FadeOut(VGroup(bg, lines)), run_time=0.5)
'''


def _generate_minimal_fallback_scene(scene_id: int, text: str, duration: float) -> str:
    """Last-resort: absolute minimum — just text, no VGroup tricks."""
    safe_text = text.replace('"', '\\"').replace("'", "\\'")[:180]
    wait_time = max(duration - 2.0, 0.5)
    return f'''
class RenderScene(Scene):
    def construct(self):
        self.camera.background_color = "#0A0A14"
        t = Text("{safe_text}", font_size=26, color=WHITE)
        t.move_to(ORIGIN)
        self.play(FadeIn(t), run_time=0.8)
        self.wait({wait_time})
        self.play(FadeOut(t), run_time=0.5)
'''


# ─── main renderer ───────────────────────────────────────────────────────────

def _render_manim_scene(
    scene_id: int,
    manim_code: str,
    scene_data: dict,
    width: int,
    height: int,
    quality: str,
    log_callback=None,
) -> str | None:
    """Agentic Manim renderer with self-healing and multi-tier fallback."""
    MANIM_SCENES_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    scene_text: str = scene_data.get("text", "")
    scene_duration: float = float(scene_data.get("duration", 5.0))

    def _log(category: str, msg: str) -> None:
        if log_callback:
            log_callback(category, msg)
        print(f"[pipeline.render] [{category}] {msg}")

    def _clean_code(code: str) -> str:
        _strip_prefixes = (
            "from manim import", "import manim",
            "config.pixel_width", "config.pixel_height",
            "config.frame_width", "config.frame_height", "config.frame_rate",
        )
        return "\n".join(
            line for line in code.splitlines()
            if not any(line.strip().startswith(p) for p in _strip_prefixes)
        )

    def _normalise_class_name(code: str) -> str:
        return re.sub(
            r"\bclass\s+\w+\s*\(\s*(?:Scene|MovingCameraScene|ZoomedScene)\s*\)\s*:",
            "class RenderScene(Scene):",
            code,
            count=1,
        )

    def _try_render(code: str, attempt: int) -> tuple[str | None, str]:
        # Pre-flight: Python syntax check
        syntax_err = _syntax_check(code)
        if syntax_err:
            _log("SYNTAX", f"Pre-flight failed: {syntax_err}")
            return None, syntax_err

        cleaned = _normalise_class_name(_clean_code(code))
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
            "--renderer=cairo",   # force Cairo — avoids OpenGL/display issues
            "--disable_caching",  # avoids stale partial-render cache problems
        ]
        env = os.environ.copy()
        env["SCENE_DATA"] = json.dumps(scene_data)

        _log("RENDER", f"Attempt {attempt} for scene {scene_id}")
        try:
            result = subprocess.run(
                cmd, env=env, capture_output=True, text=True,
                check=True, timeout=120,   # prevent hung renders
            )
            video_files = list((MANIM_SCENES_DIR / "media" / "videos").rglob(output_name))
            if not video_files:
                return None, f"Manim finished but '{output_name}' not found in media/videos/."

            final_path = VIDEOS_DIR / f"custom_scene_{scene_id}.mp4"
            if final_path.exists():
                final_path.unlink()
            video_files[0].replace(final_path)
            _log("RENDER", f"Scene {scene_id} rendered OK → {final_path}")
            return str(final_path), ""

        except subprocess.TimeoutExpired:
            return None, "Render timed out after 120 s."
        except subprocess.CalledProcessError as exc:
            combined = (exc.stderr or "") + "\n" + (exc.stdout or "")
            error_label, _ = _categorize_error(combined)
            _log("ERROR", f"Scene {scene_id} attempt {attempt} failed [{error_label}]")
            return None, combined
        except Exception as exc:
            return None, str(exc)

    # ── main fix loop ────────────────────────────────────────────────────────
    current_code = manim_code
    error_history: list[str] = []

    for attempt in range(1, MAX_FIX_RETRIES + 2):
        result, error = _try_render(current_code, attempt)
        if result:
            return result

        error_history.append(error)

        if attempt > MAX_FIX_RETRIES:
            break

        _log("AGENT", f"🤖 Auto-fixing (attempt {attempt}/{MAX_FIX_RETRIES})…")
        try:
            fixed_code = _ask_llm_to_fix_manim(
                broken_code=current_code,
                error_text=error,
                attempt=attempt,
                scene_description=scene_text,
            )
            if not fixed_code:
                _log("AGENT", "⚠️ LLM returned empty fix — skipping.")
                continue
            if fixed_code.strip() == current_code.strip():
                _log("AGENT", "⚠️ LLM returned identical code — skipping duplicate attempt.")
                continue
            # Quick syntax check before spending a render attempt
            pre = _syntax_check(fixed_code)
            if pre:
                _log("AGENT", f"⚠️ Fixed code has syntax error ({pre}) — asking LLM again.")
                # One more targeted syntax fix
                fixed_code = _ask_llm_to_fix_manim(fixed_code, pre, attempt=attempt, scene_description=scene_text)
                if _syntax_check(fixed_code):
                    _log("AGENT", "⚠️ Second syntax fix also failed — skipping.")
                    continue
            current_code = fixed_code
        except Exception as fix_exc:
            _log("AGENT", f"⚠️ Fix call raised: {fix_exc}")

    # ── fallback tier 1: styled card ────────────────────────────────────────
    _log("FALLBACK", "Trying styled fallback scene (tier 1)…")
    fallback1 = _generate_fallback_scene(scene_id, scene_text, scene_duration)
    result, err1 = _try_render(fallback1, attempt=0)
    if result:
        return result

    # ── fallback tier 2: absolute minimum ───────────────────────────────────
    _log("FALLBACK", "Trying minimal fallback scene (tier 2)…")
    fallback2 = _generate_minimal_fallback_scene(scene_id, scene_text, scene_duration)
    result, err2 = _try_render(fallback2, attempt=0)
    if result:
        return result

    _log("FATAL", f"Scene {scene_id} could not be rendered after all attempts. Errors:\n{err2}")
    return None