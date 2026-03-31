"""
Node 5 — Manim Renderer
───────────────────────
Generates Python scripts for Manim scenes based on scene plans,
then executes Manim via command line to render the videos.
"""

import subprocess
import json
import os
from pathlib import Path
import textwrap

from src.agent.model_loader import MANIM_SCENES_DIR, VIDEOS_DIR, MANIM_QUALITY, MANIM_PREVIEW, VIDEO_RESOLUTION, VIDEO_FPS

MANIM_IMPORTS = """
from manim import *
import json
import os

# Set resolution and FPS
config.pixel_width = {width}
config.pixel_height = {height}
config.frame_rate = {fps}
"""

TEMPLATE_MAP = {
    "text_explanation": """
class RenderScene(Scene):
    def construct(self):
        # Data injected via env var
        data = json.loads(os.environ["SCENE_DATA"])
        text_content = data["text"]
        duration = data["duration"]
        
        # Word wrap using a simple heuristic since Manim's Text width can be tricky
        wrapped_text = "\\n".join(textwrap.wrap(text_content, width=40))
        text_mobj = Text(wrapped_text, font_size=36)
        
        self.play(Write(text_mobj), run_time=min(2.0, duration * 0.4))
        self.wait(max(0.1, duration - min(2.0, duration * 0.4)))
""",
    
    "keyword_highlight": """
class RenderScene(Scene):
    def construct(self):
        data = json.loads(os.environ["SCENE_DATA"])
        text_content = data["text"]
        duration = data["duration"]
        
        words = text_content.split()
        longest = max(words, key=len).strip(".,?!") if words else ""
        
        wrapped_text = "\\n".join(textwrap.wrap(text_content, width=40))
        text_mobj = Text(
            wrapped_text, 
            font_size=36, 
            t2c={longest: YELLOW} if longest else {}
        )
            
        self.play(FadeIn(text_mobj, shift=UP), run_time=min(1.5, duration * 0.3))
        self.wait(max(0.1, duration - min(1.5, duration * 0.3)))
""",

    "bullet_list_explanation": """
class RenderScene(Scene):
    def construct(self):
        data = json.loads(os.environ["SCENE_DATA"])
        text_content = data["text"]
        duration = data["duration"]
        
        group = VGroup()
        bullets = textwrap.wrap(text_content, width=40)[:3] # Max 3 lines to fake a list
        
        for i, line in enumerate(bullets):
            t = Text(f"• {line}", font_size=36)
            group.add(t)
            
        group.arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        
        write_time = duration * 0.6
        time_per_bullet = write_time / max(1, len(bullets))
        
        for item in group:
            self.play(Write(item), run_time=time_per_bullet)
            
        self.wait(duration - write_time)
""",

    "arrow_flow_diagram": """
class RenderScene(Scene):
    def construct(self):
        data = json.loads(os.environ["SCENE_DATA"])
        text_content = data["text"]
        duration = data["duration"]
        
        box1 = RoundedRectangle(corner_radius=0.5, height=2, width=4).set_fill(BLUE, opacity=0.5)
        text1 = Text("Start", font_size=30).move_to(box1)
        g1 = VGroup(box1, text1).move_to(UP*2)
        
        box2 = RoundedRectangle(corner_radius=0.5, height=2, width=4).set_fill(GREEN, opacity=0.5)
        text2 = Text("Process", font_size=30).move_to(box2)
        g2 = VGroup(box2, text2).move_to(DOWN*2)
        
        arrow = Arrow(g1.get_bottom(), g2.get_top(), buff=0.2)
        
        desc = Text("\\n".join(textwrap.wrap(text_content, 30)), font_size=24).move_to(RIGHT*0)
        
        self.play(Create(g1), run_time=min(1.0, duration*0.2))
        self.play(GrowArrow(arrow), run_time=min(0.5, duration*0.1))
        self.play(Create(g2), run_time=min(1.0, duration*0.2))
        self.play(Write(desc), run_time=min(1.5, duration*0.3))
        self.wait(max(0.1, duration - min(4.0, duration*0.8)))
"""
}

def _get_quality_flag() -> str:
    if MANIM_QUALITY == "low_quality": return "-ql"
    if MANIM_QUALITY == "high_quality": return "-qh"
    return "-qm"

def manim_render_node(state: dict) -> dict:
    scene_plans = state.get("scene_plans", [])
    if not scene_plans:
        return {"error": "No scene plans available.", "failed_node": "manim_renderer"}

    print(f"[manim_renderer] Rendering {len(scene_plans)} scenes")
    
    rendered_scenes = []
    width, height = map(int, VIDEO_RESOLUTION.split("x"))
    
    MANIM_SCENES_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    
    for plan in scene_plans:
        scene_id = plan["scene_id"]
        anim_type = plan["animation_type"]
        
        # Fallback to text_explanation if not found
        template = TEMPLATE_MAP.get(anim_type, TEMPLATE_MAP["text_explanation"])
        
        script_code = MANIM_IMPORTS.format(width=width, height=height, fps=VIDEO_FPS)
        script_code += f"import textwrap\n"
        script_code += template
        
        script_path = MANIM_SCENES_DIR / f"scene_{scene_id}.py"
        script_path.write_text(script_code, encoding="utf-8")
        
        quality_flag = _get_quality_flag()
        preview_flag = "-p" if MANIM_PREVIEW else ""
        
        # The output path scheme for manim: media/videos/<script_name>/<quality>/RenderScene.mp4
        output_name = f"scene_{scene_id}_render.mp4"
        
        cmd = [
            "manim", 
            "render",
            str(script_path),
            "RenderScene",
            quality_flag,
            "-o", output_name,
            "--media_dir", str(MANIM_SCENES_DIR / "media")
        ]
        if preview_flag:
            cmd.append(preview_flag)
            
        env = os.environ.copy()
        env["SCENE_DATA"] = json.dumps(plan)
        
        print(f"[manim_renderer] Running manim for scene_{scene_id}: {' '.join(cmd)}")
        try:
            res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            
            # Find the output file
            # Manim structure: media/videos/scene_1/<quality_folder_name>/scene_1_render.mp4
            # Quality folders: 480p15, 720p30, 1080p60 etc. Let's just find it via glob.
            
            video_files = list((MANIM_SCENES_DIR / "media" / "videos").rglob(output_name))
            if not video_files:
                raise FileNotFoundError(f"Manim completed but output video '{output_name}' not found.")
                
            actual_video_path = video_files[0]
            
            # Copy to videos folder
            final_scene_path = VIDEOS_DIR / f"scene_{scene_id}.mp4"
            actual_video_path.replace(final_scene_path)
            
            rendered_scenes.append(str(final_scene_path))
            print(f"[manim_renderer] Successfully rendered {final_scene_path.name}")
            
        except subprocess.CalledProcessError as exc:
            print(f"ERROR: [manim_renderer] Manim command failed for scene {scene_id}. Error: {exc.stderr}")
            return {"error": f"Manim failure on scene {scene_id}", "failed_node": "manim_renderer"}
        except Exception as exc:
            print(f"ERROR: [manim_renderer] Error during rendering scene {scene_id}: {exc}")
            return {"error": str(exc), "failed_node": "manim_renderer"}

    return {"rendered_scenes": rendered_scenes}
