"""Audio recording: pluggable backends + start/stop control (D1, D2, D3).

Recording spans two stateless CLI calls. ``start_recording`` spawns a detached
recorder subprocess (``opencallnotes-worker _record-run``); ``stop_recording``
signals it and finalizes the WAV + metadata.
"""

from __future__ import annotations

import contextlib
import os
import signal
import subprocess
import sys
import threading
import time
import wave
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Protocol

from . import paths
from .models import Session, new_session_id
from .store import SessionStore

# Whisper works best at 16 kHz mono; keep recordings small and model-friendly.
DEFAULT_SAMPLERATE = 16000
DEFAULT_CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2  # int16 PCM
_PID_FILE = "recording.pid"
_LOG_FILE = "recorder.log"
_STOP_GRACE_SECONDS = 10.0


class RecordingError(RuntimeError):
    """Raised on recording lifecycle failures."""


class Recorder(Protocol):
    """Captures audio into an open WAV until ``should_stop`` returns True."""

    def record(
        self,
        *,
        wav: wave.Wave_write,
        device_id: str,
        samplerate: int,
        channels: int,
        should_stop: Callable[[], bool],
    ) -> None: ...


class SyntheticRecorder:
    """Deterministic backend that writes silence. No hardware required (D3)."""

    def record(
        self,
        *,
        wav: wave.Wave_write,
        device_id: str,
        samplerate: int,
        channels: int,
        should_stop: Callable[[], bool],
    ) -> None:
        chunk_frames = max(1, samplerate // 10)  # 0.1 s blocks
        silent_chunk = b"\x00" * (chunk_frames * channels * SAMPLE_WIDTH_BYTES)
        while not should_stop():
            wav.writeframes(silent_chunk)
            time.sleep(chunk_frames / samplerate)


class SoundDeviceRecorder:
    """Real capture via PortAudio. Imports native deps lazily (D3)."""

    def record(
        self,
        *,
        wav: wave.Wave_write,
        device_id: str,
        samplerate: int,
        channels: int,
        should_stop: Callable[[], bool],
    ) -> None:
        import numpy
        import sounddevice

        device: int | str = int(device_id) if device_id.isdigit() else device_id
        blocksize = max(1, samplerate // 10)
        with sounddevice.InputStream(
            samplerate=samplerate,
            channels=channels,
            device=device,
            dtype="int16",
            blocksize=blocksize,
        ) as stream:
            while not should_stop():
                frames, _overflowed = stream.read(blocksize)
                wav.writeframes(numpy.asarray(frames, dtype=numpy.int16).tobytes())


def get_recorder() -> Recorder:
    """Select the recorder backend from ``OPENCALLNOTES_AUDIO_BACKEND``."""
    backend = os.environ.get("OPENCALLNOTES_AUDIO_BACKEND", "sounddevice")
    if backend == "synthetic":
        return SyntheticRecorder()
    if backend == "sounddevice":
        return SoundDeviceRecorder()
    raise RecordingError(f"unknown audio backend: {backend!r}")


def wav_duration_seconds(path: Path) -> float:
    """Return the duration of a PCM WAV file in seconds (0.0 if unreadable)."""
    if not path.exists():
        return 0.0
    try:
        with wave.open(str(path), "rb") as wav:
            rate = wav.getframerate()
            return wav.getnframes() / rate if rate else 0.0
    except (wave.Error, EOFError):
        return 0.0


# -- Lifecycle: start -----------------------------------------------------


def start_recording(
    store: SessionStore,
    *,
    title: str,
    device_id: str,
    language: str,
    model: str,
    now: datetime,
    samplerate: int = DEFAULT_SAMPLERATE,
    channels: int = DEFAULT_CHANNELS,
) -> Session:
    """Create a session and spawn the detached recorder subprocess (D1)."""
    session = Session(
        id=new_session_id(title, now),
        title=title,
        created_at=now.isoformat(),
        language=language,
        model=model,
        status="recording",
    )
    store.write_session(session, create_dir=True)
    folder = paths.session_dir(session.id)

    log_path = folder / _LOG_FILE
    with log_path.open("wb") as log:
        # No shell, fixed argv -> no shell injection (security requirement).
        proc = subprocess.Popen(  # noqa: S603
            recorder_command(
                session.id, device_id=device_id, samplerate=samplerate, channels=channels
            ),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    (folder / _PID_FILE).write_text(str(proc.pid), encoding="utf-8")
    return session


def recorder_command(
    session_id: str, *, device_id: str, samplerate: int, channels: int
) -> list[str]:
    """Build the argv that relaunches this worker as the recorder subprocess.

    When running from source, ``sys.executable`` is a Python interpreter, so we
    relaunch via ``-m opencallnotes_worker``. When running as a PyInstaller
    *frozen* binary, ``sys.executable`` is the worker binary itself and already
    dispatches CLI subcommands, so ``-m`` must NOT be passed (it would be parsed
    as a bad argument and the recorder would never start).
    """
    argv = [sys.executable]
    if not getattr(sys, "frozen", False):
        argv += ["-m", "opencallnotes_worker"]
    argv += [
        "_record-run",
        "--session-id", session_id,
        "--device-id", device_id,
        "--samplerate", str(samplerate),
        "--channels", str(channels),
    ]
    return argv


def run_recorder(session_id: str, *, device_id: str, samplerate: int, channels: int) -> None:
    """Recorder subprocess entrypoint: capture to ``audio.wav`` until signalled."""
    folder = paths.session_dir(session_id)
    wav_path = folder / "audio.wav"

    stop_event = threading.Event()

    def _handle(_signum: int, _frame: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)

    recorder = get_recorder()
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(SAMPLE_WIDTH_BYTES)
        wav.setframerate(samplerate)
        recorder.record(
            wav=wav,
            device_id=device_id,
            samplerate=samplerate,
            channels=channels,
            should_stop=stop_event.is_set,
        )


# -- Lifecycle: stop ------------------------------------------------------


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_for_exit(pid: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            return True
        time.sleep(0.05)
    return not _pid_alive(pid)


def stop_recording(store: SessionStore, session_id: str) -> Session:
    """Signal the recorder, wait for clean shutdown, finalize metadata (D1)."""
    session = store.read_session(session_id)
    folder = paths.session_dir(session_id)
    pid_file = folder / _PID_FILE

    if pid_file.exists():
        try:
            pid = int(pid_file.read_text(encoding="utf-8").strip())
        except ValueError as exc:
            raise RecordingError(f"corrupt pid file for session {session_id}") from exc
        if _pid_alive(pid):
            with contextlib.suppress(ProcessLookupError):
                os.kill(pid, signal.SIGTERM)
            if not _wait_for_exit(pid, _STOP_GRACE_SECONDS):
                with contextlib.suppress(ProcessLookupError):
                    os.kill(pid, signal.SIGKILL)
                _wait_for_exit(pid, 2.0)
        pid_file.unlink(missing_ok=True)

    duration = wav_duration_seconds(folder / session.audio_file)
    session.duration_seconds = round(duration, 3)
    session.status = "recorded"
    return store.write_session(session)
