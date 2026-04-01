import json
from pathlib import Path
from src.agent.progress import get_military_log
from src.agent.model_loader import (
    AUDIO_DIR, VIDEO_RESOLUTION, VIDEO_OUTPUT_NAME, MANIM_QUALITY, OUTPUTS_DIR,
)

# New modular imports
from src.pipeline.utils import _strip_timestamps, _split_script_into_scenes, _get_audio_duration
from src.tts import _synthesise_tts
from src.pipeline.render import _render_manim_scene
from src.pipeline.stitching import _stitch

def run_custom_pipeline(
    manim_code: str,
    script: str,
    tts_provider: str = "gtts",
):
    """
    Modularized video generation pipeline.
    Yields log strings, finally yields a JSON with 'final_video' or 'error'.
    """
    yield json.dumps({"log": get_military_log("INIT", "STARTING MODULAR PIPELINE...")})

    # 1. Split script
    scenes_raw = _split_script_into_scenes(script)
    yield json.dumps({"log": get_military_log("DETECTION", f"MISSION SEGMENTED INTO {len(scenes_raw)} SCENES")})

    # 2. TTS synthesis
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    audio_files: list[str] = []
    scenes_for_tts = [_strip_timestamps(s) for s in scenes_raw]

    for idx, tts_text in enumerate(scenes_for_tts, start=1):
        yield json.dumps({"log": get_military_log("SYNTHESIS", f"TTS SIGNAL: SCENE {idx} ({len(tts_text)} CHARS)")})
        out_path = AUDIO_DIR / f"custom_scene_{idx}.wav"
        try:
            _synthesise_tts(tts_text, out_path, tts_provider)
            audio_files.append(str(out_path))
        except Exception as exc:
            yield json.dumps({"log": get_military_log("ABORT", f"TTS FAILURE: {exc}"), "error": str(exc), "failed_node": "custom_tts"})
            return

    # 3. Manim rendering
    width, height = map(int, VIDEO_RESOLUTION.split("x"))
    rendered_scenes: list[str] = []
    
    for idx, (raw_text, audio_path) in enumerate(zip(scenes_raw, audio_files), start=1):
        duration = _get_audio_duration(audio_path)
        yield json.dumps({"log": get_military_log("RENDER", f"MANIM SECTOR: {idx} [DURATION: {duration:.2f}S]")})
        
        scene_data = {
            "scene_id": idx,
            "text": _strip_timestamps(raw_text),
            "duration": duration,
        }

        # Inner callback to capture agentic logs
        def _log_forwarder(category, msg):
            # This is a bit of a hack to get the logs out of the nested generator,
            # but since we're in a yield loop, we'll actually need to handle this differently.
            # For now, we'll just print to stdout and the renderer will handle internal logging.
            pass

        rendered = _render_manim_scene(
            idx, manim_code, scene_data, width, height, MANIM_QUALITY,
            log_callback=lambda cat, msg: print(f"[{cat}] {msg}")
        )

        if not rendered:
            yield json.dumps({
                "log": get_military_log("CRITICAL", f"RENDER FAILED: SECTOR {idx}"),
                "error": f"Manim rendering failed on scene {idx}",
                "failed_node": "custom_manim"
            })
            return

        rendered_scenes.append(rendered)

    # 4. Stitching
    yield json.dumps({"log": get_military_log("ASSEMBLY", "STITCHING MISSION CLIPS...")})
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(OUTPUTS_DIR / f"custom_{VIDEO_OUTPUT_NAME}")

    success = _stitch(rendered_scenes, audio_files, output_path)
    
    if not success:
        # MoviePy fallback (legacy support)
        yield json.dumps({"log": get_military_log("RETRY", "FFMPEG FAILED. ATTEMPTING MOVIEPY FALLBACK...")})
        try:
            from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
            clips = []
            for vf, af in zip(rendered_scenes, audio_files):
                vid = VideoFileClip(vf).set_audio(AudioFileClip(af))
                clips.append(vid)
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(output_path, fps=30, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
            success = True
        except Exception as exc:
            yield json.dumps({"log": get_military_log("ABORT", f"STITCHING FAILED: {exc}")})

    if not success:
        yield json.dumps({"error": "All stitching methods failed.", "failed_node": "custom_stitch"})
        return

    yield json.dumps({"log": get_military_log("COMPLETE", f"FINAL VIDEO ARCHIVED: {output_path}")})
    yield json.dumps({"final_video": output_path})
