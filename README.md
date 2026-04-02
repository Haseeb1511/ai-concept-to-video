# AI Video Generator (LangGraph + Manim)

A production-style Python pipeline that automatically generates short educational videos from a topic text.





## How to run
```bash

us sync
streamlit run frontend/app.py
uv run python main.py

``` 


## Mnetion this  featrue  in reademe 
Autonomous Agent: I replaced the basic "retry loop" in src/pipeline/render.py with a LangGraph ReAct Agent.
Proactive Fixing: If your Manim code has an error, GPT-4o now uses a native test_render_manim tool to verify its own fixes before finalizing the video.
Reasoning: The agent can "read" the error traceback, decide how to fix it, and test it again automatically.
Script & Code Alignment: Your custom/script and custom/manim are now perfectly matched for 7 scenes.
I helped you add blank lines and timestamps to ensure the segmenting logic works exactly as intended.
Architecture: We kept the MCP Server for your Claude Desktop App (so you can prototype quickly) but used Native Native Tools for your backend to ensure maximum speed and production stability.




# Model to downlaod

1. Coqui TTS (Local Text-to-Speech)
Model Name: tts_models/en/ljspeech/tacotron2-DDC
Source: Coqui TTS GitHub
Usage: Located in src/tts/coqui_provider.py. This model runs entirely on your CPU by default (as configured in the code).

2. Ollama (Local LLM)
Default Model: llama3
Config: Found in src/agent/model_loader.py.








