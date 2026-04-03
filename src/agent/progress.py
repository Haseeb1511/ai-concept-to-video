import datetime

# Icon map for each log category
_ICONS = {
    "INIT":      "🚀",
    "DETECTION": "🔍",
    "SYNTHESIS": "🎙️",
    "RENDER":    "🎬",
    "AGENT":     "🤖",
    "RETRY":     "🔄",
    "FALLBACK":  "⚠️",
    "ASSEMBLY":  "🔗",
    "COMPLETE":  "✅",
    "CRITICAL":  "❌",
    "ERROR":     "❌",
    "ABORT":     "🛑",
    "INFO":      "ℹ️",
}

_LABELS = {
    "INIT":      "Starting up",
    "DETECTION": "Analyzing script",
    "SYNTHESIS": "Generating audio",
    "RENDER":    "Rendering scene",
    "AGENT":     "AI agent",
    "RETRY":     "Retrying",
    "FALLBACK":  "Using fallback",
    "ASSEMBLY":  "Stitching video",
    "COMPLETE":  "Done",
    "CRITICAL":  "Failed",
    "ERROR":     "Error",
    "ABORT":     "Aborted",
    "INFO":      "Info",
}

def get_pipeline_log(category: str, message: str) -> str:
    """
    Format a friendly, readable pipeline log message.
    Example: 🎬 [14:32:01] Rendering scene  →  Manim Sector 3 (duration: 4.20s)
    """
    now = datetime.datetime.now().strftime("%H:%M:%S")
    cat_upper = category.upper()
    icon  = _ICONS.get(cat_upper,  "•")
    label = _LABELS.get(cat_upper, category.capitalize())

    # Humanize the message – lowercase and clean up military-style words
    human_msg = (
        message
        .replace("MISSION SEGMENTED INTO", "Split into")
        .replace("TTS SIGNAL: SCENE", "Audio for scene")
        .replace("MANIM SECTOR:", "Rendering scene")
        .replace("STITCHING MISSION CLIPS...", "All scenes ready, stitching together...")
        .replace("FFMPEG FAILED. ATTEMPTING MOVIEPY FALLBACK...", "FFmpeg failed, trying MoviePy...")
        .replace("STITCHING FAILED:", "Stitch error:")
        .replace("FINAL VIDEO ARCHIVED:", "Video saved to")
        .replace("STARTING MODULAR PIPELINE...", "Pipeline started")
        .replace("RENDER FAILED: SECTOR", "Render failed for scene")
        .replace("TTS FAILURE:", "Audio generation failed:")
    )
    # Soften ALL CAPS words
    human_msg = " ".join(
        w.capitalize() if w.isupper() and len(w) > 2 else w
        for w in human_msg.split()
    )

    return f"{icon} [{now}] {label}  →  {human_msg}"


# Keep old name as alias so existing callers don't break
def get_military_log(category: str, message: str) -> str:
    return get_pipeline_log(category, message)
