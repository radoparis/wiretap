# opencallnotes-worker

The local recording + on-device transcription worker for
[OpenCallNotes](../README.md). It is a small `typer` CLI that the macOS SwiftUI app
drives as a subprocess over a JSON contract (see `../opencallnotes-agent-docs/05_WORKER_API.md`).

## Install

```bash
cd worker
uv sync                       # core + dev tools (pytest/ruff/mypy)
uv sync --extra audio --extra mlx   # add real capture + MLX transcription (Apple Silicon)
```

## Run

```bash
uv run opencallnotes-worker devices --json
uv run opencallnotes-worker record start --device-id 0 --title "Client call" --json
uv run opencallnotes-worker record stop --session-id SESSION_ID --json
uv run opencallnotes-worker transcribe SESSION_ID --json
uv run opencallnotes-worker export SESSION_ID --format md --json
```

## Backends

Native dependencies are isolated behind pluggable backends so the worker runs and
is fully tested without audio hardware or Apple Silicon (see `../DECISIONS.md` D3):

| Concern       | Env var                              | Default        | Test value   |
| ------------- | ------------------------------------ | -------------- | ------------ |
| Audio capture | `OPENCALLNOTES_AUDIO_BACKEND`        | `sounddevice`  | `synthetic`  |
| Transcription | `OPENCALLNOTES_TRANSCRIBE_BACKEND`   | `mlx`          | `fake`       |

Storage root is overridable with `OPENCALLNOTES_HOME` (defaults to the macOS
Application Support directory).

## Develop

```bash
uv run ruff check .
uv run mypy
uv run pytest
```
