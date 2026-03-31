# AI Video Generator (LangGraph + Manim)

A production-style Python pipeline that automatically generates short educational videos from a topic text.










# Model to downlaod

1. Coqui TTS (Local Text-to-Speech)
Model Name: tts_models/en/ljspeech/tacotron2-DDC
Source: Coqui TTS GitHub
Usage: Located in src/tts/coqui_provider.py. This model runs entirely on your CPU by default (as configured in the code).

2. Ollama (Local LLM)
Default Model: llama3
Config: Found in src/agent/model_loader.py.














## Architecture

The system uses **LangGraph** to coordinate these states:
1. `script_generator`: LLM converts topic to structured JSON script with visual hints.
2. `tts_generation`: Synthesises audio (gTTS, ElevenLabs, or Coqui).
3. `audio_duration`: Measures audio timing to sync animations.
4. `scene_planner`: Converts script + audio timings into Manim animation templates.
5. `manim_render`: Generates Manim scripts and executes the CLI renderer.
6. `video_stitch`: Uses FFmpeg (or MoviePy fallback) to concatenate scenes + audio into the final output.

## Setup Instructions

### System Requirements
You will need to install **FFmpeg**, **ImageMagick**, and **LaTeX** (optional, for math expressions in Manim) on your system.

On Windows (using Chocolatey or Scoop):
```bash
choco install ffmpeg
choco install imagemagick
```
or download manually. 
See the [Manim installation guide](https://docs.manim.community/en/stable/installation.html) for more details.

### Python Environment
1. Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
cd ai_video_generator
pip install -r requirements.txt
```

3. Setup environment variables:
```bash
copy .env.example .env
```
Edit `.env` to add your optional OpenAI or ElevenLabs API keys.


## Running the System

### 1. Via FastAPI Server (Recommended)
Start the server:
```bash
uvicorn app.main:app --reload
```

Trigger a video generation via curl or Postman:
```bash
curl -X POST "http://127.0.0.1:8000/generate-video" \
     -H "Content-Type: application/json" \
     -d '{"topic": "Explain Attention Mechanism"}'
```

### 2. Via Python directly
You can write a simple `run.py` at the root directory:
```python
from app.pipeline import run_video_pipeline

if __name__ == "__main__":
    result = run_video_pipeline("Explain Neural Networks")
    print(result)
```

## Outputs

Videos will be assembled in the `outputs/` folder (e.g., `outputs/final_video.mp4`). Intermediate files are kept in `audio/`, `manim_scenes/`, and `videos/`.
