import re
import subprocess
from pathlib import Path

# ─── constants ──────────────────────────────────────────────────────────────
_TIMESTAMP_RE = re.compile(
    r'\[[^\]]*?[\d]+\s*[–\-—]\s*[\d]+s?.*?\]',   # matches [0–3s], [Scene 1 | 3-10s], etc.
    re.IGNORECASE,
)

def _strip_timestamps(text: str) -> str:
    """
    Remove timestamp markers like [0–3s], [3-10s], [50–60s] from the text.
    These are reference-only markers and must NOT be spoken in TTS audio.
    Also collapses any resulting double-spaces and strips leading whitespace per line.
    """
    cleaned = _TIMESTAMP_RE.sub("", text)
    # collapse extra whitespace that remains after stripping
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    # strip each line individually to remove leading spaces left behind
    lines = [line.strip() for line in cleaned.splitlines()]
    # remove blank lines at start/end but keep internal blank lines (scene separators)
    result = "\n".join(lines).strip()
    return result

def _split_script_into_scenes(script: str) -> list[str]:
    """
    Splits the full script into scene-sized chunks.
    Strategy:
      1. Split on blank lines (two or more newlines) to get paragraphs.
      2. If that yields only 1 chunk, fall back to splitting every 2-3 sentences.
    """
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", script.strip()) if p.strip()]
    if len(paragraphs) > 1:
        return paragraphs
    # Fallback: split every 2 sentences
    sentences = re.split(r"(?<=[.!?])\s+", script.strip())
    chunk_size = 2
    chunks = []
    for i in range(0, len(sentences), chunk_size):
        chunk = " ".join(sentences[i:i + chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks if chunks else [script.strip()]

def _get_quality_flag(quality: str) -> str:
    """Returns the Manim quality flag based on the quality setting."""
    if quality == "low_quality":
        return "-ql"
    if quality == "high_quality":
        return "-qh"
    if quality == "fourk_quality":
        return "-qk"
    if quality == "production_quality":
        return "-qp"
    return "-qm"

def _get_audio_duration(audio_path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path
            ],
            capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except Exception:
        return 5.0
