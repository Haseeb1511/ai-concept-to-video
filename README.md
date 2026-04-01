# AI Video Generator (LangGraph + Manim)

A production-style Python pipeline that automatically generates short educational videos from a topic text.





## How to run
```bash

us sync
streamlit run frontend/app.py
uv run python main.py

``` 





# Model to downlaod

1. Coqui TTS (Local Text-to-Speech)
Model Name: tts_models/en/ljspeech/tacotron2-DDC
Source: Coqui TTS GitHub
Usage: Located in src/tts/coqui_provider.py. This model runs entirely on your CPU by default (as configured in the code).

2. Ollama (Local LLM)
Default Model: llama3
Config: Found in src/agent/model_loader.py.








