"""Unit tests for transcript exporters (Task 5)."""

from __future__ import annotations

import json

import pytest

from opencallnotes_worker import export
from opencallnotes_worker.export import ExportError, _format_timestamp
from opencallnotes_worker.models import Session, Transcript, TranscriptSegment
from opencallnotes_worker.store import SessionStore


def _transcript() -> Transcript:
    return Transcript(
        language="en",
        model="test-model",
        duration_seconds=7.5,
        text="hello world goodbye",
        segments=[
            TranscriptSegment(id=0, start=0.0, end=3.25, text="hello world"),
            TranscriptSegment(id=1, start=3.25, end=7.5, text="goodbye"),
        ],
    )


def test_format_timestamp() -> None:
    assert _format_timestamp(0) == "00:00:00,000"
    assert _format_timestamp(3.25) == "00:00:03,250"
    assert _format_timestamp(3661.5) == "01:01:01,500"
    assert _format_timestamp(-5) == "00:00:00,000"


def test_render_txt_uses_segments() -> None:
    assert export.render_txt(_transcript()) == "hello world\ngoodbye\n"


def test_render_srt_is_well_formed() -> None:
    srt = export.render_srt(_transcript())
    assert srt.startswith("1\n00:00:00,000 --> 00:00:03,250\nhello world\n")
    assert "2\n00:00:03,250 --> 00:00:07,500\ngoodbye\n" in srt


def test_render_md_has_metadata_and_timestamps() -> None:
    md = export.render_md(_transcript())
    assert "# Transcript" in md
    assert "- Language: en" in md
    assert "**[00:00:00,000]** hello world" in md


def test_render_json_roundtrips() -> None:
    data = json.loads(export.render_json(_transcript()))
    assert data["language"] == "en"
    assert len(data["segments"]) == 2


def test_render_unknown_format_raises() -> None:
    with pytest.raises(ExportError):
        export.render(_transcript(), "pdf")


def test_write_export_writes_file() -> None:
    store = SessionStore()
    store.write_session(
        Session(id="2026-06-18_10-00-00_x", title="x", created_at="2026-06-18T10:00:00+00:00"),
        create_dir=True,
    )
    path = export.write_export("2026-06-18_10-00-00_x", _transcript(), "md")
    assert path.exists()
    assert path.name == "transcript.md"
    assert "# Transcript" in path.read_text(encoding="utf-8")
