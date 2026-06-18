"""Recording lifecycle tests: synthetic backend + real start/stop subprocess (D1)."""

from __future__ import annotations

import wave
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from opencallnotes_worker import audio, paths
from opencallnotes_worker.audio import SyntheticRecorder, wav_duration_seconds
from opencallnotes_worker.store import SessionStore


def test_synthetic_recorder_writes_frames(tmp_path: Path) -> None:
    wav_path = tmp_path / "audio.wav"
    calls = {"n": 0}

    def should_stop() -> bool:
        calls["n"] += 1
        return calls["n"] > 3  # record three 0.1 s chunks then stop

    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(16000)
        SyntheticRecorder().record(
            wav=wav, device_id="synthetic", samplerate=16000, channels=1,
            should_stop=should_stop,
        )

    assert wav_duration_seconds(wav_path) > 0


def test_wav_duration_missing_file(tmp_path: Path) -> None:
    assert wav_duration_seconds(tmp_path / "nope.wav") == 0.0


def test_start_then_stop_records_audio() -> None:
    """End-to-end: spawn the detached recorder, then stop and finalize."""
    store = SessionStore()
    session = audio.start_recording(
        store,
        title="Integration",
        device_id="synthetic",
        language="auto",
        model="test-model",
        now=datetime(2026, 6, 18, 12, 0, 0),
        samplerate=16000,
        channels=1,
    )
    folder = paths.session_dir(session.id)
    assert (folder / "recording.pid").exists()
    assert store.read_session(session.id).status == "recording"

    # Let the recorder capture a little audio (synthetic backend writes silence).
    _wait_until(lambda: (folder / "audio.wav").exists(), 5.0)

    stopped = audio.stop_recording(store, session.id)
    assert stopped.status == "recorded"
    assert stopped.duration_seconds > 0
    assert (folder / "audio.wav").exists()
    assert not (folder / "recording.pid").exists()


def _wait_until(predicate: Callable[[], bool], timeout: float) -> None:
    import time

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
