"""
Node 6 — Video Stitcher
───────────────────────
Combines the rendered manim scenes with the corresponding TTS audio,
then concatenates them into the final video output.
"""

from pathlib import Path
import os
import subprocess

from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from moviepy.config import change_settings

from src.agent.model_loader import OUTPUTS_DIR, VIDEO_OUTPUT_NAME, TEMP_DIR

# Ensure ImageMagick binary path is correct if we need it (moviepy sometimes needs it)
# change_settings({"IMAGEMAGICK_BINARY": "magick"})

def _stitch_ffmpeg(video_files: list[str], audio_files: list[str], output_path: str) -> bool:
    """Uses FFmpeg directly to stitch video and audio. Faster than MoviePy."""
    try:
        # Step 1: Combine each video with its corresponding audio
        merged_clips = []
        for i, (vf, af) in enumerate(zip(video_files, audio_files)):
            merged_out = TEMP_DIR / f"merged_{i}.mp4"
            cmd_merge = [
                "ffmpeg", "-y",
                "-i", vf,
                "-i", af,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                str(merged_out)
            ]
            subprocess.run(cmd_merge, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            merged_clips.append(str(merged_out))
            
        # Step 2: Concatenate the merged clips
        concat_list = TEMP_DIR / "concat_list.txt"
        with open(concat_list, "w", encoding="utf-8") as f:
            for clip in merged_clips:
                # FFmpeg requires paths to be correctly formatted in the list file
                f.write(f"file '{clip}'\n")
                
        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            output_path
        ]
        
        print(f"[video_stitcher] Final FFmpeg concat: {' '.join(cmd_concat)}")
        subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: [video_stitcher] FFmpeg stitching failed: {e}")
        return False


def _stitch_moviepy(video_files: list[str], audio_files: list[str], output_path: str) -> bool:
    """Fallback MoviePy stitcher."""
    try:
        clips = []
        for vf, af in zip(video_files, audio_files):
            vid = VideoFileClip(vf)
            aud = AudioFileClip(af)
            
            # Match lengths
            vid = vid.set_audio(aud)
            clips.append(vid)
            
        final_clip = concatenate_videoclips(clips, method="compose")
        final_clip.write_videofile(
            output_path,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            logger=None
        )
        return True
    except Exception as e:
        print(f"ERROR: [video_stitcher] MoviePy stitching failed: {e}")
        return False

def video_stitch_node(state: dict) -> dict:
    video_files = state.get("rendered_scenes", [])
    audio_files = state.get("audio_files", [])
    
    if not video_files or not audio_files:
        return {"error": "Missing video or audio files.", "failed_node": "video_stitch"}
        
    if len(video_files) != len(audio_files):
        print(f"WARNING: Count mismatch: {len(video_files)} videos vs {len(audio_files)} audios.")
        
    print(f"[video_stitcher] Stitching {len(video_files)} scenes into final output.")
    
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # We create a unique name based on the state topic
    safe_topic = ''.join(c if c.isalnum() else '_' for c in state.get('topic', 'output')).strip('_')
    safe_topic = safe_topic[:20] if safe_topic else "final_video"
    
    output_path = OUTPUTS_DIR / f"{safe_topic}_{VIDEO_OUTPUT_NAME}"
    output_str = str(output_path)
    
    # Check if FFmpeg exists
    ffmpeg_available = False
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ffmpeg_available = True
    except FileNotFoundError:
        pass
        
    success = False
    if ffmpeg_available:
        print("[video_stitcher] FFmpeg found, using FFmpeg fast-stitch.")
        success = _stitch_ffmpeg(video_files, audio_files, output_str)
        
    if not success:
        print("[video_stitcher] Falling back to MoviePy stitcher.")
        success = _stitch_moviepy(video_files, audio_files, output_str)
        
    if not success:
        return {"error": "All stitching methods failed.", "failed_node": "video_stitch"}
        
    print(f"[video_stitcher] Final video successfully created at {output_str}")
    return {"final_video": output_str}
