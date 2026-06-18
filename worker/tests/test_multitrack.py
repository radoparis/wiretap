"""Tests for v0.2 multi-track (Me/Them) transcription and labeled export."""

from __future__ import annotations

import wave
from pathlib import Path

from opencallnotes_worker import export, paths
from opencallnotes_worker.models import AudioTrack, Session, Transcript, TranscriptSegment
from opencallnotes_worker.store import SessionStore
from opencallnotes_worker.transcribe import transcribe_session


def _write_silence(path: Path, seconds: float, rate: int = 16000) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(b"\x00\x00" * int(rate * seconds))


def _call_session(store: SessionStore, session_id: str = "2026-06-18_15-00-00_call") -> str:
    store.write_session(
        Session(
            id=session_id,
            title="Call",
            created_at="2026-06-18T15:00:00+00:00",
            status="recorded",
            tracks=[
                AudioTrack(file="mic.wav", speaker="Me"),
                AudioTrack(file="system.wav", speaker="Them"),
            ],
        ),
        create_dir=True,
    )
    folder = paths.session_dir(session_id)
    _write_silence(folder / "mic.wav", 6.0)
    _write_silence(folder / "system.wav", 12.0)
    return session_id


def test_multitrack_segments_are_labeled_and_sorted() -> None:
    store = SessionStore()
    session_id = _call_session(store)

    transcript = transcribe_session(store, session_id)

    speakers = {seg.speaker for seg in transcript.segments}
    assert speakers == {"Me", "Them"}
    starts = [seg.start for seg in transcript.segments]
    assert starts == sorted(starts)                      # chronological merge
    assert [seg.id for seg in transcript.segments] == list(range(len(transcript.segments)))
    # duration reflects the longer track
    assert transcript.duration_seconds == 12.0


def test_single_track_has_no_speaker_label() -> None:
    store = SessionStore()
    session_id = "2026-06-18_15-10-00_solo"
    store.write_session(
        Session(id=session_id, title="Solo", created_at="2026-06-18T15:10:00+00:00",
                status="recorded"),
        create_dir=True,
    )
    _write_silence(paths.session_dir(session_id) / "audio.wav", 5.0)
    transcript = transcribe_session(store, session_id)
    assert all(seg.speaker is None for seg in transcript.segments)


def _labeled_transcript() -> Transcript:
    return Transcript(
        language="en", model="m", duration_seconds=10.0, text="",
        segments=[
            TranscriptSegment(id=0, start=0.0, end=2.0, text="hi there", speaker="Me"),
            TranscriptSegment(id=1, start=2.0, end=4.0, text="hello back", speaker="Them"),
        ],
    )


def test_exports_include_speaker_labels() -> None:
    t = _labeled_transcript()
    assert export.render_txt(t) == "Me: hi there\nThem: hello back\n"
    srt = export.render_srt(t)
    assert "Me: hi there" in srt and "Them: hello back" in srt


def test_md_label_format() -> None:
    md = export.render_md(_labeled_transcript())
    assert "**[00:00:00,000] Me:** hi there" in md
    assert "**[00:00:02,000] Them:** hello back" in md
