from __future__ import annotations

from typing import Any


def _render_context(context: dict[str, Any]) -> str:
    parts = []
    if context.get("project_name"):
        parts.append(f"Context: This transcription is for the project '{context['project_name']}'.")
    return "\n".join(parts)


def process(
    text: str,
    capability: dict[str, Any] | None,
    context: dict[str, Any],
    api_cfg: dict[str, Any],
    api_key: str | None,
) -> str:
    if capability is None:
        return text

    prompt_template = capability.get("prompt", "{text}")
    context_str = _render_context(context)
    prompt = prompt_template.replace("{text}", text).replace("{context}", context_str).strip()

    try:
        return _call_mistral(prompt, api_cfg, api_key)
    except Exception as exc:
        from mlx_yap.output import notify
        notify("yap: API error", str(exc)[:100])
        return text


def _call_mistral(prompt: str, api_cfg: dict[str, Any], api_key: str | None) -> str:
    from mistralai import Mistral

    client = Mistral(api_key=api_key or "")
    response = client.chat.complete(
        model=api_cfg.get("model", "mistral-small-latest"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a voice transcription post-processor. "
                    "Return only the processed text."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )
    return response.choices[0].message.content.strip()
