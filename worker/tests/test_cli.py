"""End-to-end tests of the CLI JSON contract used by the SwiftUI app (D7)."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from typing import Any


def _run(env: dict[str, str], *args: str) -> tuple[int, dict[str, Any]]:
    proc = subprocess.run(
        [sys.executable, "-m", "opencallnotes_worker", *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc.returncode, payload


def test_devices_json_contract(worker_env: dict[str, str]) -> None:
    code, payload = _run(worker_env, "devices", "--json")
    assert code == 0
    assert "devices" in payload


def test_full_flow_record_transcribe_export(worker_env: dict[str, str]) -> None:
    code, started = _run(
        worker_env, "record", "start", "--device-id", "synthetic", "--title", "CLI call", "--json"
    )
    assert code == 0 and started["status"] == "recording"
    session_id = started["session_id"]

    # Wait for the recorder subprocess to create the WAV, then stop.
    _wait_for_audio(worker_env, session_id)
    code, stopped = _run(worker_env, "record", "stop", "--session-id", session_id, "--json")
    assert code == 0 and stopped["status"] == "recorded"
    assert stopped["duration_seconds"] > 0

    code, listed = _run(worker_env, "sessions", "list", "--json")
    assert code == 0
    assert any(s["id"] == session_id for s in listed["sessions"])

    code, transcribed = _run(worker_env, "transcribe", session_id, "--json")
    assert code == 0 and transcribed["status"] == "transcribed"

    code, got = _run(worker_env, "sessions", "get", session_id, "--json")
    assert code == 0 and got["transcript_available"] is True

    code, exported = _run(worker_env, "export", session_id, "--format", "srt", "--json")
    assert code == 0 and exported["format"] == "srt"
    assert exported["path"].endswith("transcript.srt")


def test_missing_session_error_contract(worker_env: dict[str, str]) -> None:
    code, payload = _run(worker_env, "sessions", "get", "2026-01-01_00-00-00_missing", "--json")
    assert code == 1
    assert payload["error"]["code"] == "session_not_found"


def test_invalid_session_id_error_contract(worker_env: dict[str, str]) -> None:
    code, payload = _run(worker_env, "record", "stop", "--session-id", "../etc", "--json")
    assert code == 1
    assert payload["error"]["code"] == "invalid_session_id"


def _wait_for_audio(env: dict[str, str], session_id: str, timeout: float = 5.0) -> None:
    from opencallnotes_worker import paths

    audio_path = paths.session_dir(session_id) / "audio.wav"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if audio_path.exists() and audio_path.stat().st_size > 44:  # past WAV header
            return
        time.sleep(0.05)
