"""Tests for the transcription flow using the deterministic fake backend (D3)."""

from __future__ import annotations

import wave
from pathlib import Path

import pytest

from opencallnotes_worker import paths
from opencallnotes_worker.models import Session
from opencallnotes_worker.store import SessionStore, load_transcript_dict
from opencallnotes_worker.transcribe import TranscribeError, transcribe_session


def _write_silence_wav(path: Path, *, seconds: float = 6.0, rate: int = 16000) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x00\x00" * int(rate * seconds))


def _recorded_session(store: SessionStore, session_id: str = "2026-06-18_10-00-00_call") -> str:
    store.write_session(
        Session(
            id=session_id,
            title="Call",
            created_at="2026-06-18T10:00:00+00:00",
            status="recorded",
        ),
        create_dir=True,
    )
    _write_silence_wav(paths.session_dir(session_id) / "audio.wav")
    return session_id


def test_transcribe_produces_transcript_and_exports() -> None:
    store = SessionStore()
    session_id = _recorded_session(store)

    transcript = transcribe_session(store, session_id)

    assert transcript.language == "en"
    assert len(transcript.segments) >= 1
    folder = paths.session_dir(session_id)
    for name in ("transcript.json", "transcript.txt", "transcript.md", "transcript.srt"):
        assert (folder / name).exists(), name

    refreshed = store.read_session(session_id)
    assert refreshed.status == "transcribed"
    assert load_transcript_dict(session_id) is not None


def test_transcribe_respects_language_override() -> None:
    store = SessionStore()
    session_id = _recorded_session(store)
    transcript = transcribe_session(store, session_id, language="pl")
    assert transcript.language == "pl"


def test_transcribe_missing_audio_marks_failed() -> None:
    store = SessionStore()
    store.write_session(
        Session(
            id="2026-06-18_11-00-00_noaudio",
            title="No audio",
            created_at="2026-06-18T11:00:00+00:00",
            status="recorded",
        ),
        create_dir=True,
    )
    with pytest.raises(TranscribeError):
        transcribe_session(store, "2026-06-18_11-00-00_noaudio")
