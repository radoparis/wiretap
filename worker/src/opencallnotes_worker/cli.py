"""Typer CLI: the JSON subprocess contract used by the SwiftUI app (D7).

Every command accepts ``--json/--no-json`` (default JSON). In JSON mode it prints
exactly one JSON object to stdout; failures print ``{"error": {...}}`` and exit
non-zero.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime
from typing import Any

import typer

from . import audio, devices, export
from .models import DEFAULT_MODEL
from .paths import PathSafetyError
from .store import SessionNotFoundError, SessionStore, load_transcript_dict
from .transcribe import TranscribeError, transcribe_session

app = typer.Typer(
    name="opencallnotes-worker",
    help="Local recording + on-device transcription worker for OpenCallNotes.",
    no_args_is_help=True,
    add_completion=False,
)
record_app = typer.Typer(help="Recording lifecycle.", no_args_is_help=True)
sessions_app = typer.Typer(help="Session library.", no_args_is_help=True)
app.add_typer(record_app, name="record")
app.add_typer(sessions_app, name="sessions")

_ERROR_CODES: dict[type[Exception], str] = {
    SessionNotFoundError: "session_not_found",
    PathSafetyError: "invalid_session_id",
    export.ExportError: "invalid_format",
    TranscribeError: "transcribe_failed",
    audio.RecordingError: "recording_failed",
}


def _emit(
    payload: dict[str, Any], *, json_out: bool, human: Callable[[dict[str, Any]], str]
) -> None:
    typer.echo(json.dumps(payload) if json_out else human(payload))


def _run(
    json_out: bool,
    produce: Callable[[], dict[str, Any]],
    human: Callable[[dict[str, Any]], str],
) -> None:
    try:
        payload = produce()
    except Exception as exc:  # noqa: BLE001 - converted to a structured error contract
        code = next(
            (c for t, c in _ERROR_CODES.items() if isinstance(exc, t)), "internal_error"
        )
        if json_out:
            typer.echo(json.dumps({"error": {"code": code, "message": str(exc)}}))
        else:
            typer.echo(f"error [{code}]: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    _emit(payload, json_out=json_out, human=human)


# -- devices --------------------------------------------------------------


@app.command(name="devices")
def devices_cmd(json_out: bool = typer.Option(True, "--json/--no-json")) -> None:  # noqa: FBT001
    """List audio input devices."""

    def produce() -> dict[str, Any]:
        return {"devices": [d.model_dump() for d in devices.list_input_devices()]}

    def human(p: dict[str, Any]) -> str:
        rows = p["devices"]
        if not rows:
            return "No input devices found."
        return "\n".join(f"{d['id']:>4}  {d['name']} ({d['input_channels']}ch)" for d in rows)

    _run(json_out, produce, human)


# -- record ---------------------------------------------------------------


@record_app.command("start")
def record_start(
    device_id: str = typer.Option(..., "--device-id"),
    title: str = typer.Option("Untitled", "--title"),
    language: str = typer.Option("auto", "--language"),
    model: str = typer.Option(DEFAULT_MODEL, "--model"),
    samplerate: int = typer.Option(audio.DEFAULT_SAMPLERATE, "--samplerate"),
    channels: int = typer.Option(audio.DEFAULT_CHANNELS, "--channels"),
    json_out: bool = typer.Option(True, "--json/--no-json"),  # noqa: FBT001
) -> None:
    """Start a recording (spawns a detached recorder process)."""

    def produce() -> dict[str, Any]:
        store = SessionStore()
        session = audio.start_recording(
            store,
            title=title,
            device_id=device_id,
            language=language,
            model=model,
            now=datetime.now().astimezone(),
            samplerate=samplerate,
            channels=channels,
        )
        return {"session_id": session.id, "status": session.status}

    _run(json_out, produce, lambda p: f"recording: {p['session_id']}")


@record_app.command("stop")
def record_stop(
    session_id: str = typer.Option(..., "--session-id"),
    json_out: bool = typer.Option(True, "--json/--no-json"),  # noqa: FBT001
) -> None:
    """Stop a recording and finalize the session."""

    def produce() -> dict[str, Any]:
        store = SessionStore()
        session = audio.stop_recording(store, session_id)
        return {
            "session_id": session.id,
            "status": session.status,
            "duration_seconds": session.duration_seconds,
        }

    _run(json_out, produce, lambda p: f"recorded {p['session_id']} ({p['duration_seconds']}s)")


@app.command(name="_record-run", hidden=True)
def record_run(
    session_id: str = typer.Option(..., "--session-id"),
    device_id: str = typer.Option(..., "--device-id"),
    samplerate: int = typer.Option(audio.DEFAULT_SAMPLERATE, "--samplerate"),
    channels: int = typer.Option(audio.DEFAULT_CHANNELS, "--channels"),
) -> None:
    """Internal: the detached recorder subprocess body. Not for direct use."""
    audio.run_recorder(
        session_id, device_id=device_id, samplerate=samplerate, channels=channels
    )


# -- sessions -------------------------------------------------------------


@sessions_app.command("list")
def sessions_list(json_out: bool = typer.Option(True, "--json/--no-json")) -> None:  # noqa: FBT001
    """List recorded sessions."""

    def produce() -> dict[str, Any]:
        store = SessionStore()
        return {"sessions": [s.model_dump() for s in store.list_sessions()]}

    def human(p: dict[str, Any]) -> str:
        rows = p["sessions"]
        if not rows:
            return "No recordings yet."
        return "\n".join(
            f"{s['created_at']}  {s['status']:<12} {s['title']}" for s in rows
        )

    _run(json_out, produce, human)


@sessions_app.command("get")
def sessions_get(
    session_id: str = typer.Argument(...),
    json_out: bool = typer.Option(True, "--json/--no-json"),  # noqa: FBT001
) -> None:
    """Show a session, including its transcript if available."""

    def produce() -> dict[str, Any]:
        store = SessionStore()
        session = store.read_session(session_id)
        transcript = load_transcript_dict(session_id)
        payload = session.model_dump()
        payload["transcript_available"] = transcript is not None
        payload["transcript"] = transcript
        return payload

    _run(json_out, produce, lambda p: json.dumps(p, indent=2))


@sessions_app.command("reindex")
def sessions_reindex(json_out: bool = typer.Option(True, "--json/--no-json")) -> None:  # noqa: FBT001
    """Rebuild the SQLite index from session folders."""

    def produce() -> dict[str, Any]:
        return {"indexed": SessionStore().reindex()}

    _run(json_out, produce, lambda p: f"indexed {p['indexed']} sessions")


# -- transcribe / export --------------------------------------------------


@app.command()
def transcribe(
    session_id: str = typer.Argument(...),
    model: str | None = typer.Option(None, "--model"),
    language: str | None = typer.Option(None, "--language"),
    json_out: bool = typer.Option(True, "--json/--no-json"),  # noqa: FBT001
) -> None:
    """Transcribe a recorded session on-device."""

    def produce() -> dict[str, Any]:
        store = SessionStore()
        transcript = transcribe_session(store, session_id, model=model, language=language)
        return {
            "session_id": session_id,
            "status": "transcribed",
            "language": transcript.language,
            "duration_seconds": transcript.duration_seconds,
            "segments": len(transcript.segments),
        }

    _run(json_out, produce, lambda p: f"transcribed {p['session_id']} ({p['segments']} segments)")


@app.command(name="export")
def export_cmd(
    session_id: str = typer.Argument(...),
    fmt: str = typer.Option("md", "--format"),
    json_out: bool = typer.Option(True, "--json/--no-json"),  # noqa: FBT001
) -> None:
    """Export a session's transcript to a single format."""

    def produce() -> dict[str, Any]:
        from .models import Transcript

        data = load_transcript_dict(session_id)
        if data is None:
            raise TranscribeError(f"session {session_id} has no transcript yet")
        transcript = Transcript.model_validate(data)
        path = export.write_export(session_id, transcript, fmt)
        return {"session_id": session_id, "format": fmt, "path": str(path)}

    _run(json_out, produce, lambda p: p["path"])


if __name__ == "__main__":
    app()
