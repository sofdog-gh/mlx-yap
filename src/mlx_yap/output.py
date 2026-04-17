from __future__ import annotations

import subprocess


SOUNDS = {
    "recording_start": "/System/Library/Sounds/Tink.aiff",
    "done": "/System/Library/Sounds/Pop.aiff",
    "error": "/System/Library/Sounds/Basso.aiff",
}


def paste(text: str) -> None:
    subprocess.run(["pbcopy"], input=text.encode(), check=True)
    subprocess.run(
        [
            "osascript",
            "-e",
            'tell application "System Events" to keystroke "v" using {command down}',
        ],
        check=True,
    )


def notify(title: str, message: str) -> None:
    script = (
        f'display notification "{_esc(message)}" with title "{_esc(title)}"'
    )
    subprocess.run(["osascript", "-e", script], check=False)


def audio_cue(event: str) -> None:
    sound = SOUNDS.get(event)
    if sound:
        subprocess.Popen(["afplay", sound])


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')
