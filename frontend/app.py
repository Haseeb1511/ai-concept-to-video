import streamlit as st

# ── Page config lives here so it runs exactly once ────────────────────────────
st.set_page_config(
    page_title="AI Short Studio",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Multi-page navigation ──────────────────────────────────────────────────────
workflow_page = st.Page(
    "pages/workflow.py",
    title="Short Generator",
    icon="🎬",
)

chatting_page = st.Page(
    "pages/chatting.py",
    title="Chatting",
    icon="💬",
)

voiceover_studio_page = st.Page(
    "pages/voiceover_studio.py",
    title="Voiceover Studio",
    icon="🎙️",
)

pg = st.navigation([workflow_page, chatting_page, voiceover_studio_page])
pg.run()
