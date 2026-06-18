"""Unit tests for SessionStore: session.json + SQLite index (D4)."""

from __future__ import annotations

import pytest

from opencallnotes_worker.models import Session
from opencallnotes_worker.store import SessionNotFoundError, SessionStore


def _session(session_id: str, *, status: str = "recorded") -> Session:
    return Session(
        id=session_id,
        title=session_id,
        created_at=f"{session_id}T00:00:00+00:00",
        status=status,  # type: ignore[arg-type]
    )


def test_write_and_read_roundtrip() -> None:
    store = SessionStore()
    written = store.write_session(_session("2026-06-18_10-00-00_a"), create_dir=True)
    loaded = store.read_session(written.id)
    assert loaded == written


def test_read_missing_raises() -> None:
    with pytest.raises(SessionNotFoundError):
        SessionStore().read_session("2026-01-01_00-00-00_missing")


def test_list_is_sorted_newest_first() -> None:
    store = SessionStore()
    store.write_session(_session("2026-06-17_10-00-00_old"), create_dir=True)
    store.write_session(_session("2026-06-18_10-00-00_new"), create_dir=True)
    ids = [s.id for s in store.list_sessions()]
    assert ids == ["2026-06-18_10-00-00_new", "2026-06-17_10-00-00_old"]


def test_index_upsert_reflects_updates() -> None:
    store = SessionStore()
    session = store.write_session(_session("2026-06-18_10-00-00_a"), create_dir=True)
    session.status = "transcribed"
    session.duration_seconds = 12.5
    store.write_session(session)
    listed = store.list_sessions()[0]
    assert listed.status == "transcribed"
    assert listed.duration_seconds == 12.5


def test_reindex_rebuilds_from_folders() -> None:
    store = SessionStore()
    store.write_session(_session("2026-06-18_10-00-00_a"), create_dir=True)
    store.write_session(_session("2026-06-18_11-00-00_b"), create_dir=True)
    # Wipe the index and rebuild purely from folders.
    fresh = SessionStore()
    assert fresh.reindex() == 2
    assert {s.id for s in fresh.list_sessions()} == {
        "2026-06-18_10-00-00_a",
        "2026-06-18_11-00-00_b",
    }
