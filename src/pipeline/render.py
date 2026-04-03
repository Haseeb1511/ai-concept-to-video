import os
import re
import ast
import subprocess
import json
import textwrap
from pathlib import Path
from typing import TypedDict, Annotated, List, Optional, Union
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from src.agent.model_loader import (
    MANIM_SCENES_DIR, VIDEOS_DIR, VIDEO_FPS, call_llm, get_tool_calling_llm
)
from src.pipeline.utils import _get_quality_flag
from src.mcp.client import get_mcp_tools

class AgentState(TypedDict):
    manim_code: str
    error_history: List[str]
    attempt: int
    max_attempts: int
    scene_text: str
    success: bool
    final_video: Optional[str]
    width: int
    height: int
    quality: str
    scene_id: int
    scene_data: dict
    messages: List[BaseMessage]

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

# ─── LangGraph Nodes ─────────────────────────────────────────────────────────

def _render_node(state: AgentState):
    """Attempt to render and update state."""
    code = state["manim_code"]
    attempt = state["attempt"] + 1
    scene_id = state["scene_id"]

    print(f"   🎬 [Scene {scene_id}] Render attempt {attempt}/{state['max_attempts']}...")
    
    result, error = _try_render_internal(
        scene_id,
        code,
        state["scene_data"],
        state["width"],
        state["height"],
        state["quality"],
        attempt
    )
    
    if result:
        print(f"   ✅ [Scene {scene_id}] Rendered successfully on attempt {attempt}")
    else:
        short_err = (error or "").strip().splitlines()[-1] if error else "unknown error"
        print(f"   ❌ [Scene {scene_id}] Attempt {attempt} failed: {short_err}")
    
    messages = list(state["messages"])
    if error:
        messages.append(HumanMessage(content=f"Render failed with error:\n{error}"))
    
    return {
        "attempt": attempt,
        "success": result is not None,
        "final_video": result,
        "error_history": state["error_history"] + ([error] if error else []),
        "messages": messages
    }

def _researcher_node(state: AgentState):
    """ReAct agent node to research and fix code."""
    llm_with_tools = get_tool_calling_llm()
    scene_id = state["scene_id"]
    attempt  = state["attempt"]

    if attempt >= 3:
        print(f"   🤖 [Scene {scene_id}] Attempt {attempt}: Switching to simplified scene strategy...")
        system_msg = SystemMessage(content=_SIMPLIFY_SYSTEM)
    else:
        print(f"   🤖 [Scene {scene_id}] AI agent analyzing error and fixing code (attempt {attempt})...")
        system_msg = SystemMessage(content=_BASE_FIX_SYSTEM)
        
    messages = [system_msg] + state["messages"]
    
    if state["attempt"] >= 2:
        messages.append(HumanMessage(content=f"Reminder: The scene should show: {state['scene_text']}"))

    response = llm_with_tools.invoke(messages)
    
    new_code = state["manim_code"]
    if not response.tool_calls:
        new_code = _strip_markdown_fences(response.content)
        print(f"   📝 [Scene {scene_id}] Got fixed code from AI ({len(new_code)} chars)")
    else:
        print(f"   🔧 [Scene {scene_id}] AI is using MCP tools to research the fix...")
        
    return {
        "messages": state["messages"] + [response],
        "manim_code": new_code
    }

def _should_continue(state: AgentState):
    if state["success"]:
        return END
    if state["attempt"] >= state["max_attempts"]:
        return END
    
    if state["messages"] and hasattr(state["messages"][-1], "tool_calls") and state["messages"][-1].tool_calls:
        return "tools"
        
    return "researcher"

