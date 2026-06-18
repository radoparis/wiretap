"""Transcription progress reporting.

Whisper decodes audio sequentially and (in verbose mode) prints each segment as
``[start --> end] text``. We parse the ``end`` timestamp to derive a true
fraction (processed audio seconds / total), and write it to a small JSON file the
UI polls while a blocking ``transcribe`` call is in flight.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
from collections.abc import Callable
from pathlib import Path

# Called with (processed_seconds, total_seconds) as transcription advances.
ProgressCallback = Callable[[float, float], None]

PROGRESS_FILE = "transcribe.progress"

# Matches the end timestamp in a Whisper verbose line: "[00:00.000 --> 01:02.500] ..."
_ARROW_RE = re.compile(r"-->\s*([0-9:]+\.[0-9]{1,3})\s*\]")


def parse_timestamp(value: str) -> float | None:
    """Parse ``MM:SS.mmm`` or ``HH:MM:SS.mmm`` into seconds; ``None`` if malformed."""
    try:
        main, millis = value.split(".")
        parts = [int(p) for p in main.split(":")]
    except ValueError:
        return None
    seconds = 0
    for part in parts:
        seconds = seconds * 60 + part
    return seconds + int(millis.ljust(3, "0")[:3]) / 1000.0


class StdoutProgressParser(io.TextIOBase):
    """A ``redirect_stdout`` target that turns Whisper's verbose lines into
    progress callbacks. It swallows the output so the worker's real stdout stays
    a clean single JSON object."""

    def __init__(self, total_seconds: float, callback: ProgressCallback) -> None:
        super().__init__()
        self._total = total_seconds
        self._callback = callback
        self._buffer = ""

    def write(self, text: str) -> int:
        self._buffer += text
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            self._handle(line)
        return len(text)

    def _handle(self, line: str) -> None:
        match = _ARROW_RE.search(line)
        if match is None:
            return
        end = parse_timestamp(match.group(1))
        if end is None:
            return
        processed = min(end, self._total) if self._total > 0 else end
        # Progress reporting must never break transcription.
        with contextlib.suppress(Exception):
            self._callback(processed, self._total)


def write_progress(folder: Path, processed_seconds: float, total_seconds: float) -> None:
    """Atomically write the progress file for a session folder."""
    fraction = 0.0
    if total_seconds > 0:
        fraction = max(0.0, min(1.0, processed_seconds / total_seconds))
    payload = {
        "processed_seconds": round(processed_seconds, 3),
        "total_seconds": round(total_seconds, 3),
        "fraction": round(fraction, 4),
    }
    path = folder / PROGRESS_FILE
    tmp = folder / f"{PROGRESS_FILE}.tmp"
    tmp.write_text(json.dumps(payload), encoding="utf-8")
    os.replace(tmp, path)


def clear_progress(folder: Path) -> None:
    """Remove the progress file (and any stray temp) once transcription ends."""
    (folder / PROGRESS_FILE).unlink(missing_ok=True)
    (folder / f"{PROGRESS_FILE}.tmp").unlink(missing_ok=True)
