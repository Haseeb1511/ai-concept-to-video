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

if "final_video" not in st.session_state:
    st.session_state.final_video = None
if "seo_title" not in st.session_state:
    st.session_state.seo_title = ""
if "seo_desc" not in st.session_state:
    st.session_state.seo_desc = ""

# --- Custom Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fix Streamlit Material Icons rendering as text ligatures */
    .material-symbols-rounded, 
    .material-icons, 
    [data-testid="stIconMaterial"], 
    [class*="Icon"] {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif !important;
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
    
    /* ── Activity Feed Log Panel ───────────────────────── */
    .activity-feed {
        background: linear-gradient(145deg, #0d1117, #111827);
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 0;
        overflow: hidden;
        margin-top: 20px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03);
    }

    .feed-header {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 12px 16px;
        background: rgba(22, 27, 34, 0.8);
        border-bottom: 1px solid #21262d;
        backdrop-filter: blur(8px);
    }

    .feed-title {
        font-size: 12px;
        font-weight: 600;
        color: #8b949e;
        letter-spacing: 0.6px;
        text-transform: uppercase;
        flex: 1;
    }

    .feed-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #2ea043;
        box-shadow: 0 0 6px #2ea043;
        animation: pulse-dot 1.5s ease-in-out infinite;
    }

    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    .feed-body {
        padding: 12px 16px;
        max-height: 280px;
        overflow-y: auto;
        scrollbar-width: thin;
        scrollbar-color: #30363d transparent;
    }

    .feed-body::-webkit-scrollbar { width: 4px; }
    .feed-body::-webkit-scrollbar-track { background: transparent; }
    .feed-body::-webkit-scrollbar-thumb { background: #30363d; border-radius: 2px; }

    .feed-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 7px 0;
        border-bottom: 1px solid rgba(33,38,45,0.6);
        animation: slide-in 0.25s ease;
        font-size: 13px;
        line-height: 1.4;
    }

    .feed-item:last-child { border-bottom: none; }

    @keyframes slide-in {
        from { opacity: 0; transform: translateY(-4px); }
        to   { opacity: 1; transform: translateY(0); }
    }

    .feed-icon {
        font-size: 15px;
        flex-shrink: 0;
        margin-top: 1px;
    }

    .feed-time {
        font-size: 11px;
        color: #484f58;
        flex-shrink: 0;
        font-family: 'JetBrains Mono', monospace;
        margin-top: 2px;
    }

    .feed-text {
        flex: 1;
        color: #c9d1d9;
    }

    .feed-pill {
        font-size: 10px;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 20px;
        flex-shrink: 0;
        letter-spacing: 0.4px;
        margin-top: 2px;
    }

    /* Pill variants */
    .pill-info     { background: rgba(88,166,255,0.15);  color: #58a6ff;  border: 1px solid rgba(88,166,255,0.25); }
    .pill-audio    { background: rgba(163,113,247,0.15); color: #a371f7;  border: 1px solid rgba(163,113,247,0.25); }
    .pill-render   { background: rgba(56,189,248,0.15);  color: #38bdf8;  border: 1px solid rgba(56,189,248,0.25); }
    .pill-agent    { background: rgba(251,191,36,0.15);  color: #fbbf24;  border: 1px solid rgba(251,191,36,0.25); }
    .pill-warning  { background: rgba(249,115,22,0.15);  color: #f97316;  border: 1px solid rgba(249,115,22,0.25); }
    .pill-success  { background: rgba(46,164,67,0.15);   color: #3fb950;  border: 1px solid rgba(46,164,67,0.25); }
    .pill-error    { background: rgba(248,81,73,0.15);   color: #f85149;  border: 1px solid rgba(248,81,73,0.25); }
    .pill-assembly { background: rgba(52,211,153,0.15);  color: #34d399;  border: 1px solid rgba(52,211,153,0.25); }

    /* Sidebar Tool Showcase */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #21262d;
    }

    .sidebar-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #e6edf3;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid #30363d;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .tool-category {
        font-size: 0.8rem;
        font-weight: 600;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 20px 0 10px 0;
    }

    .tool-card {
        background: rgba(22, 27, 34, 0.5);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
        cursor: default;
    }

    .tool-card:hover {
        border-color: #58a6ff;
        background: rgba(88, 166, 255, 0.05);
        transform: translateX(4px);
    }

    .tool-name {
        font-size: 0.9rem;
        font-weight: 600;
        color: #58a6ff;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .tool-desc {
        font-size: 0.75rem;
        color: #8b949e;
        line-height: 1.4;
    }

    .category-icon {
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar: Project Tools Showcase ---
with st.sidebar:
    st.markdown("""
        <div class="sidebar-header">
            <span class="category-icon">🛠️</span> Available Tools
        </div>
    """, unsafe_allow_html=True)

    tools_data = {
        "YouTube Ops": [
            {"icon": "📺", "name": "list_my_videos", "desc": "Retrieve recent uploads from your channel."},
            {"icon": "📊", "name": "get_video_stats", "desc": "Fetch views, likes, and engagement metrics."},
            {"icon": "🔍", "name": "search_youtube", "desc": "Find reference material via YouTube Data API."}
        ],
        "Knowledge Base": [
            {"icon": "📚", "name": "search_manim_docs", "desc": "Deep search Manim Community documentation."},
            {"icon": "📄", "name": "read_doc_page", "desc": "Extract technical syntax from web docs."}
        ],
        "Automation": [
            {"icon": "⚡", "name": "execute_manim", "desc": "Compile and preview Manim scenes in real-time."},
            {"icon": "🧹", "name": "cleanup_temp", "desc": "Maintain workspace hygiene (temp files)."}
        ],
        "Media Assets": [
            {"icon": "🖼️", "name": "search_image", "desc": "Find relevant visuals for video concept."},
            {"icon": "📥", "name": "download_image", "desc": "Asset acquisition for the production pipeline."}
        ]
    }

    for category, items in tools_data.items():
        st.markdown(f'<div class="tool-category">{category}</div>', unsafe_allow_html=True)
        for tool in items:
            st.markdown(f"""
                <div class="tool-card">
                    <div class="tool-name">
                        <span>{tool['icon']}</span>
                        <span>{tool['name']}</span>
                    </div>
                    <div class="tool-desc">{tool['desc']}</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#484f58; font-size:11px; text-align:center;">MCP Agent · Version 1.0.4</p>', unsafe_allow_html=True)

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
            with requests.post(backend_custom_url, json=payload, stream=True, timeout=None) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            data = json.loads(line.decode("utf-8"))
                            
                            if "log" in data:
                                log_history.append(data["log"])

                                def _classify(log_text):
                                    lt = log_text.upper()
                                    if any(k in lt for k in ["AGENT", "AI AGENT", "LANGGRAPH", "FIXING", "RESEARCHING"]):
                                        return ("🤖", "Agent",    "pill-agent")
                                    if any(k in lt for k in ["AUDIO", "SYNTHESIS", "TTS"]):
                                        return ("🎙️", "Audio",    "pill-audio")
                                    if any(k in lt for k in ["RENDER", "MANIM", "SCENE"]):
                                        return ("🎬", "Render",   "pill-render")
                                    if any(k in lt for k in ["STITCH", "ASSEMBLY", "MERGE"]):
                                        return ("🔗", "Assembly",  "pill-assembly")
                                    if any(k in lt for k in ["FALLBACK", "RETRY", "WARNING"]):
                                        return ("⚠️", "Fallback",  "pill-warning")
                                    if any(k in lt for k in ["DONE", "COMPLETE", "✅", "READY", "VIDEO SAVED"]):
                                        return ("✅", "Done",     "pill-success")
                                    if any(k in lt for k in ["ERROR", "FAILED", "ABORT", "CRITICAL", "❌"]):
                                        return ("❌", "Error",    "pill-error")
                                    return ("ℹ️", "Info",         "pill-info")

                                def _extract_time(log_text):
                                    import re
                                    m = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", log_text)
                                    return m.group(1) if m else ""

                                def _extract_message(log_text):
                                    # Strip the icon + [time] + label + arrow prefix
                                    import re
                                    cleaned = re.sub(r"^[^\w\[]*", "", log_text)         # leading emojis
                                    cleaned = re.sub(r"\[\d{2}:\d{2}:\d{2}\]\s*", "", cleaned)  # [HH:MM:SS]
                                    cleaned = re.sub(r"^[A-Za-z ]+\s*→\s*", "", cleaned)        # label → 
                                    return cleaned.strip() or log_text.strip()

                                items_html = ""
                                for l in log_history[-18:]:
                                    icon, label, pill = _classify(l)
                                    t = _extract_time(l)
                                    msg = _extract_message(l)
                                    items_html += f"""
<div class="feed-item">
    <span class="feed-icon">{icon}</span>
    <span class="feed-text">{msg}</span>
    <span class="feed-time">{t}</span>
    <span class="feed-pill {pill}">{label}</span>
</div>"""

                                log_container.markdown(f"""
<div class="activity-feed">
    <div class="feed-header">
        <span class="feed-dot"></span>
        <span class="feed-title">Live Activity</span>
        <span style="font-size:11px;color:#484f58">{len(log_history)} events</span>
    </div>
    <div class="feed-body">
        {items_html}
    </div>
</div>
""", unsafe_allow_html=True)

                            if "error" in data:
                                st.error(f"❌ Generation failed in **{data.get('failed_node', 'Pipeline')}**: {data['error']}")
                                break

                            if "final_video" in data:
                                video_path = data["final_video"]
                                st.session_state.final_video = video_path
                                st.success("🎉 Your video is ready!")
                                break
                elif response.status_code == 409:
                    st.warning("⏳ A video is already being generated. Please wait for it to finish.")
                else:
                    st.error(f"⚠️ Backend returned an error: {response.status_code}")

        except Exception as e:
            st.error(f"🔌 Connection error: {e}")

if st.session_state.final_video and os.path.exists(st.session_state.final_video):
    # Display the final video robustly outside button condition
    st.video(st.session_state.final_video)
    with open(st.session_state.final_video, "rb") as file:
        st.download_button(
            label="⬇️ Download Video",
            data=file,
            file_name="custom_video.mp4",
            mime="video/mp4"
        )
    
    st.markdown("---")
    st.markdown("### 🚀 Generate SEO Meta (Optional)")
    st.markdown('<p style="color:#8b949e; font-size:14px; margin-top:-10px;">Use our expert AI persona (Claude Opus) to generate high-retention titles and descriptions.</p>', unsafe_allow_html=True)
    
    # We clear SEO results if they generate a new video
    if st.button("✨ Generate Title & Description"):
        with st.spinner("Claude Opus is crafting your metadata..."):
            seo_url = f"{backend_base}/generate-seo"
            try:
                resp = requests.post(seo_url, json={"manim_code": manim_code.strip(), "script": script_text.strip()})
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.seo_title = data.get("title", "")
                    st.session_state.seo_desc = data.get("description", "")
                else:
                    st.error(f"Failed to generate SEO. Error: {resp.text}")
            except Exception as e:
                st.error(f"Network error calling SEO generator: {e}")

    if st.session_state.seo_title or st.session_state.seo_desc:
        st.text_input("🏷️ Generated YouTube Title", value=st.session_state.seo_title)
        st.text_area("📝 Generated YouTube Description", value=st.session_state.seo_desc, height=220)

# --- Footer ---
st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#484f58; font-size:12px;">Built with LangGraph · Manim · FastAPI · Streamlit</p>',
    unsafe_allow_html=True
)
