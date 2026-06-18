"""Session persistence: ``session.json`` (canonical) + SQLite index (D4).

All SQL is parameterized (security requirement).
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from . import paths
from .models import Session

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id               TEXT PRIMARY KEY,
    title            TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    duration_seconds REAL NOT NULL DEFAULT 0,
    audio_file       TEXT NOT NULL DEFAULT 'audio.wav',
    language         TEXT NOT NULL DEFAULT 'auto',
    model            TEXT NOT NULL,
    status           TEXT NOT NULL
);
"""


class SessionNotFoundError(LookupError):
    """Raised when a session id does not exist on disk."""


class SessionStore:
    """Reads/writes session metadata to folders and keeps a SQLite index."""

    def __init__(self) -> None:
        self._connect_and_migrate()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(paths.db_path())
        conn.row_factory = sqlite3.Row
        return conn

    def _connect_and_migrate(self) -> None:
        with closing(self._connect()) as conn, conn:
            conn.executescript(_SCHEMA)

    # -- session.json IO -------------------------------------------------

    def _session_json_path(self, session_id: str) -> Path:
        return paths.session_dir(session_id) / "session.json"

    def write_session(self, session: Session, *, create_dir: bool = False) -> Session:
        """Persist ``session.json`` and upsert the SQLite index."""
        if create_dir:
            paths.session_dir(session.id, create=True)
        path = self._session_json_path(session.id)
        path.write_text(session.model_dump_json(indent=2), encoding="utf-8")
        self._index(session)
        return session

    def read_session(self, session_id: str) -> Session:
        """Load a session from its canonical ``session.json``."""
        path = self._session_json_path(session_id)
        if not path.exists():
            raise SessionNotFoundError(session_id)
        return Session.model_validate_json(path.read_text(encoding="utf-8"))

    # -- SQLite index ----------------------------------------------------

    def _index(self, session: Session) -> None:
        with closing(self._connect()) as conn, conn:
            conn.execute(
                """
                INSERT INTO sessions
                    (id, title, created_at, duration_seconds, audio_file,
                     language, model, status)
                VALUES (:id, :title, :created_at, :duration_seconds, :audio_file,
                        :language, :model, :status)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    created_at=excluded.created_at,
                    duration_seconds=excluded.duration_seconds,
                    audio_file=excluded.audio_file,
                    language=excluded.language,
                    model=excluded.model,
                    status=excluded.status
                """,
                session.model_dump(),
            )

    def list_sessions(self) -> list[Session]:
        """Return all indexed sessions, newest first."""
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC, id DESC"
            ).fetchall()
        return [Session.model_validate(dict(row)) for row in rows]

    def reindex(self) -> int:
        """Rebuild the SQLite index by scanning session folders (D4)."""
        with closing(self._connect()) as conn, conn:
            conn.execute("DELETE FROM sessions")
        count = 0
        for child in sorted(paths.recordings_dir().iterdir()):
            meta = child / "session.json"
            if child.is_dir() and meta.exists():
                self._index(Session.model_validate_json(meta.read_text(encoding="utf-8")))
                count += 1
        return count


def load_transcript_dict(session_id: str) -> dict[str, object] | None:
    """Return parsed ``transcript.json`` for a session, or ``None`` if absent."""
    path = paths.session_dir(session_id) / "transcript.json"
    if not path.exists():
        return None
    data: dict[str, object] = json.loads(path.read_text(encoding="utf-8"))
    return data
