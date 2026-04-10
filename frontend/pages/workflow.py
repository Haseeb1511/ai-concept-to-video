import streamlit as st
import requests
import os
import json
from pathlib import Path

# ─── Session State ─────────────────────────────────────────────────────────
if "final_video" not in st.session_state:
    st.session_state.final_video = None
if "seo_title" not in st.session_state:
    st.session_state.seo_title = ""
if "seo_desc" not in st.session_state:
    st.session_state.seo_desc = ""

# Page config is handled in app.py

# ─── Custom Styling ────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=Outfit:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

/* ── Reset & Base ─────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }

:root {
    --bg-void:    #06090d;
    --bg-base:    #0b1018;
    --bg-surface: #101720;
    --bg-card:    #141e2b;
    --bg-hover:   #19253500;
    --border:     #1c2a3a;
    --border-lit: #2a3f57;
    --blue:       #4da6ff;
    --blue-dim:   #2d6fa8;
    --purple:     #9d6fff;
    --teal:       #2fd4a7;
    --amber:      #f5a623;
    --red:        #f05252;
    --green:      #2ea04f;
    --text-primary: #dde8f5;
    --text-body:    #8da0b8;
    --text-muted:   #4a5e75;
    --text-dim:     #2c3d52;
    --glow-blue:  rgba(77,166,255,0.18);
    --glow-purple: rgba(157,111,255,0.18);
}

/* ── Global Font ──────────────────────────────────────── */
html, body, .stApp {
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg-void) !important;
    color: var(--text-body) !important;
}

/* Specific text elements for custom font */
.stMarkdown, .stText, .stButton, .stTextArea, .stTextInput, .stSelectbox, label, p, div {
    font-family: 'Outfit', sans-serif;
}

/* Scanline texture overlay */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: repeating-linear-gradient(
        0deg,
        transparent,
        transparent 2px,
        rgba(0,0,0,0.03) 2px,
        rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

/* ── Main container ────────────────────────────────────── */
.main .block-container {
    max-width: 840px !important;
    padding: 2.5rem 2rem 4rem !important;
    margin: 0 auto;
}

/* ── Hero Banner ───────────────────────────────────────── */
.hero-wrap {
    position: relative;
    text-align: center;
    padding: 3.5rem 2rem 2.8rem;
    margin-bottom: 2rem;
    border-radius: 20px;
    background:
        radial-gradient(ellipse 80% 60% at 50% -10%, rgba(77,166,255,0.12), transparent),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(157,111,255,0.10), transparent),
        linear-gradient(160deg, #0f1922 0%, #0b1018 60%, #0f1320 100%);
    border: 1px solid var(--border-lit);
    overflow: hidden;
}

.hero-wrap::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
        radial-gradient(circle at 20% 80%, rgba(77,166,255,0.06) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(157,111,255,0.06) 0%, transparent 50%);
    border-radius: 20px;
}

.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px;
    font-weight: 500;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--blue);
    background: rgba(77,166,255,0.08);
    border: 1px solid rgba(77,166,255,0.2);
    padding: 5px 14px;
    border-radius: 30px;
    margin-bottom: 1.2rem;
}

.hero-eyebrow-dot {
    width: 5px; height: 5px;
    background: var(--blue);
    border-radius: 50%;
    box-shadow: 0 0 6px var(--blue);
    animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
    0%,100% { opacity: 1; }
    50% { opacity: 0.2; }
}

