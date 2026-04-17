# mlx-yap

Local voice dictation for macOS, powered by [MLX](https://github.com/ml-explore/mlx). Hold a key, speak, release — text appears wherever your cursor is. Works in **any application**: terminal, browser, Notes, Messages, Slack, your IDE — anywhere you can type.

- **Fully local transcription** via [mlx-whisper](https://github.com/ml-explore/mlx-examples) on Apple Silicon (M-series GPU + Neural Engine)
- **Optional post-processing** via Mistral API (cleanup, summarize, clarify)
- **No cloud audio** — your voice never leaves your machine
- **System-wide** — not limited to the terminal

---

## How it works

```
Hold Right Cmd  →  speak  →  release  →  text at cursor
                                 ↕
                    Ctrl+Shift+M to cycle mode:
                    raw → cleanup → summarize → clarify → raw …
```

`yap` runs as a background daemon in your terminal. It listens for a global hotkey (Right Cmd), records from your mic while held, transcribes locally via MLX Whisper, and pastes the result into whatever application is currently focused.

### Why

CLI agent frameworks like [Claude Code](https://docs.anthropic.com/en/docs/claude-code) and [Codex](https://github.com/openai/codex) have built-in voice input (`/voice`), but it's only available with subscription billing — not when using API keys directly.

It started as a tool for voice-driven vibe coding, but since it works system-wide (any app with cursor focus), it's just as useful for drafting emails, writing notes, messaging, etc.

---

## Setup

**Requirements:** macOS, Apple Silicon (M1+), Python 3.12+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/sofdog-gh/mlx-yap.git
cd mlx-yap
uv sync
```

First run downloads the Whisper model (~1.5 GB, one time):

```bash
uv run yap
```

### macOS permissions (one-time, required)

`yap` uses global hotkeys and simulates paste (Cmd+V) into the active app. This requires **Accessibility** permissions.

| Permission | Where | Required for |
|---|---|---|
| **Accessibility** | System Settings → Privacy & Security → Accessibility | Global hotkeys + paste simulation |
| **Microphone** | Prompted automatically | Recording |

To grant Accessibility to your terminal app:

1. Open **System Settings → Privacy & Security → Accessibility**
2. Click the **+** button
3. Find the apps you want to use `yap` in and add them
4. Make sure the toggle is **on**

Without this, `yap` won't detect hotkeys or paste into applications. You may need to restart the apps.

---

## Usage

```
yap                          Start the daemon
yap mode <name>              Switch active capability
yap language [code]          View or set transcription language
yap context --project <name> Set project name (helps transcription accuracy)
yap capabilities             List all capabilities, mark active one
```

### Language

By default, `yap` auto-detects the spoken language. This adds latency to every recording because Whisper runs an extra detection pass. For faster transcription, set your language once:

```bash
uv run yap language en       # English
uv run yap language fr       # French
uv run yap language de       # German
```

This is persisted in your config — you only need to set it once. Run `uv run yap language` to see the current setting. Whisper supports 99 languages; use ISO codes (en, fr, de, ja, zh, …) or full names (english, french, german, …).

### Hotkeys

| Action | Hotkey |
|---|---|
| Record | Hold **Right Cmd** |
| Cycle capability | **Ctrl+Shift+M** |

Mode is persistent — set it once, it applies to all subsequent recordings. You can switch it from another terminal while the daemon is running.

---

## Configuration

Config lives at `~/.config/mlx-yap/config.yaml`. Created automatically on first run; copy `config.example.yaml` to customize.

```yaml
whisper:
  model: mlx-community/whisper-large-v3-turbo  # best speed/quality on M4
  language: null                                 # null = auto-detect, or e.g. "en"

api:
  provider: mistral
  model: mistral-small-latest
  api_key_env: MISTRAL_API_KEY                  # name of the env var holding your key

context:
  project_name: ""   # improve transcription (more context)

active_capability: raw
```

Set your API key in the environment (e.g. in `.zshrc`):

```bash
export MISTRAL_API_KEY=your_key_here
```

---

## Capabilities

Capabilities control what happens to the transcribed text before it's pasted. Post-processing is optional — each non-raw capability sends the transcription through a Mistral model with a configurable prompt.

```
raw        →  paste transcription as-is
cleanup    →  fix grammar, strip filler words ("um", "uh", "like", …)
summarize  →  condense to key points and action items
clarify    →  clean up + reorganize scattered/convoluted ideas logically
```

Switch interactively with **Ctrl+Shift+M**, or from the command line:

```bash
yap mode cleanup
```

### Adding a custom capability

Add a new key under `capabilities:` in your config. It needs a `description` and a `prompt` with `{text}` and `{context}` placeholders:

```yaml
capabilities:
  bullet-points:
    description: "Convert to bullet point list"
    prompt: |
      Convert this voice transcription into a concise bullet point list.
      Preserve all key information. Do not add anything that was not said.
      {context}

      Transcription:
      {text}
```

Then switch to it with `yap mode bullet-points` or cycle to it with Ctrl+Shift+M.

---

## Audio cues

| Event | Sound |
|---|---|
| Recording started | Tink |
| Done (text pasted) | Pop |
| Error | Basso |
