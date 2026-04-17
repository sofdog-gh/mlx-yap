from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import numpy as np
import sounddevice as sd

if TYPE_CHECKING:
    import numpy.typing as npt

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
MIN_DURATION_S = 0.3


class Recorder:
    def __init__(self) -> None:
        self._chunks: list[npt.NDArray] = []
        self._lock = threading.Lock()
        self._stream: sd.InputStream | None = None
        self._start_time: float | None = None

    def _callback(self, indata: npt.NDArray, frames: int, time: object, status: object) -> None:
        with self._lock:
            self._chunks.append(indata.copy())

    def start(self) -> None:
        import time as _time

        self._chunks = []
        self._start_time = _time.monotonic()
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> npt.NDArray | None:
        import time as _time

        if self._stream is None:
            return None

        self._stream.stop()
        self._stream.close()
        self._stream = None

        elapsed = _time.monotonic() - (self._start_time or 0)
        if elapsed < MIN_DURATION_S:
            return None

        with self._lock:
            if not self._chunks:
                return None
            audio = np.concatenate(self._chunks, axis=0).flatten()

        return audio
