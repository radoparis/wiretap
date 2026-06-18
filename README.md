# OpenCallNotes

OpenCallNotes is a local-first macOS app for recording conversations and generating
transcripts on your Mac — no paid APIs, no cloud upload.

> **Status:** MVP. The Python worker is implemented and tested (ruff + mypy + 39
> passing tests, no audio hardware required). The SwiftUI app is implemented as
> portable source generated via XcodeGen; it has **not yet been compiled/run on
> macOS** — see the manual validation procedure in
> [`docs/dev-guide.md`](docs/dev-guide.md) and [`DECISIONS.md`](DECISIONS.md) (D10).

## What it does

- Native macOS SwiftUI app with one obvious **Start / Stop Recording** button.
- Records your **microphone**, or **system audio** via BlackHole / an aggregate device.
- Transcribes locally with **MLX Whisper** (Apple Silicon).
- Exports transcripts as **TXT, Markdown, SRT, JSON**.
- Keeps audio + transcripts together in one per-session folder. No account, no telemetry.

## Architecture

A SwiftUI app drives a small Python worker as a subprocess over a JSON contract:

```
app-macos/   SwiftUI UI + WorkerClient (subprocess bridge)
worker/      opencallnotes-worker: recording, on-device transcription, exports
```

See [`docs/architecture.md`](docs/architecture.md) for the as-built design.

## Quick start (worker)

The worker runs and is fully testable on any OS using hardware-free backends:

```bash
brew install uv                 # or: pip install uv
cd worker
uv sync
export OPENCALLNOTES_AUDIO_BACKEND=synthetic
export OPENCALLNOTES_TRANSCRIBE_BACKEND=fake
uv run opencallnotes-worker devices --json
```

On Apple Silicon, install the real backends and ffmpeg:

```bash
brew install ffmpeg
uv sync --extra audio --extra mlx
uv run opencallnotes-worker devices --json
```

## Quick start (macOS app)

```bash
brew install xcodegen
./scripts/run-app-dev.sh        # generates the Xcode project and opens it
```

Then in Xcode: set your signing team, Build & Run, and in the app's Settings point the
**Worker path** at `scripts/run-worker.sh`. Full steps: [`docs/user-guide.md`](docs/user-guide.md).

## Privacy

Audio and transcripts stay on your Mac; the default flow makes no network calls and
uploads nothing. See [`docs/privacy.md`](docs/privacy.md).

## Legal note

Make sure you have the right to record a conversation under the laws and rules that
apply to you. OpenCallNotes never records secretly — recording status is always shown.

## Development

```bash
cd worker && uv run ruff check . && uv run mypy && uv run pytest
```

Conventions and the manual macOS validation procedure are in
[`docs/dev-guide.md`](docs/dev-guide.md). Build decisions are logged in
[`DECISIONS.md`](DECISIONS.md).

## License

MIT — see [`LICENSE`](LICENSE).
