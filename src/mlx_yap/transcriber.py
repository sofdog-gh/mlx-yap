from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy.typing as npt

_model_cache: dict[str, Any] = {}


def transcribe(audio: "npt.NDArray", cfg: dict[str, Any]) -> str:
    import mlx_whisper

    model_name = cfg["whisper"]["model"]
    language = cfg["whisper"].get("language") or None

    kwargs: dict[str, Any] = {"path_or_hf_repo": model_name}
    if language:
        kwargs["language"] = language

    result = mlx_whisper.transcribe(audio, **kwargs)
    return result["text"].strip()


def preload(cfg: dict[str, Any]) -> None:
    """Warm up the Whisper model by loading it ahead of time."""
    import numpy as np
    import mlx_whisper

    model_name = cfg["whisper"]["model"]
    language = cfg["whisper"].get("language") or None

    # Transcribe a silent 1-second clip to trigger model download + load
    silence = np.zeros(16000, dtype="float32")
    kwargs: dict[str, Any] = {"path_or_hf_repo": model_name}
    if language:
        kwargs["language"] = language

    mlx_whisper.transcribe(silence, **kwargs)
