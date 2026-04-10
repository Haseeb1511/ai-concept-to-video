import streamlit as st
import requests
import json
import uuid
import time

# ─── Session State Init ────────────────────────────────────────────────────────
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []          # [{role, content, tool_calls}]
if "chat_thread_id" not in st.session_state:
    st.session_state.chat_thread_id = str(uuid.uuid4())
if "chat_thinking" not in st.session_state:
    st.session_state.chat_thinking = False

BACKEND_BASE = "http://127.0.0.1:8000"

# Page config is handled in app.py

# ─── Styling ───────────────────────────────────────────────────────────────────
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
    --border:     #1c2a3a;
    --border-lit: #2a3f57;
    --blue:       #4da6ff;
    --purple:     #9d6fff;
    --teal:       #2fd4a7;
    --amber:      #f5a623;
    --red:        #f05252;
    --green:      #2ea04f;
    --text-primary: #dde8f5;
    --text-body:    #8da0b8;
    --text-muted:   #4a5e75;
    --text-dim:     #2c3d52;
}

/* ── Global Font & Background ─────────────────────────── */
html, body, .stApp {
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg-void) !important;
    color: var(--text-body) !important;
}

/* Specific text elements for custom font */
.stMarkdown, .stText, .stButton, .stTextArea, .stTextInput, .stSelectbox, label, p, div {
    font-family: 'Outfit', sans-serif;
}

/* Subtle scanline texture */
.stApp::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: repeating-linear-gradient(
        0deg, transparent, transparent 2px,
        rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px
    );
    pointer-events: none;
    z-index: 9999;
}

.main .block-container {
    max-width: 840px !important;
    padding: 2rem 2rem 4rem !important;
    margin: 0 auto;
}

/* ── Hero Banner ───────────────────────────────────────── */
.chat-hero {
    position: relative;
    padding: 3rem 2rem 2.6rem;
    margin-bottom: 1.6rem;
    border-radius: 20px;
    background:
        radial-gradient(ellipse 70% 60% at 50% -10%, rgba(157,111,255,0.12), transparent),
        radial-gradient(ellipse 50% 40% at 85% 110%, rgba(77,166,255,0.10), transparent),
        linear-gradient(160deg, #0f1320 0%, #0b1018 60%, #111a24 100%);
    border: 1px solid var(--border-lit);
    text-align: center;
    overflow: hidden;
}

.chat-hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
        radial-gradient(circle at 25% 75%, rgba(157,111,255,0.06) 0%, transparent 50%),
        radial-gradient(circle at 75% 25%, rgba(77,166,255,0.06) 0%, transparent 50%);
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
    color: var(--purple);
    background: rgba(157,111,255,0.08);
    border: 1px solid rgba(157,111,255,0.22);
    padding: 5px 14px;
    border-radius: 30px;
    margin-bottom: 1.2rem;
}

.hero-eyebrow-dot {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--purple);
    box-shadow: 0 0 6px var(--purple);
    animation: blink 2s ease-in-out infinite;
}

@keyframes blink {
    0%,100% { opacity:1; }
    50% { opacity:0.2; }
}

