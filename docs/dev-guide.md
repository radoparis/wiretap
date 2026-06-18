# Developer Guide

## Layout

```
worker/        Python worker (typer CLI) — fully buildable/testable on any OS
app-macos/     SwiftUI app (XcodeGen project.yml + Swift sources) — macOS only
scripts/       bootstrap.sh, run-worker.sh, run-app-dev.sh
docs/          this documentation
```

## Worker

```bash
./scripts/bootstrap.sh           # uv sync + dependency report
cd worker
uv run ruff check .
uv run mypy
uv run pytest                    # 39 tests, no audio hardware needed
```

The test suite forces hardware-free backends and an isolated storage root:

```bash
export OPENCALLNOTES_HOME="$(mktemp -d)"
export OPENCALLNOTES_AUDIO_BACKEND=synthetic
export OPENCALLNOTES_TRANSCRIBE_BACKEND=fake
uv run opencallnotes-worker devices --json
```

On Apple Silicon, install the real backends:

```bash
uv sync --extra audio --extra mlx
```

## macOS app

```bash
brew install xcodegen
./scripts/run-app-dev.sh         # generates OpenCallNotes.xcodeproj and opens it
```

The Xcode project is generated from `app-macos/project.yml`; edit the YAML, not the
generated `.xcodeproj`.

> **Status / honesty note.** The Swift code was authored in a Linux build environment
> and has **not been compiled or run**. It is written to be portable, but macOS
> behavior must be verified on a real Apple Silicon Mac before being claimed as
> working (see `../DECISIONS.md` D10). Treat the procedure below as the acceptance
> test a human must perform.

## Manual validation procedure (macOS, Apple Silicon)

Prerequisites: `brew install ffmpeg uv xcodegen`, Xcode installed, `cd worker && uv
sync --extra audio --extra mlx`.

1. **Worker smoke test**
   ```bash
   ./scripts/run-worker.sh devices --json      # lists your real input devices
   ```
2. **Build the app**: `./scripts/run-app-dev.sh`, then Build & Run in Xcode.
3. **Configure**: Settings (Cmd-,) → Worker path = absolute path to
   `scripts/run-worker.sh`, leading args empty.
4. **Record**: choose your microphone, title it, **Start Recording**, speak ~30s,
   **Stop Recording**. Grant the microphone permission prompt. Confirm the session
   appears.
5. **Transcribe**: select the session → **Transcribe**. Confirm a timestamped
   transcript renders (first run downloads the model).
6. **Export**: click **MD**; confirm `transcript.md` opens in Finder with real text.
7. **System audio (optional)**: install BlackHole, select it as input, repeat 4–6.

Report any failure with the exact command/output per `10_DECISION_POLICY.md`.

## Worker JSON contract

Every command prints exactly one JSON object to stdout. Failures print
`{"error": {"code", "message"}}` and exit non-zero. See
`../wiretap-agent-docs/05_WORKER_API.md` and `worker/tests/test_cli.py` for the
exercised contract.
