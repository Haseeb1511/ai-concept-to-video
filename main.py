"""
Entry point for the AI Video Generator backend.
Launches uvicorn with reload enabled but excludes generated directories
(manim_scenes, audio, outputs, videos, temp) so that file writes by the
Manim renderer and other pipeline nodes do NOT trigger a server restart.
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["backend", "src"],          # only watch source code
        reload_excludes=[                         # never react to generated files
            "manim_animation_result/*",
            "*.mp4",
            "*.wav",
            "*.png",
        ],
    )
