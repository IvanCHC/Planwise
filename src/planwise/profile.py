"""
Configuration management utilities for Planwise Streamlit app.
Handles saving, loading, deleting, and listing user session profiles as JSON files.
"""
import json
import re
from pathlib import Path
from typing import Any, Dict, List

PROFILES_DIR = Path(".profiles")
PROFILES_DIR.mkdir(exist_ok=True)
SAFE_CHARS = re.compile(r"[^A-Za-z0-9 _.-]")

def safe_filename(name: str) -> str:
    name = name.strip()
    name = SAFE_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name)
    return name[:80]

def profile_path(name: str) -> Path:
    return PROFILES_DIR / f"{safe_filename(name)}.json"

def list_profiles() -> list[str]:
    return sorted(p.stem for p in PROFILES_DIR.glob("*.json"))

def save_profile(name: str, data: dict) -> None:
    profile_path(name).write_text(json.dumps(data, indent=2), encoding="utf-8")

def load_profile(name: str) -> dict | None:
    p = profile_path(name)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def delete_profile(name: str) -> None:
    p = profile_path(name)
    if p.exists():
        p.unlink()
