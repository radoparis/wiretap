"""Storage-root resolution and path-safety helpers.

See DECISIONS.md D5 (storage root) and D6 (path-traversal protection).
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_APP_NAME = "OpenCallNotes"
_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")


class PathSafetyError(ValueError):
    """Raised when an untrusted identifier would escape the storage root."""


def app_home() -> Path:
    """Return the OpenCallNotes storage root, creating it if necessary.

    Overridable with ``OPENCALLNOTES_HOME``. Defaults to the macOS Application
    Support directory, or an XDG data dir on other platforms (D5).
    """
    override = os.environ.get("OPENCALLNOTES_HOME")
    if override:
        root = Path(override).expanduser()
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support" / _APP_NAME
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
        root = base / _APP_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def recordings_dir() -> Path:
    """Return the directory that holds session folders."""
    d = app_home() / "recordings"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    """Return the path to the SQLite index."""
    return app_home() / "opencallnotes.sqlite"


def validate_session_id(session_id: str) -> str:
    """Validate an untrusted session id, returning it unchanged if safe (D6)."""
    if not session_id or not _SESSION_ID_RE.match(session_id):
        raise PathSafetyError(f"invalid session id: {session_id!r}")
    if set(session_id) == {"."}:  # reject ".", "..", "..." (path navigation)
        raise PathSafetyError(f"invalid session id: {session_id!r}")
    return session_id


def session_dir(session_id: str, *, create: bool = False) -> Path:
    """Resolve a session folder, guaranteeing it stays inside ``recordings_dir``."""
    validate_session_id(session_id)
    root = recordings_dir().resolve()
    candidate = (root / session_id).resolve()
    if candidate != root and root not in candidate.parents:
        raise PathSafetyError(f"session path escapes storage root: {session_id!r}")
    if create:
        candidate.mkdir(parents=True, exist_ok=True)
    return candidate
