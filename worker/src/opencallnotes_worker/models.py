"""Pydantic data models for sessions, devices, and transcripts."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

SessionStatus = Literal["recording", "recorded", "transcribing", "transcribed", "failed"]

# Default model matches 02_ARCHITECTURE.md.
DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


class Device(BaseModel):
    """An audio input device."""

    id: str
    name: str
    input_channels: int


class Session(BaseModel):
    """Session metadata, persisted as ``session.json`` (canonical, see D4)."""

    id: str
    title: str
    created_at: str
    duration_seconds: float = 0.0
    audio_file: str = "audio.wav"
    language: str = "auto"
    model: str = DEFAULT_MODEL
    status: SessionStatus = "recording"


class TranscriptSegment(BaseModel):
    """A single timestamped transcript segment."""

    id: int
    start: float
    end: float
    text: str


class Transcript(BaseModel):
    """A full transcript, persisted as ``transcript.json``."""

    language: str
    model: str
    duration_seconds: float
    text: str
    segments: list[TranscriptSegment] = Field(default_factory=list)


def slugify(value: str) -> str:
    """Return a filesystem-safe slug for a human title (ASCII, hyphenated)."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_only).strip("-").lower()
    return slug or "session"


def new_session_id(title: str, now: datetime) -> str:
    """Build a session id of the form ``YYYY-MM-DD_HH-MM-SS_slug``."""
    stamp = now.strftime("%Y-%m-%d_%H-%M-%S")
    return f"{stamp}_{slugify(title)}"
