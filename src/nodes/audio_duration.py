"""
Node 3 — Audio Duration
───────────────────────
Measures the duration (in seconds) of each generated audio file.
These durations will be used by the scene planner to match animation times.
"""

from pydub import AudioSegment
from pathlib import Path

from pydub import AudioSegment
from pathlib import Path

from src.agent.model_loader import MIN_SCENE_DURATION

def audio_duration_node(state: dict) -> dict:
    audio_files = state.get("audio_files", [])
    
    if not audio_files:
        return {"error": "No audio files available.", "failed_node": "audio_duration"}
        
    print(f"[audio_duration] Measuring duration for {len(audio_files)} audio files")
    
    durations = []
    
    for idx, filepath in enumerate(audio_files, start=1):
        try:
            path = Path(filepath)
            if not path.exists():
                raise FileNotFoundError(f"Audio file not found: {filepath}")
                
            audio = AudioSegment.from_wav(str(path))
            duration_sec = len(audio) / 1000.0
            
            # Enforce minimum duration
            if duration_sec < MIN_SCENE_DURATION:
                print(f"WARNING: [audio_duration] Scene {idx} duration ({duration_sec}s) too short. Clamping to {MIN_SCENE_DURATION}s.")
                duration_sec = MIN_SCENE_DURATION
                
            durations.append(duration_sec)
            print(f"[audio_duration] Scene {idx} ({path.name}): {duration_sec:.2f}s")
            
        except Exception as exc:
            print(f"ERROR: [audio_duration] Failed to measure {filepath}: {exc}")
            return {"error": str(exc), "failed_node": "audio_duration"}
            
    return {"audio_durations": durations}
