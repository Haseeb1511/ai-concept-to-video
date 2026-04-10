"""
frontend/pages/voiceover_studio.py
────────────────────────────────────────────────────────────────────────────
Voiceover Studio — render any Manim VoiceoverScene with built-in OpenAI TTS.

Completely separate from workflow.py:
  • paste your Claude-generated VoiceoverScene code
  • pick an OpenAI voice and output resolution
  • hit Generate → streams manim logs → shows final MP4
────────────────────────────────────────────────────────────────────────────
"""

import sys
import os
from pathlib import Path
import streamlit as st

# ── Resolve project root so src imports work regardless of CWD ───────────────
_HERE = Path(__file__).resolve()
_PROJECT_ROOT = _HERE.parent.parent.parent          # …/yt-short-generator
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.voiceover_pipeline.runner import (
    RESOLUTION_PRESETS,
    OPENAI_VOICES,
    run_voiceover_pipeline,
)

# ─── Session state ────────────────────────────────────────────────────────────
if "vs_video_path" not in st.session_state:
    st.session_state.vs_video_path = None
if "vs_logs" not in st.session_state:
    st.session_state.vs_logs = []

# ─── CSS (same design token system as workflow.py) ───────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Outfit:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

:root {
    --bg-void:    #06090d;
    --bg-base:    #0b1018;
    --bg-surface: #101720;
    --bg-card:    #141e2b;
    --border:     #1c2a3a;
    --border-lit: #2a3f57;
    --blue:       #4da6ff;
    --purple:     #9d6fff;
    --teal:       #2fd4a7;
    --amber:      #f5a623;
    --green:      #2ea04f;
    --red:        #f05252;
    --text-primary: #dde8f5;
    --text-body:    #8da0b8;
    --text-muted:   #4a5e75;
    --text-dim:     #2c3d52;
    --glow-purple: rgba(157,111,255,0.18);
}

html, body, .stApp {
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg-void) !important;
    color: var(--text-body) !important;
}

/* scanlines */
.stApp::before {
    content: '';
    position: fixed; inset: 0;
    background-image: repeating-linear-gradient(
        0deg, transparent, transparent 2px,
        rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
    );
    pointer-events: none; z-index: 9999;
}

.main .block-container {
    max-width: 860px !important;
    padding: 2.5rem 2rem 4rem !important;
    margin: 0 auto;
}

