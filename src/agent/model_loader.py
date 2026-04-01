import os
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
AUDIO_DIR = BASE_DIR / "audio"
VIDEOS_DIR = BASE_DIR / "videos"
OUTPUTS_DIR = BASE_DIR / "outputs"
MANIM_SCENES_DIR = BASE_DIR / "manim_scenes"
TEMP_DIR = BASE_DIR / "temp"

# Ensure directories exist
for _d in [AUDIO_DIR, VIDEOS_DIR, OUTPUTS_DIR, MANIM_SCENES_DIR, TEMP_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

# LLM & EMBEDDING
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")



# Chatting LLM
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    streaming=True,
    api_key=OPENAI_API_KEY
)

# Embedding LLM
EMBEDDING = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY
)



# PROVIDER & PIPELINE SETTINGS
TTS_PROVIDER = "gtts"
ELEVENLABS_API_KEY = ""
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

MANIM_QUALITY = "high_quality"
MANIM_PREVIEW = False

VIDEO_RESOLUTION = "1080x1920"
VIDEO_FPS = 60
VIDEO_OUTPUT_NAME = "final_video.mp4"

MAX_SCENES = 6
MIN_SCENE_DURATION = 2.0




# HELPER FUNCTIONS (Replacement for ModelLoader class)
def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Invokes the global LLM instance (OpenAI/LangChain)."""
    from langchain_core.messages import SystemMessage, HumanMessage
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]
    response = llm.invoke(messages)
    return response.content





def generate_text(system_prompt: str, user_prompt: str) -> str:
    """
    Unified entry point for text generation (OpenAI).
    """
    return call_llm(system_prompt, user_prompt)
