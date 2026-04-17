from __future__ import annotations

import signal
import threading
from enum import Enum, auto
from typing import Any

from pynput import keyboard

from mlx_yap import config as cfg_mod
from mlx_yap import output, recorder, transcriber, processor


class State(Enum):
    IDLE = auto()
    RECORDING = auto()
    PROCESSING = auto()


def _cycle_capability(cfg: dict[str, Any]) -> str:
    caps = list(cfg["capabilities"].keys())
    current = cfg.get("active_capability", "raw")
    try:
        idx = caps.index(current)
    except ValueError:
        idx = 0
    next_cap = caps[(idx + 1) % len(caps)]
    cfg_mod.update_field("active_capability", next_cap)
    return next_cap


class Daemon:
    def __init__(self) -> None:
        self._state = State.IDLE
        self._recorder = recorder.Recorder()
        self._pressed: set = set()
        self._lock = threading.Lock()
        self._right_cmd_key: keyboard.Key | None = None

    def _is_right_cmd(self, key: Any) -> bool:
        # pynput represents Right Cmd as Key.cmd_r on macOS
        return key == keyboard.Key.cmd_r

    def _is_cycle_combo(self) -> bool:
        # Ctrl+Shift+M
        has_ctrl = any(
            k in self._pressed
            for k in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r)
        )
        has_shift = any(
            k in self._pressed
            for k in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r)
        )
        has_m = keyboard.KeyCode.from_char("m") in self._pressed
        return has_ctrl and has_shift and has_m

    def _on_press(self, key: Any) -> None:
        self._pressed.add(key)

        if self._is_cycle_combo():
            self._handle_cycle()
            return

        if self._is_right_cmd(key):
            with self._lock:
                if self._state == State.IDLE:
                    self._state = State.RECORDING
                    self._recorder.start()
                    output.audio_cue("recording_start")

    def _on_release(self, key: Any) -> None:
        self._pressed.discard(key)

        if self._is_right_cmd(key):
            with self._lock:
                if self._state != State.RECORDING:
                    return
                self._state = State.PROCESSING

            thread = threading.Thread(target=self._run_pipeline, daemon=True)
            thread.start()

    def _handle_cycle(self) -> None:
        cfg = cfg_mod.load()
        next_cap = _cycle_capability(cfg)
        cap_cfg = cfg["capabilities"].get(next_cap)
        desc = cap_cfg["description"] if cap_cfg else "no post-processing"
        output.notify("yap: Mode changed", f"Mode: {next_cap} — {desc}")

    def _run_pipeline(self) -> None:
        try:
            audio = self._recorder.stop()
            if audio is None:
                with self._lock:
                    self._state = State.IDLE
                return

            cfg = cfg_mod.load()
            api_key = cfg_mod.get_api_key(cfg)

            text = transcriber.transcribe(audio, cfg)
            if not text:
                output.notify("yap", "Nothing transcribed")
                with self._lock:
                    self._state = State.IDLE
                return

            active = cfg.get("active_capability", "raw")
            capability = cfg["capabilities"].get(active)
            text = processor.process(
                text, capability, cfg.get("context", {}), cfg["api"], api_key
            )

            output.paste(text)
            output.audio_cue("done")
        except Exception as exc:
            output.notify("yap: error", str(exc)[:120])
            output.audio_cue("error")
        finally:
            with self._lock:
                self._state = State.IDLE

    def run(self) -> None:
        cfg = cfg_mod.load()
        print("yap: loading Whisper model… (first run may take a while)")
        transcriber.preload(cfg)
        active = cfg.get("active_capability", "raw")
        lang = cfg["whisper"].get("language")
        lang_label = lang if lang else "auto-detect"
        print(f"yap: ready  [mode: {active}, lang: {lang_label}]  — hold Right ⌘ to record, Ctrl+Shift+M to cycle mode")
        if not lang:
            print("yap: tip — set a language for faster transcription: uv run yap language en")
        output.notify("yap", f"Ready — mode: {active}")

        stop = threading.Event()
        signal.signal(signal.SIGINT, lambda *_: stop.set())
        signal.signal(signal.SIGTERM, lambda *_: stop.set())

        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            while listener.is_alive() and not stop.is_set():
                stop.wait(timeout=0.5)
            listener.stop()
