import streamlit as st
import requests
import os
import json
from pathlib import Path

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Video Generator",
    page_icon="🎬",
    layout="centered",
)

# --- Custom Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Base Backgrounds and Text */
    .stApp, .main {
        background-color: #0d1117;
        color: #8b949e;
    }
    
    h1, h2, h3, h4, h5, h6, .stMarkdown p {
        color: #8b949e;
    }
    
    /* Gradient Hero Heading */
    .hero-heading {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #58a6ff, #a371f7, #79c0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }

    /* Sub Heading */
    .sub-heading {
        font-size: 1rem;
        color: #8b949e;
        margin-top: -0.25rem;
        margin-bottom: 1.5rem;
    }

    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #161b22;
        border-radius: 10px;
        padding: 4px;
        border: 1px solid #21262d;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #8b949e;
        font-weight: 500;
        padding: 8px 20px;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #1c2a3a, #1f2a40) !important;
        color: #58a6ff !important;
        border: 1px solid #30363d;
    }

    /* Elevated Cards / Containers */
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] {
        background-color: #161b22;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: box-shadow 0.3s ease;
    }
    
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"]:hover {
        box-shadow: 0 0 15px rgba(88, 166, 255, 0.15);
    }
    
    /* Inputs */
    .stTextInput>div>div>input, div[data-baseweb="select"] > div {
        background-color: #0d1117;
        color: #e6edf3;
        border: 1px solid #21262d;
        border-radius: 8px;
        font-size: 14px;
    }

    .stTextArea>div>div>textarea {
        background-color: #0d1117 !important;
        color: #e6edf3 !important;
        border: 1px solid #21262d !important;
        border-radius: 8px !important;
        font-size: 13px !important;
        font-family: 'JetBrains Mono', 'Courier New', monospace !important;
        line-height: 1.6 !important;
    }

    .stTextArea>div>div>textarea:focus {
        border-color: #58a6ff !important;
        box-shadow: 0 0 0 1px #58a6ff !important;
    }
    
    .stTextInput>div>div>input:focus, div[data-baseweb="select"] > div:focus-within {
        border-color: #58a6ff;
        box-shadow: 0 0 0 1px #58a6ff;
    }

    /* Primary CTA Button */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        background: linear-gradient(90deg, #58a6ff, #3182ce);
        border: none;
        color: #ffffff;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(88, 166, 255, 0.4);
        border: none;
        color: #ffffff;
    }

    /* Custom tab button - Purple gradient */
    .custom-generate-btn button {
        background: linear-gradient(90deg, #a371f7, #7c3aed) !important;
    }
    .custom-generate-btn button:hover {
        box-shadow: 0 4px 12px rgba(163, 113, 247, 0.4) !important;
    }
    
    /* Alerts / Pill Badges approximation */
    .stAlert {
        border-radius: 8px;
        border: 1px solid rgba(163, 113, 247, 0.3);
        background-color: rgba(163, 113, 247, 0.05);
    }

    /* Code hint box */
    .code-hint {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 3px solid #58a6ff;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 12px;
        color: #8b949e;
        margin-bottom: 16px;
        font-family: 'JetBrains Mono', monospace;
    }

    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
        margin-left: 8px;
        vertical-align: middle;
    }
    .badge-blue  { background: rgba(88,166,255,0.15); color: #58a6ff; border: 1px solid rgba(88,166,255,0.3); }
    
    /* Tactical Terminal / Military Logs */
    .tactical-terminal {
        background-color: #050505;
        border: 2px solid #1a1a1a;
        border-top: 20px solid #1a1a1a;
        border-radius: 4px;
        padding: 15px;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 13px;
        color: #00ff41; /* Classic Matrix/Terminal Green */
        height: 300px;
        overflow-y: auto;
        box-shadow: inset 0 0 10px #000;
        margin-top: 20px;
        position: relative;
    }

    .tactical-terminal::before {
        content: "AGENTIC TACTICAL FEED";
        position: absolute;
        top: -18px;
        left: 10px;
        font-size: 10px;
        font-weight: 800;
        color: #8b949e;
    }

    .log-line {
        margin: 0;
        padding: 2px 0;
        line-height: 1.4;
        text-shadow: 0 0 2px rgba(0, 255, 65, 0.5);
    }

    /* Agentic log line colors */
    .log-line.agent  { color: #00d4ff; text-shadow: 0 0 4px rgba(0, 212, 255, 0.6); }
    .log-line.error  { color: #ff4444; text-shadow: 0 0 4px rgba(255, 68, 68, 0.6); }
    .log-line.fallback { color: #ff9f43; text-shadow: 0 0 4px rgba(255, 159, 67, 0.6); }
    .log-line.retry  { color: #ffd32a; text-shadow: 0 0 4px rgba(255, 211, 42, 0.6); }
    .log-line.critical { color: #ff6b6b; text-shadow: 0 0 6px rgba(255, 107, 107, 0.8); font-weight: bold; }
    .log-line.complete { color: #2ed573; text-shadow: 0 0 6px rgba(46, 213, 115, 0.8); font-weight: bold; }
    
    /* Scanline effect */
    .tactical-terminal::after {
        content: "";
        position: absolute;
        top: 0; left: 0; bottom: 0; right: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.1) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
        background-size: 100% 3px, 3px 100%;
        pointer-events: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.markdown('<h1 class="hero-heading">🎬 AI Video Generator</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-heading">Generate short educational videos powered by LangGraph, Manim & FastAPI.</p>',
    unsafe_allow_html=True
)

# ─── Shared backend URL ────────────────────────────────────────────────────
backend_base = "http://127.0.0.1:8000"

# ─── Main Interface ────────────────────────────────────────────────────────
st.markdown(
    '<p style="color:#8b949e; margin-bottom:4px;">Paste your own <strong style="color:#58a6ff">Manim code</strong> '
    'and <strong style="color:#a371f7">narration script</strong>. '
    'The pipeline will map the script onto the animation and stitch the final video.</p>',
    unsafe_allow_html=True
)

st.markdown("""
<div class="code-hint">
💡 <strong>Tips for your Manim code:</strong><br>
&nbsp;• Your scene class <strong>MUST</strong> be named <code>RenderScene(Scene)</code><br>
&nbsp;• Do <strong>not</strong> include <code>from manim import *</code> — it's added automatically<br>
&nbsp;• Access narration & timing via: <code>data = json.loads(os.environ["SCENE_DATA"])</code><br>
&nbsp;&nbsp;&nbsp;→ <code>data["text"]</code>, <code>data["duration"]</code>, <code>data["scene_id"]</code><br>
&nbsp;• Script is split into scenes by <strong>blank lines</strong> (double Enter) between paragraphs
</div>
""", unsafe_allow_html=True)

# ── Auto-load from disk
_base = Path(__file__).parent.parent / "custom"
_manim_file  = _base / "manim"
_script_file = _base / "script"
_default_manim  = _manim_file.read_text(encoding="utf-8")  if _manim_file.exists()  else ""
_default_script = _script_file.read_text(encoding="utf-8") if _script_file.exists() else ""

with st.container():
    manim_code = st.text_area(
        "🎨 Manim Code",
        value=_default_manim,
        placeholder="""class RenderScene(Scene):
    def construct(self):
        data = json.loads(os.environ["SCENE_DATA"])
        title = Text(data["text"], font_size=36)
        self.play(Write(title))
        self.wait(data["duration"] - 2)""",
        height=320,
        key="custom_manim_code",
    )

    script_text = st.text_area(
        "📝 Narration Script",
        value=_default_script,
        placeholder="Separate each scene with a blank line.\n\nScene 1: Welcome to this tutorial.\n\nScene 2: ...",
        height=200,
        key="custom_script",
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        tts_custom = st.selectbox(
            "TTS Provider:",
            options=["openai", "elevenlabs", "gtts", "coqui"],
            index=0,
            key="custom_tts"
        )
    with col2:
        backend_custom_url = st.text_input(
            "Backend URL:",
            value=f"{backend_base}/generate-custom-video",
            key="custom_backend_url"
        )

    st.markdown('<div class="custom-generate-btn">', unsafe_allow_html=True)
    custom_generate_btn = st.button("✨ Generate Custom Video", key="custom_generate")
    st.markdown('</div>', unsafe_allow_html=True)

if custom_generate_btn:
    if not manim_code.strip():
        st.error("Please paste your Manim code!")
    elif not script_text.strip():
        st.error("Please paste your narration script!")
    else:
        log_container = st.empty()
        log_history = []

        try:
            payload = {
                "manim_code": manim_code.strip(),
                "script": script_text.strip(),
                "tts_provider": tts_custom,
            }
            # Use stream=True for real-time tactical feedback
            with requests.post(backend_custom_url, json=payload, stream=True, timeout=600) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode("utf-8"))
                            
                            # Log handling — color-code agentic categories
                            if "log" in data:
                                log_history.append(data["log"])
                                def _log_css_class(log_text):
                                    lt = log_text.upper()
                                    if ">> AGENT:" in lt:   return "log-line agent"
                                    if ">> ERROR:" in lt:   return "log-line error"
                                    if ">> FALLBACK:" in lt: return "log-line fallback"
                                    if ">> RETRY:" in lt:   return "log-line retry"
                                    if ">> CRITICAL:" in lt: return "log-line critical"
                                    if ">> COMPLETE:" in lt: return "log-line complete"
                                    return "log-line"
                                display_logs = "".join([f'<p class="{_log_css_class(l)}">{l}</p>' for l in log_history[-20:]])
                                log_container.markdown(f"""
                                    <div class="tactical-terminal">
                                        {display_logs}
                                    </div>
                                """, unsafe_allow_html=True)

                            # Error handling
                            if "error" in data:
                                st.error(f"Tactical Failure in **{data.get('failed_node', 'Pipeline')}**: {data['error']}")
                                break

                            # Final result
                            if "final_video" in data:
                                video_path = data["final_video"]
                                st.success("✅ Custom Video Mission Complete!")
                                if os.path.exists(video_path):
                                    st.video(video_path)
                                    with open(video_path, "rb") as file:
                                        st.download_button(
                                            label="⬇️ Download Custom Asset",
                                            data=file,
                                            file_name="custom_video.mp4",
                                            mime="video/mp4"
                                        )
                                break
                elif response.status_code == 409:
                    st.warning("⏳ Tactical Warning: A generation is already in progress.")
                else:
                    st.error(f"Backend Link Offline: {response.status_code}")

        except Exception as e:
            st.error(f"Critical Protocol Error: {e}")

# --- Footer ---
st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#484f58; font-size:12px;">Built with LangGraph · Manim · FastAPI · Streamlit</p>',
    unsafe_allow_html=True
)
