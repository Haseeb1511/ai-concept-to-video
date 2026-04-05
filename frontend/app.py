import streamlit as st

# ── Page config lives here so it runs exactly once ────────────────────────────
st.set_page_config(
    page_title="AI Video Studio",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Multi-page navigation ──────────────────────────────────────────────────────
workflow_page = st.Page(
    "pages/workflow.py",
    title="Workflow",
    icon="🎬",
)

chatting_page = st.Page(
    "pages/chatting.py",
    title="Chatting",
    icon="💬",
)

pg = st.navigation([workflow_page, chatting_page])
pg.run()
