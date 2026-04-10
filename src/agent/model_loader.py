import os
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from dotenv import load_dotenv
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESULT_DIR = BASE_DIR / "manim_animation_result"

# Organized Structure
FINAL_VIDEOS_DIR = RESULT_DIR / "final_videos"
INTERMEDIATE_DIR = RESULT_DIR / "intermediate"

AUDIO_DIR = INTERMEDIATE_DIR / "audio"
SCENES_DIR = INTERMEDIATE_DIR / "scenes"
SCRIPTS_DIR = INTERMEDIATE_DIR / "scripts"
TEMP_DIR = INTERMEDIATE_DIR / "temp"

# Ensure directories exist
for _d in [FINAL_VIDEOS_DIR, AUDIO_DIR, SCENES_DIR, SCRIPTS_DIR, TEMP_DIR]:
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
TTS_PROVIDER = "openai"
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "3DR8c2yd30eztg65o4jV")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_VOICE_ID = os.getenv("GOOGLE_VOICE_ID", "Charon")

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
DEEPGRAM_VOICE_ID = os.getenv("DEEPGRAM_VOICE_ID", "aura-orion-en")

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

def get_tool_calling_llm(tools=None):
    """
    Returns the global LLM instance bound with the provided tools.
    If no tools are provided, it tries to fetch them from the MCP client.
    """
    if tools is None:
        from src.mcp.client import get_mcp_tools
        tools = get_mcp_tools()
        
    if not tools:
        return llm
        
    return llm.bind_tools(tools)





def generate_text(system_prompt: str, user_prompt: str) -> str:
    """
    Unified entry point for text generation (OpenAI).
    """
    return call_llm(system_prompt, user_prompt)
