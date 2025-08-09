"""
Configuration management utilities for Planwise Streamlit app.
Handles saving, loading, deleting, and listing user session profiles as JSON files.
"""
import json
import os
from typing import Any, Dict, List

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "../../configs")
os.makedirs(CONFIG_DIR, exist_ok=True)

def get_config_path(name: str) -> str:
    return os.path.join(CONFIG_DIR, f"{name}.json")

def save_config(name: str, data: Dict[str, Any]) -> Any:
    with open(get_config_path(name), "w") as f:
        json.dump(data, f, indent=2)

def load_config(name: str) -> Any:
    with open(get_config_path(name), "r") as f:
        return json.load(f)

def delete_config(name: str) -> None:
    os.remove(get_config_path(name))

def list_configs() -> List[str]:
    return [f[:-5] for f in os.listdir(CONFIG_DIR) if f.endswith(".json")]
