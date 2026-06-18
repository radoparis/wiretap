# OpenCallNotes

OpenCallNotes is a local-first macOS app for recording conversations and generating
transcripts on your Mac — no paid APIs, no cloud upload.

> **Status:** Working MVP. The Python worker is implemented and tested (ruff + mypy +
> 45 passing tests, no audio hardware required). The SwiftUI app was authored without a
> Mac to compile on, and has since been **built and run successfully on Apple Silicon**
> by the project owner — recording and on-device transcription confirmed working. See
> the manual validation procedure in [`docs/dev-guide.md`](docs/dev-guide.md).

## How this was built

OpenCallNotes was implemented **fully autonomously by a Claude agent**
(Anthropic's Claude Opus 4.8), working from the product and architecture specification
in [`opencallnotes-agent-docs/`](opencallnotes-agent-docs/), which was **authored by GPT‑5.5**. The
agent read the spec, made and documented its own implementation decisions
([`DECISIONS.md`](DECISIONS.md)), wrote all of the code and tests, and ran the quality
gates. The human's role — as the spec itself defined — was to run the app on macOS,
grant permissions, validate behavior, and report bugs.

In the spirit of honesty:
- The **Python worker** was written *and verified* by the agent (ruff, mypy, 45 tests)
  in a Linux environment using hardware‑free test backends.
- The **SwiftUI macOS app** was written by the agent but **never compiled or run by
  it** (no macOS in its build environment). Compilation and real‑world validation —
  including the live transcription progress and MLX Whisper path — were done by the
  human owner on an Apple Silicon Mac.

## Download (macOS, Apple Silicon)

Grab the latest `.dmg` from the [**Releases**](../../releases) page, open it, and drag
**OpenCallNotes** to Applications. The Python worker (recording + MLX Whisper
transcription) is bundled inside the app — **no Python or uv install needed**.

First launch: the app is ad-hoc signed but not notarized, so macOS Gatekeeper asks
once — **right-click the app → Open**, or run
`xattr -dr com.apple.quarantine /Applications/OpenCallNotes.app`. Then grant the
microphone prompt and start recording.

Releases are built by [`.github/workflows/release.yml`](.github/workflows/release.yml)
when a `v*` tag is pushed (see [`docs/dev-guide.md`](docs/dev-guide.md#releasing)).

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

GNU General Public License v3.0 — see [`LICENSE`](LICENSE).
