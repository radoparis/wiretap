"""Transcript exporters: TXT, Markdown, SRT, JSON (Task 5)."""

from __future__ import annotations

from pathlib import Path

from . import paths
from .models import Transcript, TranscriptSegment

FORMATS = ("txt", "md", "srt", "json")
_EXTENSION = {"txt": "txt", "md": "md", "srt": "srt", "json": "json"}


class ExportError(ValueError):
    """Raised when an unknown export format is requested."""


def _format_timestamp(seconds: float) -> str:
    """Format seconds as an SRT timestamp ``HH:MM:SS,mmm``."""
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _speaker_text(seg: TranscriptSegment) -> str:
    """Segment text, prefixed with the speaker label when present (v0.2)."""
    return f"{seg.speaker}: {seg.text}" if seg.speaker else seg.text


def render_txt(transcript: Transcript) -> str:
    if transcript.segments:
        return "\n".join(_speaker_text(seg) for seg in transcript.segments) + "\n"
    return transcript.text + ("\n" if transcript.text else "")


def render_md(transcript: Transcript) -> str:
    lines = ["# Transcript", ""]
    lines.append(f"- Language: {transcript.language}")
    lines.append(f"- Model: {transcript.model}")
    lines.append(f"- Duration: {transcript.duration_seconds:.1f}s")
    lines.append("")
    if transcript.segments:
        for seg in transcript.segments:
            stamp = _format_timestamp(seg.start)
            speaker = f" {seg.speaker}:" if seg.speaker else ""
            lines.append(f"**[{stamp}]{speaker}** {seg.text}")
            lines.append("")
    else:
        lines.append(transcript.text)
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def render_srt(transcript: Transcript) -> str:
    blocks: list[str] = []
    for index, seg in enumerate(transcript.segments, start=1):
        start = _format_timestamp(seg.start)
        end = _format_timestamp(seg.end)
        blocks.append(f"{index}\n{start} --> {end}\n{_speaker_text(seg)}\n")
    return "\n".join(blocks)


def render_json(transcript: Transcript) -> str:
    return transcript.model_dump_json(indent=2)


def render(transcript: Transcript, fmt: str) -> str:
    if fmt == "txt":
        return render_txt(transcript)
    if fmt == "md":
        return render_md(transcript)
    if fmt == "srt":
        return render_srt(transcript)
    if fmt == "json":
        return render_json(transcript)
    raise ExportError(f"unknown export format: {fmt!r} (expected one of {', '.join(FORMATS)})")


def export_path(session_id: str, fmt: str) -> Path:
    if fmt not in _EXTENSION:
        raise ExportError(f"unknown export format: {fmt!r}")
    return paths.session_dir(session_id) / f"transcript.{_EXTENSION[fmt]}"


def write_export(session_id: str, transcript: Transcript, fmt: str) -> Path:
    """Render a single format and write it into the session folder."""
    path = export_path(session_id, fmt)
    path.write_text(render(transcript, fmt), encoding="utf-8")
    return path


def write_all_exports(session_id: str, transcript: Transcript) -> list[Path]:
    """Write all supported export formats (D8)."""
    return [write_export(session_id, transcript, fmt) for fmt in FORMATS]
