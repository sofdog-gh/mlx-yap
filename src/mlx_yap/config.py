from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIR = Path.home() / ".config" / "mlx-yap"
CONFIG_PATH = CONFIG_DIR / "config.yaml"

DEFAULTS: dict[str, Any] = {
    "whisper": {
        "model": "mlx-community/whisper-large-v3-turbo",
        "language": None,
    },
    "hotkeys": {
        "record": "cmd_r",
        "cycle_capability": "ctrl+shift+m",
    },
    "api": {
        "provider": "mistral",
        "model": "mistral-small-latest",
        "api_key_env": "MISTRAL_API_KEY",
    },
    "context": {
        "project_name": "",
    },
    "active_capability": "raw",
    "capabilities": {
        "raw": None,
        "cleanup": {
            "description": "Fix grammar, remove filler words and hesitations",
            "prompt": (
                "Clean up this voice transcription. Fix grammar and punctuation.\n"
                "Remove filler words (um, uh, like, you know, so, basically),\n"
                "hesitations, and false starts.\n"
                "Do not add any information that was not said.\n"
                "{context}\n\n"
                "Transcription:\n{text}"
            ),
        },
        "summarize": {
            "description": "Condense to key points",
            "prompt": (
                "Summarize this voice transcription concisely.\n"
                "Preserve all key points, decisions, and action items.\n"
                "Do not add any information that was not said.\n"
                "{context}\n\n"
                "Transcription:\n{text}"
            ),
        },
        "clarify": {
            "description": "Clean up and organize unstructured ideas",
            "prompt": (
                "Clean up this voice transcription. Fix grammar, remove filler words\n"
                "and hesitations. Organize unstructured or scattered ideas into a\n"
                "clear, logical order. Group related points together.\n"
                "Do not add any information that was not said or cannot be\n"
                "unequivocally inferred.\n"
                "{context}\n\n"
                "Transcription:\n{text}"
            ),
        },
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return copy.deepcopy(DEFAULTS)
    with CONFIG_PATH.open() as f:
        user_config = yaml.safe_load(f) or {}
    return _deep_merge(DEFAULTS, user_config)


def update_field(key_path: str, value: Any) -> None:
    """Update a dotted key path in the config YAML (e.g. 'context.project_name')."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open() as f:
            data = yaml.safe_load(f) or {}
    else:
        data = {}

    keys = key_path.split(".")
    node = data
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value

    with CONFIG_PATH.open("w") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def get_api_key(cfg: dict[str, Any]) -> str | None:
    from dotenv import dotenv_values
    env_var = cfg["api"].get("api_key_env", "MISTRAL_API_KEY")
    return os.environ.get(env_var) or dotenv_values().get(env_var)
