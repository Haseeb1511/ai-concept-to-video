import subprocess
import re
from pathlib import Path
from src.agent.model_loader import TEMP_DIR

def _get_duration(file_path: str) -> float:
    """Helper to get file duration using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0

def _stitch(video_files: list[str], audio_files: list[str], output_path: str) -> bool:
    """Stitch each video+audio pair, then concatenate all together."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    try:
        merged_clips = []
        for i, (vf, af) in enumerate(zip(video_files, audio_files)):
            merged_out = TEMP_DIR / f"merged_scene_{i}.mp4"
            duration = _get_duration(af)
            
            # Merge command: Force duration to match audio exactly
            # This ensures perfect sync across all scenes
            cmd = [
                "ffmpeg", "-y",
                "-i", vf,
                "-i", af,
                "-t", str(duration), # Force output to audio length
                "-c:v", "libx264",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-pix_fmt", "yuv420p",
                "-preset", "ultrafast",
                str(merged_out),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            merged_clips.append(str(merged_out))

        concat_list = TEMP_DIR / "concat_list.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            for clip in merged_clips:
                # Use forward slashes for FFmpeg concat list to avoid Windows path issues
                safe_path = clip.replace('\\', '/')
                f.write(f"file '{safe_path}'\n")

        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_list), "-c", "copy", output_path,
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR [pipeline.stitching] FFmpeg stitch failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR [pipeline.stitching] Stitching failed: {e}")
        return False