.hero-title {
    font-family: 'Syne', sans-serif !important;
    font-size: clamp(2.4rem, 5vw, 3.8rem) !important;
    font-weight: 800 !important;
    line-height: 1.1 !important;
    letter-spacing: -1px !important;
    background: linear-gradient(135deg, #c6deff 0%, #7ab8ff 35%, #9d6fff 70%, #c6deff 100%);
    background-size: 200% auto;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    animation: shimmer 5s linear infinite;
    margin-bottom: 0.6rem !important;
}

@keyframes shimmer {
    0% { background-position: 0% center; }
    100% { background-position: 200% center; }
}

.hero-sub {
    font-size: 1rem;
    color: var(--text-body);
    font-weight: 400;
    letter-spacing: 0.2px;
    margin-bottom: 1.8rem;
}

.hero-tags {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    flex-wrap: wrap;
}

.tech-chip {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    padding: 3px 10px;
    border-radius: 20px;
    letter-spacing: 0.5px;
}

.chip-blue   { background: rgba(77,166,255,0.10); color: #6abcff; border: 1px solid rgba(77,166,255,0.22); }
.chip-purple { background: rgba(157,111,255,0.10); color: #b48dff; border: 1px solid rgba(157,111,255,0.22); }
.chip-teal   { background: rgba(47,212,167,0.10);  color: #4de0c0; border: 1px solid rgba(47,212,167,0.22); }
.chip-amber  { background: rgba(245,166,35,0.10);  color: #ffc050; border: 1px solid rgba(245,166,35,0.22); }

/* ── Section Labels ───────────────────────────────────── */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
}

/* ── Input Card Panel ─────────────────────────────────── */
.panel-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.8rem;
    margin-bottom: 1.2rem;
    position: relative;
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.panel-card:hover {
    border-color: var(--border-lit);
    box-shadow: 0 0 30px rgba(77,166,255,0.06);
}

/* ── Hint Box ─────────────────────────────────────────── */
.hint-box {
    background: linear-gradient(135deg, rgba(77,166,255,0.04), rgba(157,111,255,0.04));
    border: 1px solid rgba(77,166,255,0.15);
    border-left: 3px solid var(--blue);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 1.4rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11.5px;
    line-height: 1.75;
    color: var(--text-body);
}

.hint-box code {
    background: rgba(77,166,255,0.12);
    color: var(--blue);
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 11px;
}

.hint-box strong {
    color: var(--text-primary);
}

/* ── Streamlit Text Areas & Inputs ────────────────────── */
.stTextArea > div > div > textarea,
.stTextInput > div > div > input {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-size: 13px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    line-height: 1.65 !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    caret-color: var(--blue) !important;
}

.stTextArea > div > div > textarea:focus,
.stTextInput > div > div > input:focus {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 2px rgba(77,166,255,0.12), inset 0 1px 0 rgba(77,166,255,0.05) !important;
    outline: none !important;
}

/* label styling */
.stTextArea label p, .stTextInput label p, .stSelectbox label p {
    font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
    letter-spacing: 0.2px;
}

/* ── Selectbox ──────────────────────────────────────────── */
div[data-baseweb="select"] > div {
    background-color: var(--bg-base) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important;
}

div[data-baseweb="select"] > div:focus-within {
    border-color: var(--blue) !important;
    box-shadow: 0 0 0 2px rgba(77,166,255,0.12) !important;
}

div[data-baseweb="popover"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-lit) !important;
    border-radius: 10px !important;
}

li[role="option"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important;
    color: var(--text-body) !important;
}

li[role="option"]:hover {
    background-color: rgba(77,166,255,0.08) !important;
    color: var(--blue) !important;
}

/* ── Buttons ───────────────────────────────────────────── */
.stButton > button {
    width: 100% !important;
    height: 3.2rem !important;
    border-radius: 10px !important;
    border: none !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px !important;
    cursor: pointer !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    position: relative !important;
    overflow: hidden !important;
    background: linear-gradient(135deg, #2a5a9e 0%, #1e3f6e 100%) !important;
    color: #d0e8ff !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.07) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(77,166,255,0.3), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    background: linear-gradient(135deg, #3668b0 0%, #254e88 100%) !important;
    color: #ffffff !important;
    border: none !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.4) !important;
}

/* Purple CTA override */
.btn-generate .stButton > button {
    background: linear-gradient(135deg, #6940c0 0%, #4c2a9e 100%) !important;
    color: #e2d4ff !important;
    font-size: 15px !important;
    height: 3.4rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.08) !important;
}

.btn-generate .stButton > button:hover {
    background: linear-gradient(135deg, #7a4fd6 0%, #5c36b4 100%) !important;
    box-shadow: 0 8px 24px rgba(157,111,255,0.35), inset 0 1px 0 rgba(255,255,255,0.12) !important;
    color: #ffffff !important;
}

/* ── Download button ───────────────────────────────────── */
.stDownloadButton > button {
    width: 100% !important;
    height: 3rem !important;
    border-radius: 10px !important;
    border: 1px solid rgba(47,212,167,0.3) !important;
    background: rgba(47,212,167,0.06) !important;
    color: var(--teal) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    transition: all 0.25s ease !important;
}

.stDownloadButton > button:hover {
    background: rgba(47,212,167,0.12) !important;
    border-color: rgba(47,212,167,0.5) !important;
    box-shadow: 0 4px 16px rgba(47,212,167,0.2) !important;
    transform: translateY(-1px) !important;
    color: #5de8c5 !important;
}

/* ── Activity Feed ─────────────────────────────────────── */
.activity-feed {
    background: linear-gradient(160deg, #0b1018, #0f1720);
    border: 1px solid var(--border-lit);
    border-radius: 14px;
    overflow: hidden;
    margin-top: 1.4rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.02);
}

.feed-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 11px 16px;
    background: rgba(15, 23, 32, 0.9);
    border-bottom: 1px solid var(--border);
    backdrop-filter: blur(8px);
}

.feed-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    color: var(--text-muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    flex: 1;
}

.feed-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px var(--green);
    animation: pulse-dot 1.8s ease-in-out infinite;
}

@keyframes pulse-dot {
    0%,100% { opacity:1; transform: scale(1); }
    50% { opacity:0.3; transform: scale(0.8); }
}

.feed-count {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: var(--text-dim);
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border);
    padding: 2px 8px;
    border-radius: 20px;
}

.feed-body {
    padding: 8px 14px;
    max-height: 300px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #1e2a38 transparent;
}

.feed-body::-webkit-scrollbar { width: 3px; }
.feed-body::-webkit-scrollbar-track { background: transparent; }
.feed-body::-webkit-scrollbar-thumb { background: #1e2a38; border-radius: 2px; }

.feed-item {
    display: grid;
    grid-template-columns: 22px 1fr auto auto;
    align-items: start;
    gap: 8px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(28,42,58,0.6);
    animation: feed-in 0.3s cubic-bezier(0.4,0,0.2,1);
}

.feed-item:last-child { border-bottom: none; }

@keyframes feed-in {
    from { opacity:0; transform: translateX(-6px); }
    to   { opacity:1; transform: translateX(0); }
}

.feed-icon { font-size: 14px; padding-top: 1px; }

.feed-text {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11.5px;
    color: #9db5cc;
    line-height: 1.5;
    word-break: break-all;
}

.feed-time {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: var(--text-dim);
    padding-top: 2px;
    white-space: nowrap;
}

.feed-pill {
    font-family: 'Outfit', sans-serif;
    font-size: 9.5px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    white-space: nowrap;
    margin-top: 2px;
}

.pill-info     { background:rgba(77,166,255,0.12);  color:#6abcff;  border:1px solid rgba(77,166,255,0.22); }
.pill-audio    { background:rgba(157,111,255,0.12); color:#b48dff;  border:1px solid rgba(157,111,255,0.22); }
.pill-render   { background:rgba(56,189,248,0.12);  color:#60cdff;  border:1px solid rgba(56,189,248,0.22); }
.pill-agent    { background:rgba(245,166,35,0.12);  color:#ffc050;  border:1px solid rgba(245,166,35,0.22); }
.pill-warning  { background:rgba(249,115,22,0.12);  color:#fb923c;  border:1px solid rgba(249,115,22,0.22); }
.pill-success  { background:rgba(46,164,79,0.12);   color:#4ade80;  border:1px solid rgba(46,164,79,0.22); }
.pill-error    { background:rgba(240,82,82,0.12);   color:#f87171;  border:1px solid rgba(240,82,82,0.22); }
.pill-assembly { background:rgba(47,212,167,0.12);  color:#4de0c0;  border:1px solid rgba(47,212,167,0.22); }

/* ── Alerts ───────────────────────────────────────────── */
.stAlert {
    background: rgba(77,166,255,0.05) !important;
    border: 1px solid rgba(77,166,255,0.2) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'Outfit', sans-serif !important;
}

div[data-testid="stSuccess"] {
    background: rgba(46,160,67,0.08) !important;
    border: 1px solid rgba(46,160,67,0.25) !important;
}

div[data-testid="stError"] {
    background: rgba(240,82,82,0.08) !important;
    border: 1px solid rgba(240,82,82,0.25) !important;
}

div[data-testid="stWarning"] {
    background: rgba(245,166,35,0.08) !important;
    border: 1px solid rgba(245,166,35,0.25) !important;
}

/* ── Video Section ─────────────────────────────────────── */
.video-wrap {
    background: var(--bg-card);
    border: 1px solid var(--border-lit);
    border-radius: 16px;
    padding: 1.6rem;
    margin: 1.4rem 0;
    box-shadow: 0 0 40px rgba(77,166,255,0.06);
}

.video-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── SEO Section ───────────────────────────────────────── */
.seo-panel {
    background: linear-gradient(135deg, rgba(157,111,255,0.04), rgba(77,166,255,0.04));
    border: 1px solid rgba(157,111,255,0.2);
    border-radius: 16px;
    padding: 1.6rem;
    margin-top: 1rem;
}

.seo-title {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.3rem;
}

.seo-sub {
    font-size: 12.5px;
    color: var(--text-muted);
    margin-bottom: 1.2rem;
}

/* ── Divider ──────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 2rem 0 !important;
}

/* ── Footer ───────────────────────────────────────────── */
.footer-bar {
    text-align: center;
    padding: 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px;
    letter-spacing: 1px;
    color: var(--text-dim);
}

.footer-bar span { color: var(--text-muted); }

/* ── Spinner ──────────────────────────────────────────── */
.stSpinner > div {
    border-top-color: var(--blue) !important;
}

/* ── Column gaps ──────────────────────────────────────── */
[data-testid="stHorizontalBlock"] { gap: 14px !important; }

/* Remove default Streamlit container styling that conflicts */
div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

/* ── Sidebar ──────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--bg-base) !important;
    border-right: 1px solid var(--border) !important;
}

</style>
""", unsafe_allow_html=True)


# ─── Hero Banner ───────────────────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
    <div class="hero-eyebrow">
        <span class="hero-eyebrow-dot"></span>
        AI-Powered Studio
    </div>
    <div class="hero-title">AI Short Generator</div>
    <p class="hero-sub">Paste your Manim scene &amp; narration — the pipeline handles the rest.</p>
    <div class="hero-tags">
        <span class="tech-chip chip-blue">LangGraph</span>
        <span class="tech-chip chip-purple">Manim</span>
        <span class="tech-chip chip-teal">FastAPI</span>
        <span class="tech-chip chip-amber">Streamlit</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─── Shared backend URL ────────────────────────────────────────────────────
backend_base = "http://127.0.0.1:8000"


# ─── Hint Box ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="hint-box">
    <strong>💡 Manim Code Requirements</strong><br>
    &nbsp;• Scene class <strong>must</strong> be named <code>RenderScene(Scene)</code><br>
    &nbsp;• Do <strong>not</strong> include <code>from manim import *</code> — it's injected automatically<br>
    &nbsp;• Access narration via: <code>data = json.loads(os.environ["SCENE_DATA"])</code><br>
    &nbsp;&nbsp;&nbsp;→ keys: <code>data["text"]</code> &nbsp;·&nbsp; <code>data["duration"]</code> &nbsp;·&nbsp; <code>data["scene_id"]</code><br>
    &nbsp;• Separate script scenes with a <strong>blank line</strong> (double Enter)
</div>
""", unsafe_allow_html=True)


# ── Auto-load from disk ─────────────────────────────────────────────────────
_base = Path(__file__).resolve().parent.parent.parent / "custom"
_manim_file  = _base / "manim"
_script_file = _base / "script"
_default_manim  = _manim_file.read_text(encoding="utf-8")  if _manim_file.exists()  else ""
_default_script = _script_file.read_text(encoding="utf-8") if _script_file.exists() else ""


# ─── Input Panel ───────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Scene Configuration</p>', unsafe_allow_html=True)

manim_code = st.text_area(
    "🎨 Manim Code",
    value=_default_manim,
    placeholder="Class RenderScene(Scene): ... If empty, uses 'custom/manim'.",
    height=300,
    key="custom_manim_code",
)

st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)

script_text = st.text_area(
    "📝 Narration Script",
    value=_default_script,
    placeholder="Separate each scene with a blank line. If empty, uses 'custom/script'.",
    height=180,
    key="custom_script",
)

st.markdown('<div style="height:14px"></div>', unsafe_allow_html=True)
st.markdown('<p class="section-label">Pipeline Options</p>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.5, 1.5, 1])
with col1:
    tts_custom = st.selectbox(
        "🎙️ TTS Provider",
        options=["openai", "elevenlabs", "google", "gtts", "coqui", "deepgram"],
        index=5,
        key="custom_tts",
    )
with col2:
    resolution_custom = st.selectbox(
        "📐 Video Size",
        options=["480p (854x480)", "720p (1280x720)", "1080p (1920x1080)", "4K (3840x2160)", "Shorts (1080x1920)"],
        index=4,
        key="custom_resolution",
    )
with col3:
    backend_custom_url = st.text_input(
        "🔗 Backend URL",
        value=f"{backend_base}/generate-custom-video",
        key="custom_backend_url",
    )

st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)

col_gen, col_clear = st.columns([3, 1])
with col_gen:
    st.markdown('<div class="btn-generate">', unsafe_allow_html=True)
    custom_generate_btn = st.button("✦ Generate Video", key="custom_generate")
    st.markdown('</div>', unsafe_allow_html=True)
with col_clear:
    clear_btn = st.button("🗑️ Clear Outputs", key="clear_outputs")

if clear_btn:
    import shutil
    result_dir = Path(__file__).resolve().parent.parent.parent / "manim_animation_result"
    try:
        if result_dir.exists():
            shutil.rmtree(result_dir)
        result_dir.mkdir(parents=True, exist_ok=True)
        st.success("✅  Successfully cleared all output data!")
    except Exception as e:
        st.error(f"⚠️ Error clearing outputs: {e}")

# ─── Generation Logic ───────────────────────────────────────────────────────
if custom_generate_btn:
    # Fallback to defaults if inputs are empty
    final_manim  = manim_code.strip()  or _default_manim
    final_script = script_text.strip() or _default_script

    if not final_manim:
        st.error("⚠️ Manim code is missing (and no default 'custom/manim' found).")
    elif not final_script:
        st.error("⚠️ Narration script is missing (and no default 'custom/script' found).")
    else:
        # ── State for parallel scene tracking ──────────────────────────────
        # scene_states[i] = {"audio": None|"running"|"done"|"error",
        #                     "render": None|"running"|"done"|"error",
        #                     "error_msg": ""}
        scene_states = {}   # populated once pipeline_start is received
        n_scenes_total = 0
        pipeline_stage = "starting"  # starting → scenes → stitching → done

        progress_placeholder = st.empty()
        error_placeholder    = st.empty()

        # ── Helper: render the full progress block ──────────────────────────
        def _render_progress():
            # Stage bar
            stages = [
                ("split",     "Split Script",   pipeline_stage in ("scenes", "stitching", "done")),
                ("scenes",    "Generate Scenes", pipeline_stage in ("stitching", "done")),
                ("stitching", "Stitch Video",    pipeline_stage == "done"),
                ("done",      "Done",            pipeline_stage == "done"),
            ]
            stage_html = ""
            for key, label, completed in stages:
                active = pipeline_stage == key or (key == "scenes" and pipeline_stage == "scenes")
                if completed:
                    cls, dot = "stage-done", "✅"
                elif pipeline_stage == key:
                    cls, dot = "stage-active", "⟳"
                else:
                    cls, dot = "stage-pending", "○"
                stage_html += f'<div class="stage-item {cls}"><span class="stage-dot">{dot}</span>{label}</div>'

            # Scene cards (only shown after pipeline_start)
            cards_html = ""
            if scene_states:
                for i in sorted(scene_states.keys()):
                    s = scene_states[i]
                    audio_st  = s.get("audio",  "pending")
                    render_st = s.get("render", "pending")
                    err_msg   = s.get("error_msg", "")

                    def _badge(st_val, label):
                        if st_val == "done":
                            return f'<span class="badge badge-done">✅ {label}</span>'
                        if st_val == "running":
                            return f'<span class="badge badge-run">⟳ {label}…</span>'
                        if st_val == "error":
                            return f'<span class="badge badge-err">❌ {label}</span>'
                        return f'<span class="badge badge-pending">○ {label}</span>'

                    audio_badge  = _badge(audio_st,  "Audio")
                    render_badge = _badge(render_st, "Render")

                    card_cls = "scene-card"
                    if audio_st == "error" or render_st == "error":
                        card_cls += " scene-card-err"
                    elif audio_st == "done" and render_st == "done":
                        card_cls += " scene-card-done"
                    elif audio_st == "running" or render_st == "running":
                        card_cls += " scene-card-active"

                    err_row = f'<div class="scene-err">{err_msg}</div>' if err_msg else ""
                    cards_html += f"""
<div class="{card_cls}">
  <div class="scene-title">Scene {i}</div>
  <div class="scene-badges">{audio_badge}{render_badge}</div>
  {err_row}
</div>"""

            stitch_row = ""
            if pipeline_stage == "stitching":
                stitch_row = '<div class="stitch-row">🔗 Stitching all scenes together…</div>'
            elif pipeline_stage == "done":
                stitch_row = '<div class="stitch-row stitch-done">✅ Stitching complete</div>'

            progress_placeholder.markdown(f"""
<style>
/* ── Progress widget styles ─────────────────────────────── */
.prog-wrap {{
  background: linear-gradient(160deg,#0b1018,#0f1720);
  border: 1px solid #2a3f57;
  border-radius: 14px;
  padding: 1.2rem 1.4rem 1rem;
  margin-top: 1.2rem;
}}
.stage-bar {{
  display: flex; gap: 6px; flex-wrap: wrap;
  margin-bottom: 1rem;
  padding-bottom: 0.8rem;
  border-bottom: 1px solid #1c2a3a;
}}
.stage-item {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11px; font-weight: 500;
  padding: 4px 12px; border-radius: 20px;
  display: flex; align-items: center; gap: 6px;
  letter-spacing: 0.4px;
}}
.stage-done    {{ background:rgba(46,164,79,0.12);  color:#4ade80; border:1px solid rgba(46,164,79,0.3); }}
.stage-active  {{ background:rgba(77,166,255,0.14); color:#6abcff; border:1px solid rgba(77,166,255,0.35);
                  animation: pulse-stage 1.6s ease-in-out infinite; }}
.stage-pending {{ background:rgba(255,255,255,0.03); color:#4a5e75; border:1px solid #1c2a3a; }}
@keyframes pulse-stage {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:0.6; }} }}
.stage-dot {{ font-size:10px; }}

.scenes-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
  margin-bottom: 0.8rem;
}}
.scene-card {{
  background: #0f1720;
  border: 1px solid #1c2a3a;
  border-radius: 10px;
  padding: 10px 12px;
  transition: border-color 0.3s;
}}
.scene-card-active {{
  border-color: rgba(77,166,255,0.45);
  box-shadow: 0 0 12px rgba(77,166,255,0.1);
}}
.scene-card-done {{
  border-color: rgba(46,164,79,0.4);
  box-shadow: 0 0 10px rgba(46,164,79,0.08);
}}
.scene-card-err  {{ border-color: rgba(240,82,82,0.4); }}
.scene-title {{
  font-family: 'Syne', sans-serif;
  font-size: 12px; font-weight: 700;
  color: #dde8f5; margin-bottom: 8px;
}}
.scene-badges {{ display:flex; flex-direction:column; gap:4px; }}
.badge {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 10px; font-weight: 500;
  padding: 2px 8px; border-radius: 20px;
  display: inline-block;
}}
.badge-done    {{ background:rgba(46,164,79,0.13);  color:#4ade80; border:1px solid rgba(46,164,79,0.3); }}
.badge-run     {{ background:rgba(77,166,255,0.12); color:#6abcff; border:1px solid rgba(77,166,255,0.3);
                  animation: pulse-stage 1.4s ease-in-out infinite; }}
.badge-err     {{ background:rgba(240,82,82,0.12);  color:#f87171; border:1px solid rgba(240,82,82,0.3); }}
.badge-pending {{ background:rgba(255,255,255,0.03); color:#4a5e75; border:1px solid #1c2a3a; }}
.scene-err  {{ font-family:'IBM Plex Mono',monospace; font-size:9.5px; color:#f87171; margin-top:4px; word-break:break-all; }}

.stitch-row {{
  font-family: 'IBM Plex Mono', monospace;
  font-size: 11.5px; color: #6abcff;
  padding: 8px 2px 0;
  border-top: 1px solid #1c2a3a;
  margin-top: 4px;
  animation: pulse-stage 1.6s ease-in-out infinite;
}}
.stitch-done {{
  color: #4ade80;
  animation: none;
}}
</style>
<div class="prog-wrap">
  <div class="stage-bar">{stage_html}</div>
  <div class="scenes-grid">{cards_html}</div>
  {stitch_row}
</div>
""", unsafe_allow_html=True)

        # ── Consume the event stream ────────────────────────────────────────
        try:
            payload = {
                "manim_code": final_manim,
                "script": final_script,
                "tts_provider": tts_custom,
                "resolution": resolution_custom.split(" ")[0],
            }
            with requests.post(backend_custom_url, json=payload, stream=True, timeout=None) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if not line:
                            continue
                        data = json.loads(line.decode("utf-8"))
                        evt  = data.get("type", "")

                        # ── pipeline_start ──────────────────────────────────
                        if evt == "pipeline_start":
                            n_scenes_total = data["n_scenes"]
                            pipeline_stage = "scenes"
                            for i in range(1, n_scenes_total + 1):
                                scene_states[i] = {"audio": "pending", "render": "pending", "error_msg": ""}
                            _render_progress()

                        # ── scene_start ─────────────────────────────────────
                        elif evt == "scene_start":
                            i = data["scene"]
                            if i in scene_states:
                                scene_states[i]["audio"]  = "running"
                                scene_states[i]["render"] = "pending"
                            _render_progress()

                        # ── scene_audio_done ────────────────────────────────
                        elif evt == "scene_audio_done":
                            i = data["scene"]
                            if i in scene_states:
                                scene_states[i]["audio"] = "done"
                            _render_progress()

                        # ── scene_render_start ──────────────────────────────
                        elif evt == "scene_render_start":
                            i = data["scene"]
                            if i in scene_states:
                                scene_states[i]["render"] = "running"
                            _render_progress()


                        # ── scene_render_done ───────────────────────────────
                        elif evt == "scene_render_done":
                            i = data["scene"]
                            if i in scene_states:
                                scene_states[i]["render"] = "done"
                            _render_progress()

                        # ── scene_error ─────────────────────────────────────
                        elif evt == "scene_error":
                            i = data["scene"]
                            stage = data.get("stage", "")
                            if i in scene_states:
                                scene_states[i][stage]      = "error"
                                scene_states[i]["error_msg"] = data.get("msg", "")[:80]
                            _render_progress()

                        # ── stitch_start ────────────────────────────────────
                        elif evt == "stitch_start":
                            pipeline_stage = "stitching"
                            _render_progress()

                        # ── stitch_fallback ─────────────────────────────────
                        elif evt == "stitch_fallback":
                            # Just a warning — keep stage as stitching
                            _render_progress()

                        # ── done ────────────────────────────────────────────
                        elif evt == "done":
                            pipeline_stage = "done"
                            _render_progress()

                        # ── error (pipeline-level) ───────────────────────────
                        elif evt == "error":
                            error_placeholder.error(
                                f"❌ Pipeline error in **{data.get('node', 'unknown')}**: {data.get('msg', '')}"
                            )
                            break

                        # ── legacy final_video signal ────────────────────────
                        elif "final_video" in data:
                            video_path = data["final_video"]
                            st.session_state.final_video = video_path
                            st.markdown(f"""
<div style="margin-top:1.2rem;padding:1rem 1.4rem;background:rgba(46,164,79,0.08);
     border:1px solid rgba(46,164,79,0.3);border-radius:12px;
     font-family:'IBM Plex Mono',monospace;font-size:12px;color:#4ade80;">
  ✅&nbsp;&nbsp;Video ready<br>
  <span style="color:#8da0b8;font-size:10.5px;">{video_path}</span>
</div>""", unsafe_allow_html=True)
                            break

                elif response.status_code == 409:
                    st.warning("⏳ A video is already being generated. Please wait for it to finish.")
                else:
                    st.error(f"⚠️ Backend returned status {response.status_code}")

        except Exception as e:
            st.error(f"🔌 Connection error: {e}")


# ─── Video Output ───────────────────────────────────────────────────────────
if st.session_state.final_video and os.path.exists(st.session_state.final_video):
    st.markdown('<p class="section-label" style="margin-top:1.6rem">Output</p>', unsafe_allow_html=True)

    st.video(st.session_state.final_video)

    with open(st.session_state.final_video, "rb") as file:
        st.download_button(
            label="⬇ Download Video",
            data=file,
            file_name="custom_video.mp4",
            mime="video/mp4",
        )

    # ── SEO Panel ──────────────────────────────────────────────────────────
    st.markdown("""
<div class="seo-panel">
    <div class="seo-title">🚀 Generate SEO Metadata</div>
    <div class="seo-sub">Let Claude Opus craft high-retention YouTube titles &amp; descriptions for your video.</div>
</div>
""", unsafe_allow_html=True)

    if st.button("✦ Generate Title & Description", key="seo_btn"):
        with st.spinner("Claude Opus is crafting your metadata…"):
            seo_url = f"{backend_base}/generate-seo"
            try:
                resp = requests.post(seo_url, json={
                    "manim_code": manim_code.strip(),
                    "script": script_text.strip(),
                })
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.seo_title = data.get("title", "")
                    st.session_state.seo_desc  = data.get("description", "")
                else:
                    st.error(f"SEO generation failed: {resp.text}")
            except Exception as e:
                st.error(f"Network error: {e}")

    if st.session_state.seo_title or st.session_state.seo_desc:
        st.text_input("🏷️ Generated YouTube Title", value=st.session_state.seo_title)
        st.text_area("📝 Generated YouTube Description", value=st.session_state.seo_desc, height=220)


# ─── Footer ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div class="footer-bar">
    Built with &nbsp;<span>LangGraph</span> · <span>Manim</span> · <span>FastAPI</span> · <span>Streamlit</span>
</div>
""", unsafe_allow_html=True)