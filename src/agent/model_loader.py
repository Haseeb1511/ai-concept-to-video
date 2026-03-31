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
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Chatting LLM
llm = ChatOpenAI(
    model=OPENAI_MODEL,
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
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

TTS_PROVIDER = os.getenv("TTS_PROVIDER", "gtts")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

MANIM_QUALITY = os.getenv("MANIM_QUALITY", "medium_quality")   
MANIM_PREVIEW = os.getenv("MANIM_PREVIEW", "False").lower() == "true"

VIDEO_RESOLUTION = os.getenv("VIDEO_RESOLUTION", "1080x1920") 
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
VIDEO_OUTPUT_NAME = "final_video.mp4"

MAX_SCENES = int(os.getenv("MAX_SCENES", "6"))
MIN_SCENE_DURATION = float(os.getenv("MIN_SCENE_DURATION", "2.0"))


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

def call_ollama(system_prompt: str, user_prompt: str) -> str:
    """Directly calls Ollama API."""
    import requests
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "format": "json",
    }
    r = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=120)
    r.raise_for_status()
    return r.json()["message"]["content"]
