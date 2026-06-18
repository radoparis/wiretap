"""Tests for transcription progress reporting."""

from __future__ import annotations

import json
import wave
from pathlib import Path

from opencallnotes_worker import paths
from opencallnotes_worker.models import Session
from opencallnotes_worker.progress import (
    PROGRESS_FILE,
    StdoutProgressParser,
    clear_progress,
    parse_timestamp,
    write_progress,
)
from opencallnotes_worker.store import SessionStore
from opencallnotes_worker.transcribe import FakeBackend, transcribe_session


def test_parse_timestamp_variants() -> None:
    assert parse_timestamp("00:05.000") == 5.0
    assert parse_timestamp("01:02.500") == 62.5
    assert parse_timestamp("01:00:00.000") == 3600.0
    assert parse_timestamp("garbage") is None


def test_stdout_parser_emits_progress_from_whisper_lines() -> None:
    calls: list[tuple[float, float]] = []
    parser = StdoutProgressParser(total_seconds=10.0, callback=lambda p, t: calls.append((p, t)))
    # Whisper verbose output, written in fragments to exercise line buffering.
    parser.write("[00:00.000 --> 00:03.000]  Hello\n[00:03.000 --> ")
    parser.write("00:08.000]  world\n")
    assert calls == [(3.0, 10.0), (8.0, 10.0)]


def test_stdout_parser_clamps_to_total() -> None:
    calls: list[tuple[float, float]] = []
    parser = StdoutProgressParser(total_seconds=5.0, callback=lambda p, t: calls.append((p, t)))
    parser.write("[00:00.000 --> 00:09.000]  over\n")
    assert calls == [(5.0, 5.0)]  # processed never exceeds total


def test_write_and_clear_progress(tmp_path: Path) -> None:
    write_progress(tmp_path, 3.0, 12.0)
    data = json.loads((tmp_path / PROGRESS_FILE).read_text())
    assert data["fraction"] == 0.25
    assert data["processed_seconds"] == 3.0
    clear_progress(tmp_path)
    assert not (tmp_path / PROGRESS_FILE).exists()


def _write_silence_wav(path: Path, seconds: float = 12.0, rate: int = 16000) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x00\x00" * int(rate * seconds))


def test_fake_backend_reports_monotonic_progress(tmp_path: Path) -> None:
    audio = tmp_path / "audio.wav"
    _write_silence_wav(audio)
    calls: list[tuple[float, float]] = []
    FakeBackend().transcribe(
        audio_path=audio, model="m", language="en",
        progress=lambda p, t: calls.append((p, t)),
    )
    processed = [p for p, _ in calls]
    assert processed == sorted(processed)        # non-decreasing
    assert calls[-1][0] == calls[-1][1]          # ends at 100%


def test_transcribe_session_clears_progress_file() -> None:
    store = SessionStore()
    session_id = "2026-06-18_10-00-00_call"
    store.write_session(
        Session(id=session_id, title="Call", created_at="2026-06-18T10:00:00+00:00",
                status="recorded"),
        create_dir=True,
    )
    _write_silence_wav(paths.session_dir(session_id) / "audio.wav")
    transcribe_session(store, session_id)
    assert not (paths.session_dir(session_id) / PROGRESS_FILE).exists()
