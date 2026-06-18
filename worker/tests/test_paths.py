"""Unit tests for storage paths and path-traversal protection (D6)."""

from __future__ import annotations

import pytest

from opencallnotes_worker import paths
from opencallnotes_worker.paths import PathSafetyError


def test_app_home_respects_override(isolated_home: object) -> None:
    assert paths.app_home() == isolated_home
    assert paths.recordings_dir().is_dir()


@pytest.mark.parametrize("bad", ["../escape", "..", "a/b", "foo/../bar", "", "with space"])
def test_validate_session_id_rejects_unsafe(bad: str) -> None:
    with pytest.raises(PathSafetyError):
        paths.validate_session_id(bad)


@pytest.mark.parametrize("good", ["2026-06-18_22-15-03_call", "abc_DEF-123", "a.b"])
def test_validate_session_id_accepts_safe(good: str) -> None:
    assert paths.validate_session_id(good) == good


def test_session_dir_stays_inside_root() -> None:
    with pytest.raises(PathSafetyError):
        paths.session_dir("../../etc")

    sdir = paths.session_dir("2026-06-18_10-00-00_x", create=True)
    assert sdir.is_dir()
    assert paths.recordings_dir().resolve() in sdir.resolve().parents
