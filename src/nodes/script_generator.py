"""
Node 1 — Script Generator
─────────────────────────
Uses an LLM (OpenAI or Ollama) to convert a topic string into a
structured JSON script with scene-level text + visual hints.
"""

import json
import re

from src.agent.model_loader import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    MAX_SCENES,
    call_llm,
    call_ollama,
)

# ─────────────────────────────────────────────
# PROMPT TEMPLATE
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """\
You are an expert educational video script writer.
Your task is to create a structured script for a short educational video.

Rules:
- Generate exactly {max_scenes} scenes.
- Each scene must have a "text" field (what the narrator says, 1–3 sentences) and a
  "visual_hint" field (short description of what should appear on screen).
- Return ONLY valid JSON — no markdown, no explanation, no code fences.
- JSON schema: {{"scenes": [{{"text": "...", "visual_hint": "..."}}]}}
"""

USER_PROMPT = "Create a script about: {topic}"

def _extract_json(raw: str) -> dict:
    """Extract JSON even if the model wrapped it in markdown fences."""
    raw = raw.strip()
    # Strip ```json ... ``` fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)

# ─────────────────────────────────────────────
# NODE FUNCTION
# ─────────────────────────────────────────────
def script_generator_node(state: dict) -> dict:
    topic = state["topic"]
    print(f"[script_generator] Generating script for topic: '{topic}'")

    system = SYSTEM_PROMPT.format(max_scenes=MAX_SCENES)
    user = USER_PROMPT.format(topic=topic)

    try:
        if LLM_PROVIDER == "ollama":
            raw = call_ollama(system, user)
        else:
            raw = call_llm(system, user)

        script = _extract_json(raw)

        # Validate structure
        if "scenes" not in script or not isinstance(script["scenes"], list):
            raise ValueError("LLM response missing 'scenes' list.")

        # Enforce max scenes cap
        script["scenes"] = script["scenes"][:MAX_SCENES]

        print(f"[script_generator] Generated {len(script['scenes'])} scenes.")
        return {"script": script}

    except Exception as exc:
        print(f"ERROR: [script_generator] FAILED: {exc}")
        return {"error": str(exc), "failed_node": "script_generator"}
