import streamlit as st
import requests
import os
import time

# --- Page Configuration ---
st.set_page_config(
    page_title="AI Video Generator",
    page_icon="🎬",
    layout="centered",
)

# --- Custom Styling ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Header ---
st.title("🎬 AI Video Generator")
st.markdown("Generate short educational videos from any topic using LangGraph and Manim.")

# --- Form ---
with st.container():
    topic = st.text_input("Enter your video topic:", placeholder="e.g. Explain Dice Loss in 30 seconds?")
    
    # TTS Provider Selection
    tts_options = ["gtts", "elevenlabs", "openai", "coqui"]
    selected_tts = st.selectbox("Select TTS Provider:", options=tts_options, index=0)
    
    backend_url = st.text_input("Backend URL:", value="http://127.0.0.1:8000/generate-video")
    
    generate_btn = st.button("Generate Video")

# --- Logic ---
if generate_btn:
    if not topic:
        st.error("Please enter a topic!")
    else:
        with st.spinner("🚀 Generating your video... This may take a few minutes (Scripting -> TTS -> Manim Rendering -> Stitching)"):
            try:
                # Call the FastAPI backend
                payload = {
                    "topic": topic,
                    "tts_provider": selected_tts
                }
                response = requests.post(backend_url, json=payload, timeout=600) # Long timeout for rendering
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get("error"):
                        st.error(f"Error in {data.get('failed_node')}: {data.get('error')}")
                    elif data.get("video_path"):
                        video_path = data.get("video_path")
                        st.success("✅ Video generated successfully!")
                        
                        # Check if the video file exists locally
                        if os.path.exists(video_path):
                            st.video(video_path)
                            with open(video_path, "rb") as file:
                                st.download_button(
                                    label="Download Video",
                                    data=file,
                                    file_name="generated_video.mp4",
                                    mime="video/mp4"
                                )
                        else:
                            st.warning(f"Video file generated but not found at path: {video_path}")
                else:
                    st.error(f"Backend returned error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Could not connect to the backend. Please make sure the FastAPI server is running (uvicorn backend.main:app).")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

# --- Footer ---
st.markdown("---")
st.markdown("Built with LangGraph, Manim, and FastAPI")
