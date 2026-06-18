"""Tests for the v0.2 call-recording worker contract (begin-call / end-call)."""

from __future__ import annotations

import wave
from datetime import datetime
from pathlib import Path

from opencallnotes_worker import audio, paths
from opencallnotes_worker.store import SessionStore


def _write_silence(path: Path, seconds: float, rate: int = 16000) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x00\x00" * int(rate * seconds))


def test_begin_call_creates_two_track_session() -> None:
    store = SessionStore()
    session = audio.begin_call(
        store, title="Standup", language="auto", model="m",
        now=datetime(2026, 6, 18, 15, 0, 0),
    )
    assert session.status == "recording"
    assert [(t.file, t.speaker) for t in session.tracks] == [
        ("mic.wav", "Me"),
        ("system.wav", "Them"),
    ]
    assert paths.session_dir(session.id).is_dir()


def test_end_call_sets_duration_from_longest_track() -> None:
    store = SessionStore()
    session = audio.begin_call(
        store, title="Call", language="auto", model="m",
        now=datetime(2026, 6, 18, 15, 0, 0),
    )
    folder = paths.session_dir(session.id)
    _write_silence(folder / "mic.wav", 7.0)
    _write_silence(folder / "system.wav", 11.0)

    finalized = audio.end_call(store, session.id)
    assert finalized.status == "recorded"
    assert finalized.duration_seconds == 11.0
    assert store.read_session(session.id).status == "recorded"
