import json
import re
from src.agent.model_loader import generate_text

def generate_seo_metadata(manim_code: str, script: str) -> dict:
    """
    Generates SEO optimized title and description based on the provided script and manim code.
    """
    system_prompt = """
You are Claude Opus, an expert YouTube SEO strategist and master content creator.
Your objective is to generate highly engaging, high-retention, and heavily SEO-optimized titles and descriptions for a YouTube Short video.
You will be provided with the animation code (Manim) and the narration script used to generate the video.

REQUIREMENTS:
1. TITLE: Create a catchy, click-worthy title (under 60 characters) that maximizes views. Use strong hooks.
2. DESCRIPTION: Write a detailed, SEO-friendly description. Include relevant keywords organically.
3. HASHTAGS: Include a robust set of highly relevant, trending hashtags (e.g., #shorts, #python, #manim, #coding, etc.) at the end of the description.
4. FORMAT: You MUST output ONLY raw JSON without any markdown formatting, backticks, or extra commentary.

The JSON format must strictly be:
{
    "title": "Your Awesome Catchy Title Here",
    "description": "Your detailed SEO description here with #hashtags"
}
"""
    
    user_prompt = f"### SCRIPT:\n{script}\n\n### MANIM CODE:\n{manim_code}\n"
    
    try:
        response_text = generate_text(system_prompt, user_prompt)
        
        # Strip potential markdown formatting (e.g., ```json\n...\n```)
        response_text = re.sub(r"^```json", "", response_text, flags=re.IGNORECASE).strip()
        response_text = re.sub(r"```$", "", response_text).strip()
        
        data = json.loads(response_text)
        return data
    except Exception as e:
        print(f"Error parse JSON from SEO model: {e}")
        return {
            "title": "Error generating title",
            "description": f"An error occurred while generating SEO metadata: {str(e)}"
        }
