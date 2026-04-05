3. Future-Proofing for Complexity
While your current flow is linear, LangGraph makes it trivial to add conditional logic without making the code messy. For example, you could easily add:

Parallelism: Generating TTS for scene 1 while simultaneously rendering scene 2.
Self-Correction: If the stitch node fails, the graph can automatically route back to a "re-render" node or try a "MoviePy fallback" node based on the error type.










1. Scene-by-Scene Timeline Editor
Shows each scene as a row: [Scene N] | 🎬 Animation preview | 🔊 Audio player | ⏱️ Speed slider
Each scene has independent animation speed and audio speed controls
Visual waveform-like progress bar for context
2. Realtime Preview
Play animation + audio in sync in the browser using HTML components
No re-rendering needed for preview — just browser playbackRate
3. Apply & Re-export
When user is happy → click "Apply Adjustments"
Backend runs FFmpeg with the speed factors per scene, re-stitches into final video
This avoids re-running the expensive Manim render or TTS
4. Smart Auto-Sync Button
Automatically detects scenes where video length ≠ audio length and suggests adjustments
"The animation is 30% faster than audio — auto-stretch?" type UX







# AI Video Generator (LangGraph + Manim)

A production-style Python pipeline that automatically generates short educational videos from a topic text.

True LangGraph Orchestration (High Priority)
Instead of the current for loop in render.py, you should implement a proper State Graph.

Why: This allows the agent to decide which tool to use (e.g., "I'll check the docs for this specific AttributeError, then I'll try to re-render").
Implementation: Use langgraph to define nodes like generate, render_test, search_docs, and stitching.





# mcp tool to add
```text


 covnert to reasonin in render.py   react agent 


 



 
it store previous history somewhere so when i ask for new topic it should not use previous history.

web search
tavily
youtube data api -->Take the final outputs/final_video.mp4 and the generated SEO text and auto-upload it to YouTube.

Read analytics from your existing YouTube videos (e.g., retention rate) to "learn" what types of Manim animations keep viewers engaged, theoretically allowing the LLM to adjust its future animation styles.


3. Unsplash or Wikimedia Commons MCP (For Dynamic Assets)
Why adding it helps: Manim is great for vector math and text, but plain animations can sometimes lack visual flair compared to professional YouTube Shorts. Manim supports ImageMobject, but currently, it relies on static assets you provide.
How it integrates: When the LLM generates a script (e.g., "Imagine a black hole..."), it can use an Image Search MCP to download a real image of a black hole into your assets/ folder, and write the Manim code to fade that image into the background.



GitHub / ReadTheDocs MCP (For Advanced Manim Code Reliability)
Why adding it helps: You have a ReAct agent that loops to fix Manim code by reading the Traceback error. However, Manim Community edition updates frequently, and LLMs often hallucinate older manimlib syntaxes or non-existent methods.
How it integrates: If the LLM encounters a difficult Manim error, it could use an MCP tool that taps directly into the current Manim GitHub repository or Documentation source. It can search the docs for "how to correctly use TransformMatchingTex in version 0.18" to fix its own syntax intelligently, drastically reducing the number of retry loops.



```



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








