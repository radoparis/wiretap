"""Shared fixtures: isolated storage root + synthetic/fake backends."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point storage at a temp dir and force hardware-free backends for every test."""
    home = tmp_path / "app-home"
    monkeypatch.setenv("OPENCALLNOTES_HOME", str(home))
    monkeypatch.setenv("OPENCALLNOTES_AUDIO_BACKEND", "synthetic")
    monkeypatch.setenv("OPENCALLNOTES_TRANSCRIBE_BACKEND", "fake")
    # Drop any inherited XDG override so resolution is deterministic.
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    yield home


@pytest.fixture
def worker_env() -> dict[str, str]:
    """Environment for invoking the worker as a subprocess in tests."""
    return {
        **os.environ,
        "OPENCALLNOTES_HOME": os.environ["OPENCALLNOTES_HOME"],
        "OPENCALLNOTES_AUDIO_BACKEND": "synthetic",
        "OPENCALLNOTES_TRANSCRIBE_BACKEND": "fake",
    }
