"""Tests for device listing (Task 2: must not crash without hardware)."""

from __future__ import annotations

import pytest

from opencallnotes_worker import devices


def test_synthetic_backend_lists_synthetic_device() -> None:
    listed = devices.list_input_devices()
    assert any(d.id == "synthetic" for d in listed)


def test_sounddevice_backend_missing_portaudio_does_not_crash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # With the real backend selected but PortAudio unavailable, listing must
    # return cleanly (possibly empty) rather than raising.
    monkeypatch.setenv("OPENCALLNOTES_AUDIO_BACKEND", "sounddevice")
    listed = devices.list_input_devices()
    assert isinstance(listed, list)