/* ── Hero ── */
.vs-hero {
    text-align: center;
    padding: 3.2rem 2rem 2.6rem;
    margin-bottom: 1.8rem;
    border-radius: 22px;
    background:
        radial-gradient(ellipse 80% 60% at 50% -10%, rgba(157,111,255,0.14), transparent),
        radial-gradient(ellipse 60% 40% at 85% 110%, rgba(77,166,255,0.10), transparent),
        linear-gradient(160deg, #110f22 0%, #0b1018 60%, #100f20 100%);
    border: 1px solid var(--border-lit);
    overflow: hidden;
    position: relative;
}

.vs-eyebrow {
    display: inline-flex; align-items: center; gap: 7px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px; font-weight: 500;
    letter-spacing: 2.5px; text-transform: uppercase;
    color: var(--purple);
    background: rgba(157,111,255,0.08);
    border: 1px solid rgba(157,111,255,0.22);
    padding: 5px 14px; border-radius: 30px; margin-bottom: 1.2rem;
}

.vs-eyebrow-dot {
    width:5px; height:5px; background:var(--purple);
    border-radius:50%; box-shadow: 0 0 6px var(--purple);
    animation: blink 2s ease-in-out infinite;
}

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

.vs-title {
    font-family: 'Syne', sans-serif !important;
    font-size: clamp(2.2rem, 5vw, 3.4rem) !important;
    font-weight: 800 !important; line-height:1.1 !important;
    letter-spacing:-1px !important;
    background: linear-gradient(135deg, #d4c6ff 0%, #9d6fff 35%, #4da6ff 70%, #d4c6ff 100%);
    background-size: 200% auto;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    animation: shimmer 5s linear infinite;
    margin-bottom: 0.55rem !important;
}

@keyframes shimmer { 0%{background-position:0% center} 100%{background-position:200% center} }

.vs-sub { font-size:1rem; color:var(--text-body); margin-bottom:1.6rem; }

.tech-chip { font-family:'IBM Plex Mono',monospace; font-size:10px;
    font-weight:500; padding:3px 10px; border-radius:20px; letter-spacing:0.5px; }
.chip-purple { background:rgba(157,111,255,.10); color:#b48dff; border:1px solid rgba(157,111,255,.22); }
.chip-blue   { background:rgba(77,166,255,.10);  color:#6abcff; border:1px solid rgba(77,166,255,.22); }
.chip-teal   { background:rgba(47,212,167,.10);  color:#4de0c0; border:1px solid rgba(47,212,167,.22); }
.chip-amber  { background:rgba(245,166,35,.10);  color:#ffc050; border:1px solid rgba(245,166,35,.22); }

/* ── Section label ── */
.section-label {
    font-family:'IBM Plex Mono',monospace;
    font-size:10px; font-weight:500; letter-spacing:2px;
    text-transform:uppercase; color:var(--text-muted);
    margin-bottom:0.6rem;
    display:flex; align-items:center; gap:8px;
}
.section-label::after {
    content:''; flex:1; height:1px;
    background:linear-gradient(90deg, var(--border), transparent);
}

/* ── Hint box ── */
.hint-box {
    background: linear-gradient(135deg,rgba(157,111,255,0.04),rgba(77,166,255,0.04));
    border: 1px solid rgba(157,111,255,0.18);
    border-left: 3px solid var(--purple);
    border-radius: 10px; padding: 14px 18px; margin-bottom: 1.4rem;
    font-family:'IBM Plex Mono',monospace; font-size:11.5px;
    line-height:1.75; color:var(--text-body);
}
.hint-box code { background:rgba(157,111,255,0.12); color:var(--purple);
    padding:1px 6px; border-radius:4px; font-size:11px; }
.hint-box strong { color:var(--text-primary); }

/* ── Inputs ── */
.stTextArea > div > div > textarea,
.stTextInput > div > div > input {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-size:13px !important;
    font-family:'IBM Plex Mono',monospace !important;
    line-height:1.65 !important;
    caret-color: var(--purple) !important;
}
.stTextArea > div > div > textarea:focus,
.stTextInput > div > div > input:focus {
    border-color: var(--purple) !important;
    box-shadow: 0 0 0 2px rgba(157,111,255,0.12) !important;
    outline: none !important;
}
.stTextArea label p, .stTextInput label p, .stSelectbox label p {
    font-family:'Outfit',sans-serif !important;
    font-size:13px !important; font-weight:600 !important;
    color:var(--text-primary) !important;
}

/* ── Selectbox ── */
div[data-baseweb="select"] > div {
    background-color: var(--bg-base) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family:'Outfit',sans-serif !important; font-size:13px !important;
}
div[data-baseweb="select"] > div:focus-within {
    border-color: var(--purple) !important;
    box-shadow: 0 0 0 2px rgba(157,111,255,0.12) !important;
}
div[data-baseweb="popover"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-lit) !important; border-radius:10px !important;
}
li[role="option"] {
    font-family:'Outfit',sans-serif !important; font-size:13px !important;
    color:var(--text-body) !important;
}
li[role="option"]:hover {
    background-color:rgba(157,111,255,0.08) !important; color:var(--purple) !important;
}

/* ── Generate button ── */
.btn-generate .stButton > button {
    width:100% !important; height:3.4rem !important;
    border-radius:10px !important; border:none !important;
    font-family:'Outfit',sans-serif !important; font-size:15px !important;
    font-weight:600 !important; cursor:pointer !important;
    background: linear-gradient(135deg, #6940c0 0%, #4c2a9e 100%) !important;
    color: #e2d4ff !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.08) !important;
    transition: all 0.25s cubic-bezier(0.4,0,0.2,1) !important;
}
.btn-generate .stButton > button:hover {
    background: linear-gradient(135deg, #7a4fd6 0%, #5c36b4 100%) !important;
    box-shadow: 0 8px 24px rgba(157,111,255,0.35), inset 0 1px 0 rgba(255,255,255,0.12) !important;
    color:#ffffff !important; transform:translateY(-2px) !important;
}

/* ── Clear button ── */
.stButton > button {
    width:100% !important; height:3.2rem !important;
    border-radius:10px !important; border:none !important;
    font-family:'Outfit',sans-serif !important; font-size:14px !important;
    font-weight:600 !important;
    background: linear-gradient(135deg, #2a5a9e 0%, #1e3f6e 100%) !important;
    color: #d0e8ff !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.07) !important;
    transition: all 0.25s cubic-bezier(0.4,0,0.2,1) !important;
}
.stButton > button:hover {
    transform:translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(77,166,255,0.3), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    background: linear-gradient(135deg, #3668b0 0%, #254e88 100%) !important;
    color:#ffffff !important;
}

/* ── Download button ── */
.stDownloadButton > button {
    width:100% !important; height:3rem !important;
    border-radius:10px !important;
    border: 1px solid rgba(47,212,167,0.3) !important;
    background: rgba(47,212,167,0.06) !important;
    color: var(--teal) !important;
    font-family:'Outfit',sans-serif !important; font-size:14px !important;
    font-weight:600 !important; transition:all 0.25s ease !important;
}
.stDownloadButton > button:hover {
    background: rgba(47,212,167,0.12) !important;
    border-color: rgba(47,212,167,0.5) !important;
    box-shadow: 0 4px 16px rgba(47,212,167,0.2) !important;
    transform:translateY(-1px) !important; color:#5de8c5 !important;
}

/* ── Log terminal ── */
.log-terminal {
    background: #07090e;
    border: 1px solid var(--border-lit);
    border-radius: 12px;
    overflow: hidden;
    margin-top: 1.2rem;
}
.log-header {
    display:flex; align-items:center; gap:10px;
    padding: 10px 16px;
    background: rgba(12,18,28,0.95);
    border-bottom: 1px solid var(--border);
}
.log-title {
    font-family:'IBM Plex Mono',monospace; font-size:10px;
    font-weight:500; color:var(--text-muted);
    letter-spacing:2px; text-transform:uppercase; flex:1;
}
.log-dot {
    width:7px; height:7px; border-radius:50%;
    background:var(--purple); box-shadow:0 0 8px var(--purple);
    animation: pulse-dot 1.8s ease-in-out infinite;
}
@keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.3;transform:scale(0.8)} }
.log-body {
    padding: 10px 16px; max-height: 340px;
    overflow-y: auto; scrollbar-width: thin;
    scrollbar-color: #1e2a38 transparent;
}
.log-body::-webkit-scrollbar { width:3px; }
.log-body::-webkit-scrollbar-thumb { background:#1e2a38; border-radius:2px; }
.log-line {
    font-family:'IBM Plex Mono',monospace; font-size:11.5px;
    color:#9db5cc; line-height:1.7; padding:1px 0;
}
.log-line.ok  { color:#4ade80; }
.log-line.err { color:#f87171; }
.log-line.info{ color:#b48dff; }

/* ── Video card ── */
.video-wrap {
    background: var(--bg-card);
    border: 1px solid var(--border-lit);
    border-radius: 16px; padding: 1.6rem;
    margin: 1.4rem 0;
    box-shadow: 0 0 40px rgba(157,111,255,0.07);
}
.video-header {
    font-family:'Syne',sans-serif; font-size:1.1rem;
    font-weight:700; color:var(--text-primary);
    margin-bottom:1rem; display:flex; align-items:center; gap:8px;
}

/* ── Misc ── */
.stAlert { background:rgba(157,111,255,0.05) !important;
    border:1px solid rgba(157,111,255,0.2) !important;
    border-radius:10px !important; color:var(--text-primary) !important; }
div[data-testid="stSuccess"] { background:rgba(46,160,67,0.08)!important;
    border:1px solid rgba(46,160,67,0.25)!important; }
div[data-testid="stError"]   { background:rgba(240,82,82,0.08)!important;
    border:1px solid rgba(240,82,82,0.25)!important; }

[data-testid="stSidebar"] {
    background-color: var(--bg-base) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stHorizontalBlock"] { gap: 14px !important; }
hr { border:none !important; border-top:1px solid var(--border) !important; margin:2rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ─── Hero ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vs-hero">
    <div class="vs-eyebrow">
        <span class="vs-eyebrow-dot"></span>
        Built-in Manim Voiceover
    </div>
    <div class="vs-title">Voiceover Studio</div>
    <p class="vs-sub">Paste your Claude-generated VoiceoverScene code → choose voice &amp; resolution → render.</p>
    <div style="display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">
        <span class="tech-chip chip-purple">manim-voiceover</span>
        <span class="tech-chip chip-blue">OpenAI TTS</span>
        <span class="tech-chip chip-teal">Auto Render</span>
        <span class="tech-chip chip-amber">No SRT / No Subtitles</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Hint box ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hint-box">
    <strong>⚡ How to use this page</strong><br>
    &nbsp;1. Write your Manim VoiceoverScene code directly into <code>custom/voiceover_manim</code> — it loads automatically<br>
    &nbsp;2. Or paste the <em>entire Python file</em> below — it must contain a <code>VoiceoverScene</code> subclass<br>
    &nbsp;3. The system auto-detects the class name, injects the correct resolution &amp; patches the voice<br>
    &nbsp;4. No separate script needed — voiceover text is <strong>already inside your code</strong><br>
    &nbsp;• Subtitles are permanently disabled — no <code>.srt</code> file will be created<br>
    &nbsp;• If the textarea is empty, the pipeline falls back to <code>custom/voiceover_manim</code> automatically
</div>
""", unsafe_allow_html=True)


# ── Auto-load from disk ─────────────────────────────────────────────────────
_base = Path(__file__).resolve().parent.parent.parent / "custom"
_voiceover_manim_file = _base / "voiceover_manim"
_default_voiceover_manim = (
    _voiceover_manim_file.read_text(encoding="utf-8")
    if _voiceover_manim_file.exists() and _voiceover_manim_file.stat().st_size > 0
    else ""
)


# ─── Code input ───────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Manim VoiceoverScene Code</p>', unsafe_allow_html=True)

manim_code = st.text_area(
    "🎬 Manim VoiceoverScene Code",
    value=_default_voiceover_manim,
    placeholder=(
        "from manim import *\n"
        "from manim_voiceover import VoiceoverScene\n"
        "from manim_voiceover.services.openai import OpenAIService\n\n"
        "class MyShort(VoiceoverScene):\n"
        "    def construct(self):\n"
        "        self.set_speech_service(OpenAIService(voice=\"onyx\", transcription_model=None), create_subcaption=False)\n"
        "        with self.voiceover(text=\"Hello world!\") as tracker:\n"
        "            self.play(Create(Circle()), run_time=tracker.duration)\n"
        "\n"
        "# If empty, uses 'custom/voiceover_manim' automatically."
    ),
    height=380,
    key="vs_manim_code",
)


# ─── Options row ─────────────────────────────────────────────────────────────
st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
st.markdown('<p class="section-label">Render Options</p>', unsafe_allow_html=True)

col_voice, col_res = st.columns([1, 1])

with col_voice:
    chosen_voice = st.selectbox(
        "🎙️ OpenAI Voice Model",
        options=OPENAI_VOICES,
        index=OPENAI_VOICES.index("onyx") if "onyx" in OPENAI_VOICES else 0,
        help="This overrides the voice= setting inside your code.",
        key="vs_voice",
    )

with col_res:
    chosen_resolution = st.selectbox(
        "📐 Output Resolution",
        options=list(RESOLUTION_PRESETS.keys()),
        index=list(RESOLUTION_PRESETS.keys()).index("Shorts (1080x1920)"),
        key="vs_resolution",
    )

# ─── Action buttons ───────────────────────────────────────────────────────────
st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)

col_gen, col_clr = st.columns([3, 1])
with col_gen:
    st.markdown('<div class="btn-generate">', unsafe_allow_html=True)
    generate_btn = st.button("✦ Generate Voiceover Video", key="vs_generate")
    st.markdown('</div>', unsafe_allow_html=True)
with col_clr:
    clear_btn = st.button("🗑️ Clear", key="vs_clear")

if clear_btn:
    st.session_state.vs_video_path = None
    st.session_state.vs_logs = []
    st.rerun()


# ─── Generation logic ─────────────────────────────────────────────────────────
if generate_btn:
    code = manim_code.strip() or _default_voiceover_manim
    if not code:
        st.error("⚠️ No code found. Paste code above or save it to 'custom/voiceover_manim'.")
    else:
        st.session_state.vs_video_path = None
        st.session_state.vs_logs = []

        # ── Build log HTML helper ─────────────────────────────────────────
        log_placeholder = st.empty()

        def _render_logs(logs: list[str]) -> None:
            items_html = ""
            for line in logs[-80:]:          # show last 80 lines
                if line.startswith("✅"):
                    cls = "ok"
                elif line.startswith("❌"):
                    cls = "err"
                elif line.startswith("📋"):
                    cls = "info"
                else:
                    cls = ""
                safe = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                items_html += f'<div class="log-line {cls}">{safe}</div>'

            log_placeholder.markdown(f"""
<div class="log-terminal">
  <div class="log-header">
    <span class="log-dot"></span>
    <span class="log-title">Render Log</span>
    <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:var(--text-dim);
                 background:rgba(255,255,255,0.03);border:1px solid var(--border);
                 padding:2px 8px;border-radius:20px;">{len(logs)} lines</span>
  </div>
  <div class="log-body" id="log-scroll">{items_html}</div>
</div>
<script>
  var el = document.getElementById('log-scroll');
  if(el) el.scrollTop = el.scrollHeight;
</script>
""", unsafe_allow_html=True)

        # ── Stream the pipeline ───────────────────────────────────────────
        output_mp4 = None
        try:
            for log_line in run_voiceover_pipeline(
                manim_code=code,
                resolution_label=chosen_resolution,
                openai_voice=chosen_voice,
            ):
                st.session_state.vs_logs.append(log_line)
                _render_logs(st.session_state.vs_logs)

                if log_line.startswith("✅ OUTPUT:"):
                    output_mp4 = log_line.replace("✅ OUTPUT:", "").strip()

        except Exception as exc:
            err = f"❌ Pipeline error: {exc}"
            st.session_state.vs_logs.append(err)
            _render_logs(st.session_state.vs_logs)
            st.error(str(exc))

        if output_mp4 and Path(output_mp4).exists():
            st.session_state.vs_video_path = output_mp4
            st.success("🎉 Video rendered successfully!")
        elif output_mp4 is None:
            # Check if error lines exist
            has_error = any("❌" in l for l in st.session_state.vs_logs)
            if has_error:
                st.error("❌ Render failed. Check the log above for details.")


# ─── Video preview ────────────────────────────────────────────────────────────
if st.session_state.vs_video_path:
    video_path = Path(st.session_state.vs_video_path)
    if video_path.exists():
        st.markdown("""
<div class="video-wrap">
  <div class="video-header">🎬 Rendered Output</div>
</div>
""", unsafe_allow_html=True)
        st.video(str(video_path))

        col_dl, col_info = st.columns([2, 1])
        with col_dl:
            with open(video_path, "rb") as vf:
                st.download_button(
                    label="⬇️ Download MP4",
                    data=vf,
                    file_name=video_path.name,
                    mime="video/mp4",
                    key="vs_download",
                )
        with col_info:
            size_mb = video_path.stat().st_size / 1_048_576
            st.markdown(f"""
<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:10px;
            padding:12px 16px;font-family:'IBM Plex Mono',monospace;font-size:11px;
            color:var(--text-muted);line-height:2;">
    📁 {video_path.name}<br>
    💾 {size_mb:.2f} MB<br>
    📐 {chosen_resolution}
</div>
""", unsafe_allow_html=True)

    else:
        st.warning("⚠️ Video file no longer found on disk.")


# ─── Previous log (persisted across reruns) ──────────────────────────────────
elif st.session_state.vs_logs and not generate_btn:
    items_html = ""
    for line in st.session_state.vs_logs[-80:]:
        cls = "ok" if line.startswith("✅") else "err" if line.startswith("❌") else "info" if line.startswith("📋") else ""
        safe = line.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
        items_html += f'<div class="log-line {cls}">{safe}</div>'

    st.markdown(f"""
<div class="log-terminal">
  <div class="log-header">
    <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:500;
                 color:var(--text-muted);letter-spacing:2px;">LAST RUN LOG</span>
  </div>
  <div class="log-body">{items_html}</div>
</div>
""", unsafe_allow_html=True)


# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 1rem 1rem;
    font-family:'IBM Plex Mono',monospace;font-size:10.5px;
    letter-spacing:1px;color:#2c3d52;">
    AI Short Studio &nbsp;·&nbsp; Voiceover Studio &nbsp;·&nbsp;
    <span style="color:#4a5e75;">manim-voiceover + OpenAI TTS</span>
</div>
""", unsafe_allow_html=True)