# --- Internal Helper for Render Node ---
def _try_render_internal(scene_id, code, scene_data, width, height, quality, attempt):
    cleaned = _normalise_class_name(_clean_code(code))
    script_code = MANIM_IMPORTS.format(width=width, height=height, fps=VIDEO_FPS)
    script_code += "\n" + cleaned

    script_path = MANIM_SCENES_DIR / f"custom_scene_{scene_id}.py"
    script_path.write_text(script_code, encoding="utf-8")
    print(f"      📄 Script written → {script_path.name} ({len(script_code)} chars)")

    quality_flag = _get_quality_flag(quality)
    output_name = f"custom_scene_{scene_id}_render.mp4"

    cmd = [
        "manim", "render", str(script_path), "RenderScene",
        quality_flag, "-o", output_name,
        "--media_dir", str(MANIM_SCENES_DIR / "media"),
        "--renderer=cairo",
        "--disable_caching",
    ]
    env = os.environ.copy()
    env["SCENE_DATA"] = json.dumps(scene_data)

    print(f"      ⚙️  Running manim render ({quality_flag})...")
    try:
        subprocess.run(
            cmd, env=env, capture_output=True, text=True,
            check=True, timeout=120,
        )
        video_files = list((MANIM_SCENES_DIR / "media" / "videos").rglob(output_name))
        if not video_files:
            print(f"      ⚠️  Manim finished but output file not found: {output_name}")
            return None, f"Manim finished but '{output_name}' not found."

        final_path = VIDEOS_DIR / f"custom_scene_{scene_id}.mp4"
        if final_path.exists():
            final_path.unlink()
        video_files[0].replace(final_path)
        print(f"      ✅ Video saved → {final_path.name}")
        return str(final_path), ""

    except subprocess.CalledProcessError as exc:
        combined = (exc.stderr or "") + "\n" + (exc.stdout or "")
        last_line = combined.strip().splitlines()[-1] if combined.strip() else "unknown error"
        print(f"      ❌ Manim process error: {last_line}")
        return None, combined
    except Exception as exc:
        print(f"      ❌ Unexpected error: {exc}")
        return None, str(exc)

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
    """Agentic Manim renderer with LangGraph self-healing and multi-tier fallback."""
    MANIM_SCENES_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

    scene_text: str = scene_data.get("text", "")
    scene_duration: float = float(scene_data.get("duration", 5.0))

    def _log(category: str, msg: str) -> None:
        if log_callback:
            log_callback(category, msg)
        print(f"[pipeline.render] [{category}] {msg}")

    # --- Build LangGraph ---
    from langgraph.prebuilt import ToolNode
    
    workflow = StateGraph(AgentState)
    workflow.add_node("render", _render_node)
    workflow.add_node("researcher", _researcher_node)
    workflow.add_node("tools", ToolNode(get_mcp_tools()))

    workflow.set_entry_point("render")
    workflow.add_conditional_edges("render", _should_continue, {
        "researcher": "researcher",
        END: END
    })
    workflow.add_conditional_edges("researcher", _should_continue, {
        "tools": "tools",
        "researcher": "researcher", 
        END: END
    })
    workflow.add_edge("tools", "researcher")

    app = workflow.compile()

    _log("AGENT", f"Starting LangGraph render agent for Scene {scene_id} (max {MAX_FIX_RETRIES} attempts)")
    print(f"\n   🤖 LangGraph agent initialized for Scene {scene_id}")
    
    initial_state = {
        "manim_code": manim_code,
        "error_history": [],
        "attempt": 0,
        "max_attempts": MAX_FIX_RETRIES,
        "scene_text": scene_text,
        "success": False,
        "final_video": None,
        "width": width,
        "height": height,
        "quality": quality,
        "scene_id": scene_id,
        "scene_data": scene_data,
        "messages": []
    }

    final_state = app.invoke(initial_state)

    if final_state["success"]:
        _log("COMPLETE", f"Scene {scene_id} rendered OK → {final_state['final_video']}")
        return final_state["final_video"]

    # ── fallback tier 1: styled card ────────────────────────────────────────
    _log("FALLBACK", f"All {MAX_FIX_RETRIES} AI attempts failed. Trying styled fallback card...")
    print(f"   ⚠️  [Scene {scene_id}] Falling back to styled text card (tier 1)")
    fallback1 = _generate_fallback_scene(scene_id, scene_text, scene_duration)
    result, err1 = _try_render_internal(scene_id, fallback1, scene_data, width, height, quality, 0)
    if result:
        print(f"   ✅ [Scene {scene_id}] Fallback tier 1 succeeded")
        return result

    # ── fallback tier 2: absolute minimum ───────────────────────────────────
    _log("FALLBACK", "Trying minimal text fallback (tier 2)...")
    print(f"   ⚠️  [Scene {scene_id}] Trying minimal text fallback (tier 2)")
    fallback2 = _generate_minimal_fallback_scene(scene_id, scene_text, scene_duration)
    result, err2 = _try_render_internal(scene_id, fallback2, scene_data, width, height, quality, 0)
    if result:
        print(f"   ✅ [Scene {scene_id}] Fallback tier 2 succeeded")
        return result

    _log("FATAL", f"Scene {scene_id} failed after all attempts and fallbacks.")
    print(f"   ❌ [Scene {scene_id}] All render attempts and fallbacks exhausted")
    return None