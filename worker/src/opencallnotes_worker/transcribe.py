"""On-device transcription: pluggable backends (D3).

``MlxWhisperBackend`` runs MLX Whisper on Apple Silicon. ``FakeBackend`` is a
deterministic placeholder used in tests/CI so the record -> transcribe -> export
flow can be exercised without MLX or audio hardware.
"""

from __future__ import annotations

import contextlib
import os
import time
from pathlib import Path
from typing import Protocol

from . import paths
from .audio import wav_duration_seconds
from .models import Transcript, TranscriptSegment
from .progress import (
    ProgressCallback,
    StdoutProgressParser,
    clear_progress,
    write_progress,
)
from .store import SessionStore


class TranscribeError(RuntimeError):
    """Raised on transcription failures."""


def _normalize_language(language: str) -> str | None:
    """Map the ``auto`` sentinel to ``None`` (let the model detect)."""
    return None if language.lower() == "auto" else language


class TranscriptionBackend(Protocol):
    def transcribe(
        self, *, audio_path: Path, model: str, language: str,
        progress: ProgressCallback | None = None,
    ) -> Transcript: ...


class MlxWhisperBackend:
    """Real on-device transcription via ``mlx_whisper`` (lazy import)."""

    def transcribe(
        self, *, audio_path: Path, model: str, language: str,
        progress: ProgressCallback | None = None,
    ) -> Transcript:
        try:
            import mlx_whisper
        except Exception as exc:  # pragma: no cover - requires Apple Silicon
            raise TranscribeError(
                "mlx-whisper is not installed. Install the 'mlx' extra on Apple "
                "Silicon, or set OPENCALLNOTES_TRANSCRIBE_BACKEND=fake."
            ) from exc

        total = wav_duration_seconds(audio_path)
        # verbose=True makes mlx-whisper print each segment as it is decoded; we
        # capture that stream to derive real progress and keep it off stdout.
        sink: contextlib.AbstractContextManager[object]
        if progress is not None:
            sink = contextlib.redirect_stdout(StdoutProgressParser(total, progress))
        else:
            sink = contextlib.nullcontext()
        with sink:
            result = mlx_whisper.transcribe(
                str(audio_path),
                path_or_hf_repo=model,
                language=_normalize_language(language),
                verbose=True,
            )
        if progress is not None:
            progress(total, total)
        segments = [
            TranscriptSegment(
                id=int(seg.get("id", index)),
                start=float(seg.get("start", 0.0)),
                end=float(seg.get("end", 0.0)),
                text=str(seg.get("text", "")).strip(),
            )
            for index, seg in enumerate(result.get("segments", []))
        ]
        return Transcript(
            language=str(result.get("language") or language),
            model=model,
            duration_seconds=wav_duration_seconds(audio_path),
            text=str(result.get("text", "")).strip(),
            segments=segments,
        )


class FakeBackend:
    """Deterministic placeholder transcript derived from audio duration (D3)."""

    def transcribe(
        self, *, audio_path: Path, model: str, language: str,
        progress: ProgressCallback | None = None,
    ) -> Transcript:
        duration = wav_duration_seconds(audio_path)
        lang = _normalize_language(language) or "en"
        segments: list[TranscriptSegment] = []
        window = 5.0
        index = 0
        start = 0.0
        # Pace the synthetic run so progress is observable when requested.
        paced = progress is not None and os.environ.get("OPENCALLNOTES_FAKE_PACE") == "1"
        while start < max(duration, window):
            end = min(start + window, duration) if duration else window
            segments.append(
                TranscriptSegment(
                    id=index,
                    start=round(start, 3),
                    end=round(end, 3),
                    text=f"[synthetic transcript segment {index}]",
                )
            )
            if progress is not None:
                progress(min(end, duration) if duration else end, duration)
            if paced:
                time.sleep(0.05)
            index += 1
            start += window
            if duration and start >= duration:
                break
        text = " ".join(seg.text for seg in segments)
        return Transcript(
            language=lang, model=model, duration_seconds=duration, text=text, segments=segments
        )


def get_backend() -> TranscriptionBackend:
    """Select the transcription backend from ``OPENCALLNOTES_TRANSCRIBE_BACKEND``."""
    backend = os.environ.get("OPENCALLNOTES_TRANSCRIBE_BACKEND", "mlx")
    if backend == "fake":
        return FakeBackend()
    if backend == "mlx":
        return MlxWhisperBackend()
    raise TranscribeError(f"unknown transcription backend: {backend!r}")


def transcribe_session(
    store: SessionStore,
    session_id: str,
    *,
    model: str | None = None,
    language: str | None = None,
) -> Transcript:
    """Transcribe a recorded session and persist ``transcript.json`` (+ exports)."""
    from .export import write_all_exports  # local import avoids a cycle

    session = store.read_session(session_id)
    folder = paths.session_dir(session_id)
    audio_path = folder / session.audio_file
    if not audio_path.exists():
        raise TranscribeError(f"audio file missing for session {session_id}")

    chosen_model = model or session.model
    chosen_language = language or session.language

    session.status = "transcribing"
    session.model = chosen_model
    session.language = chosen_language
    store.write_session(session)

    def report(processed: float, total: float) -> None:
        write_progress(folder, processed, total)

    try:
        transcript = get_backend().transcribe(
            audio_path=audio_path,
            model=chosen_model,
            language=chosen_language,
            progress=report,
        )
    except Exception:
        session.status = "failed"
        store.write_session(session)
        raise
    finally:
        clear_progress(folder)

    (folder / "transcript.json").write_text(
        transcript.model_dump_json(indent=2), encoding="utf-8"
    )
    write_all_exports(session_id, transcript)

    session.status = "transcribed"
    session.language = transcript.language
    store.write_session(session)
    return transcript
