"""
File utility helpers used across the pipeline.
"""

import hashlib
import json
import shutil
from pathlib import Path


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def safe_filename(text: str, max_len: int = 50) -> str:
    """Convert arbitrary text to a safe filename slug."""
    import re
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    slug = re.sub(r"[\s_]+", "_", slug)
    return slug[:max_len]


def topic_hash(topic: str) -> str:
    """Short deterministic hash for a topic string (used for caching)."""
    return hashlib.md5(topic.encode()).hexdigest()[:8]


def load_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def clean_directory(path: str | Path) -> None:
    p = Path(path)
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)