.chat-hero-title {
    font-family: 'Syne', sans-serif !important;
    font-size: clamp(2.2rem, 4.5vw, 3.4rem) !important;
    font-weight: 800 !important;
    line-height: 1.1 !important;
    letter-spacing: -1px !important;
    background: linear-gradient(135deg, #c6deff 0%, #9d6fff 40%, #4da6ff 75%, #c6deff 100%);
    background-size: 200% auto;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
    animation: shimmer 5s linear infinite;
    margin-bottom: 0.6rem !important;
}

@keyframes shimmer {
    0%   { background-position: 0% center; }
    100% { background-position: 200% center; }
}

.chat-hero-sub {
    font-size: 0.98rem;
    color: var(--text-body);
    font-weight: 400;
    letter-spacing: 0.2px;
    margin-bottom: 1.6rem;
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
.chip-blue   { background: rgba(77,166,255,0.10);  color:#6abcff;  border:1px solid rgba(77,166,255,0.22); }
.chip-purple { background: rgba(157,111,255,0.10); color:#b48dff;  border:1px solid rgba(157,111,255,0.22); }
.chip-teal   { background: rgba(47,212,167,0.10);  color:#4de0c0;  border:1px solid rgba(47,212,167,0.22); }
.chip-green  { background: rgba(46,160,67,0.10);   color:#4ade80;  border:1px solid rgba(46,160,67,0.22); }

/* ── Status Badge ──────────────────────────────────────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    background: rgba(46,160,67,0.08);
    border: 1px solid rgba(46,160,67,0.25);
    border-radius: 30px;
    padding: 5px 14px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #4ade80;
    margin-bottom: 1.4rem;
}

.status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #4ade80;
    box-shadow: 0 0 6px #4ade80;
    animation: pulse-green 1.8s ease-in-out infinite;
}

@keyframes pulse-green {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.4; transform:scale(0.8); }
}

/* ── Section Label ─────────────────────────────────────── */
.section-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 0.7rem;
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

/* ── Quick Prompt Chips ────────────────────────────────── */
.chip-row-wrap {
    margin-bottom: 1.4rem;
}

/* Make quick-prompt buttons look like chips */
.chip-row-wrap .stButton > button {
    height: auto !important;
    padding: 6px 13px !important;
    font-size: 11.5px !important;
    font-weight: 500 !important;
    border-radius: 30px !important;
    background: rgba(77,166,255,0.06) !important;
    border: 1px solid rgba(77,166,255,0.2) !important;
    color: #6abcff !important;
    letter-spacing: 0.3px;
    transition: all 0.2s ease !important;
    white-space: nowrap;
    box-shadow: none !important;
}

.chip-row-wrap .stButton > button:hover {
    background: rgba(77,166,255,0.14) !important;
    border-color: rgba(77,166,255,0.45) !important;
    color: #a8d8ff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(77,166,255,0.15) !important;
}

/* ── Chat Messages ─────────────────────────────────────── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border-radius: 14px !important;
    margin-bottom: 4px !important;
    padding: 14px !important;
    transition: background 0.2s ease;
}

[data-testid="stChatMessage"][data-role="user"] {
    background: rgba(77,166,255,0.05) !important;
    border: 1px solid rgba(77,166,255,0.1) !important;
}

[data-testid="stChatMessage"][data-role="assistant"] {
    background: rgba(157,111,255,0.04) !important;
    border: 1px solid rgba(157,111,255,0.09) !important;
}

[data-testid="stChatMessage"] p {
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.7 !important;
    color: var(--text-primary) !important;
}

[data-testid="stChatMessage"] code {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 12px !important;
    background: rgba(77,166,255,0.1) !important;
    color: var(--blue) !important;
    padding: 2px 6px !important;
    border-radius: 4px !important;
}

/* ── Tool Call Banner ──────────────────────────────────── */
.tool-banner {
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(245,166,35,0.06);
    border: 1px solid rgba(245,166,35,0.2);
    border-left: 3px solid rgba(245,166,35,0.5);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 8px 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 11.5px;
    color: #ffc050;
    animation: feed-in 0.3s cubic-bezier(0.4,0,0.2,1);
}

.tool-banner strong {
    color: #ffd280;
}

.tool-spinner {
    width: 13px; height: 13px;
    border: 2px solid rgba(245,166,35,0.25);
    border-top-color: #f5a623;
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

@keyframes feed-in {
    from { opacity:0; transform:translateX(-6px); }
    to   { opacity:1; transform:translateX(0); }
}

/* ── Chat Input ────────────────────────────────────────── */
[data-testid="stChatInput"] textarea {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border-lit) !important;
    border-radius: 14px !important;
    color: var(--text-primary) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    caret-color: var(--purple) !important;
}

[data-testid="stChatInput"] textarea:focus {
    border-color: var(--purple) !important;
    box-shadow: 0 0 0 2px rgba(157,111,255,0.14) !important;
    outline: none !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-muted) !important;
}

[data-testid="stChatInput"] button {
    background: linear-gradient(135deg, #6940c0, #4c2a9e) !important;
    border-radius: 10px !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4) !important;
    transition: all 0.2s ease !important;
}

[data-testid="stChatInput"] button:hover {
    background: linear-gradient(135deg, #7a4fd6, #5c36b4) !important;
    box-shadow: 0 4px 14px rgba(157,111,255,0.35) !important;
    transform: scale(1.06) !important;
}

/* ── General Buttons ───────────────────────────────────── */
.stButton > button {
    width: 100% !important;
    height: 2.8rem !important;
    border-radius: 10px !important;
    border: 1px solid var(--border-lit) !important;
    background: rgba(20,30,43,0.8) !important;
    color: var(--text-body) !important;
    font-family: 'Outfit', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}

.stButton > button:hover {
    border-color: var(--blue) !important;
    color: var(--blue) !important;
    background: rgba(77,166,255,0.05) !important;
    transform: translateY(-1px) !important;
}

/* ── Sidebar ───────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--bg-base) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

.sidebar-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.2rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

.sidebar-section {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 9.5px;
    font-weight: 500;
    color: var(--text-muted);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin: 1.4rem 0 0.7rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

.sidebar-section::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
}

/* ── Thread ID ─────────────────────────────────────────── */
.thread-info {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10px;
    color: var(--text-dim);
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 10px;
    margin-top: 8px;
    word-break: break-all;
    line-height: 1.5;
}

.thread-label {
    font-size: 9px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 4px;
}

/* ── Empty State ───────────────────────────────────────── */
.empty-state {
    text-align: center;
    padding: 56px 0;
}

.empty-icon {
    font-size: 3.2rem;
    margin-bottom: 16px;
    filter: drop-shadow(0 0 20px rgba(157,111,255,0.4));
    animation: float 3s ease-in-out infinite;
}

@keyframes float {
    0%,100% { transform: translateY(0); }
    50%      { transform: translateY(-8px); }
}

.empty-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--text-body);
    margin-bottom: 8px;
}

.empty-sub {
    font-size: 13px;
    color: var(--text-muted);
    line-height: 1.6;
    max-width: 380px;
    margin: 0 auto;
}

/* ── Alerts ────────────────────────────────────────────── */
div[data-testid="stError"] {
    background: rgba(240,82,82,0.07) !important;
    border: 1px solid rgba(240,82,82,0.25) !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
}

/* ── Divider ───────────────────────────────────────────── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.6rem 0 !important;
}

/* ── Footer ────────────────────────────────────────────── */
.footer-bar {
    text-align: center;
    padding: 1rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 10.5px;
    letter-spacing: 1px;
    color: var(--text-dim);
}
.footer-bar span { color: var(--text-muted); }

</style>
""", unsafe_allow_html=True)


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        📡 Channel Assistant
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Conversation</div>', unsafe_allow_html=True)

    if st.button("✦ New Conversation", use_container_width=True):
        st.session_state.chat_messages = []
        st.session_state.chat_thread_id = str(uuid.uuid4())
        st.rerun()

    st.markdown(f"""
    <div class="thread-info">
        <div class="thread-label">Thread ID</div>
        {st.session_state.chat_thread_id[:28]}…
    </div>
    """, unsafe_allow_html=True)


# ─── Hero Banner ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="chat-hero">
    <div class="hero-eyebrow">
        <span class="hero-eyebrow-dot"></span>
        Channel Intelligence
    </div>
    <div class="chat-hero-title">💬 Channel Intelligence</div>
    <p class="chat-hero-sub">Chat with your YouTube channel — get insights on views, trends &amp; performance.</p>
    <div class="hero-tags">
        <span class="tech-chip chip-purple">LangGraph Agent</span>
        <span class="tech-chip chip-blue">YouTube API</span>
        <span class="tech-chip chip-teal">Streaming</span>
        <span class="tech-chip chip-green">Live Data</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Status badge ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="status-badge">
    <span class="status-dot"></span>
    Agent Online
</div>
""", unsafe_allow_html=True)


# ─── Quick Prompt Chips ─────────────────────────────────────────────────────────
QUICK_PROMPTS = [
    "📋 List my recent videos",
    "📈 Most viewed video?",
    "🔥 Trending topics in my niche",
    "💡 Content ideas for my channel",
    "📊 Channel performance overview",
]

st.markdown('<p class="section-label">Quick Prompts</p>', unsafe_allow_html=True)
st.markdown('<div class="chip-row-wrap">', unsafe_allow_html=True)
cols = st.columns(len(QUICK_PROMPTS))
for i, prompt in enumerate(QUICK_PROMPTS):
    with cols[i]:
        if st.button(prompt, key=f"chip_{i}", use_container_width=True):
            st.session_state["_pending_prompt"] = prompt
st.markdown('</div>', unsafe_allow_html=True)


# ─── Render Chat History ────────────────────────────────────────────────────────
st.markdown('<p class="section-label">Conversation</p>', unsafe_allow_html=True)

for msg in st.session_state.chat_messages:
    role = msg["role"]
    content = msg["content"]
    tool_calls = msg.get("tool_calls", [])

    with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "🤖"):
        for tc in tool_calls:
            st.markdown(f"""
<div class="tool-banner">
    <span>🔧</span>
    <span>Called tool: <strong>{tc}</strong></span>
</div>
""", unsafe_allow_html=True)
        st.markdown(content)


# ─── Core send_message logic (unchanged) ───────────────────────────────────────
def send_message(user_text: str):
    """Send a message to the backend and stream the response into the UI."""
    st.session_state.chat_messages.append({"role": "user", "content": user_text})

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(user_text)

    with st.chat_message("assistant", avatar="🤖"):
        response_container = st.empty()
        tool_container = st.empty()

        accumulated_text = ""
        active_tool_calls = []
        current_tool = None
        had_error = False

        try:
            payload = {
                "message": user_text,
                "thread_id": st.session_state.chat_thread_id,
            }

            with requests.post(
                f"{BACKEND_BASE}/chat",
                json=payload,
                stream=True,
                timeout=120,
            ) as resp:
                if resp.status_code != 200:
                    st.error(f"⚠️ Backend error {resp.status_code}: {resp.text[:200]}")
                    return

                for raw_line in resp.iter_lines():
                    if not raw_line:
                        continue

                    try:
                        event = json.loads(raw_line.decode("utf-8"))
                    except json.JSONDecodeError:
                        continue

                    # ── Tool call notification ──────────────────────────────
                    if "tool_call" in event:
                        current_tool = event["tool_call"]
                        active_tool_calls.append(current_tool)
                        tool_container.markdown(f"""
<div class="tool-banner">
    <span class="tool-spinner"></span>
    <span>Calling <strong>{current_tool}</strong>…</span>
</div>
""", unsafe_allow_html=True)

                    # ── Streaming token ─────────────────────────────────────
                    elif "token" in event:
                        if current_tool:
                            tool_container.empty()
                            current_tool = None
                        accumulated_text += event["token"]
                        response_container.markdown(accumulated_text + "▌")

                    # ── Stream done ─────────────────────────────────────────
                    elif event.get("done"):
                        tool_container.empty()
                        response_container.markdown(accumulated_text)
                        if "thread_id" in event:
                            st.session_state.chat_thread_id = event["thread_id"]

                    # ── Error ───────────────────────────────────────────────
                    elif "error" in event:
                        had_error = True
                        tool_container.empty()
                        response_container.error(f"❌ {event['error']}")
                        break

        except requests.exceptions.ConnectionError:
            had_error = True
            st.error("🔌 Cannot connect to backend. Make sure `uvicorn backend.main:app` is running.")
        except Exception as e:
            had_error = True
            st.error(f"🔌 Unexpected error: {e}")

    if not had_error and accumulated_text:
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": accumulated_text,
            "tool_calls": active_tool_calls,
        })


# ─── Handle Pending Chip Prompt ────────────────────────────────────────────────
if "_pending_prompt" in st.session_state:
    pending = st.session_state.pop("_pending_prompt")
    send_message(pending)


# ─── Chat Input ────────────────────────────────────────────────────────────────
if user_input := st.chat_input(
    "Ask about your channel — views, subs, trends, top videos…",
    key="chat_input_box",
):
    send_message(user_input)


# ─── Empty State ────────────────────────────────────────────────────────────────
if not st.session_state.chat_messages:
    st.markdown("""
<div class="empty-state">
    <div class="empty-icon">💬</div>
    <div class="empty-title">Your Channel Intelligence is ready</div>
    <p class="empty-sub">
        Ask anything about your channel — top videos, audience trends,
        content ideas, or a full performance breakdown.
    </p>
</div>
""", unsafe_allow_html=True)


# ─── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div class="footer-bar">
    Built with &nbsp;<span>LangGraph</span> · <span>YouTube API</span> · <span>FastAPI</span> · <span>Streamlit</span>
</div>
""", unsafe_allow_html=True)