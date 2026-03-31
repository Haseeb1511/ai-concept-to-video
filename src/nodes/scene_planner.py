"""
Node 4 — Scene Planner
──────────────────────
Combines the script's visual hints and the audio durations to prepare
structured animation instructions for the Manim renderer.
"""

from src.agent.model_loader import MIN_SCENE_DURATION

def _determine_animation_type(visual_hint: str) -> str:
    """Simple heuristic to pick a Manim template based on the visual hint."""
    hint = visual_hint.lower()
    
    if "list" in hint or "bullet" in hint:
        return "bullet_list_explanation"
    elif "diagram" in hint or "flow" in hint or "arrow" in hint:
        return "arrow_flow_diagram"
    elif "highlight" in hint or "important" in hint:
        return "keyword_highlight"
    else:
        return "text_explanation"


def scene_planner_node(state: dict) -> dict:
    script = state.get("script", {})
    scenes = script.get("scenes", [])
    durations = state.get("audio_durations", [])
    
    if not scenes or not durations:
        return {"error": "Missing scenes or durations data.", "failed_node": "scene_planner"}
        
    if len(scenes) != len(durations):
        return {"error": "Mismatch between number of scenes and audio durations.", "failed_node": "scene_planner"}

    print(f"[scene_planner] Planning {len(scenes)} scenes")
    
    scene_plans = []
    
    for idx, (scene, duration) in enumerate(zip(scenes, durations), start=1):
        text = scene.get("text", "")
        visual_hint = scene.get("visual_hint", "")
        anim_type = _determine_animation_type(visual_hint)
        
        plan = {
            "scene_id": idx,
            "animation_type": anim_type,
            "text": text,
            "visual_hint": visual_hint,
            "duration": max(duration, MIN_SCENE_DURATION)
        }
        scene_plans.append(plan)
        print(f"[scene_planner] Formulated plan for Scene {idx}: type='{anim_type}', duration={plan['duration']:.2f}s")
        
    return {"scene_plans": scene_plans}
