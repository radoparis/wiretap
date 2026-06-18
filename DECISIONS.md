# Decisions

This file records the non-obvious product/technical decisions made while building
OpenCallNotes autonomously, per `wiretap-agent-docs/10_DECISION_POLICY.md`. Each
entry states the choice, the alternatives considered, and the reasoning.

## D1 — Recording across stateless `record start` / `record stop` invocations
**Choice:** `record start` spawns a *detached background recorder subprocess*
(`opencallnotes-worker _record-run`) whose PID is written to `<session>/recording.pid`.
`record stop` sends the recorder `SIGTERM`, waits for a clean shutdown, and finalizes
the WAV + session metadata.

**Alternatives:** (a) a long-running daemon with an IPC socket; (b) keeping the
recording in the foreground of `record start` (impossible — the call must return so the
UI can show a timer and later call `record stop`).

**Reasoning:** `05_WORKER_API.md` explicitly allows a small worker/daemon and says
"Do not ask. Decide and document." A detached subprocess is the simplest thing that
satisfies the start/stop contract without a persistent daemon or socket protocol. The
recorder installs a `SIGTERM`/`SIGINT` handler so the WAV is always closed cleanly,
satisfying Task 3's "Handles Ctrl+C safely."

## D2 — WAV writing via stdlib `wave`, not `soundfile`
**Choice:** Write WAV with Python's stdlib `wave` module.

**Reasoning:** `soundfile` needs the native `libsndfile`, which adds an install
dependency and is not needed for 16-bit PCM WAV. `wave` is dependency-free, portable,
and fully testable on Linux/CI. (Priority order: simplicity + maintainability.)

## D3 — Pluggable audio + transcription backends (macOS adapter isolation)
**Choice:** Audio capture and transcription are behind small backend interfaces:
- Audio: `SoundDeviceRecorder` (real, Apple Silicon / any PortAudio host) and
  `SyntheticRecorder` (generates silence; deterministic, no hardware). Selected via
  `OPENCALLNOTES_AUDIO_BACKEND` (`sounddevice` default, `synthetic` for tests).
- Transcription: `MlxWhisperBackend` (real, lazy-imports `mlx_whisper`) and
  `FakeBackend` (deterministic placeholder). Selected via
  `OPENCALLNOTES_TRANSCRIBE_BACKEND` (`mlx` default, `fake` for tests).

**Reasoning:** `CLAUDE.md` mandates isolating macOS adapters and providing mocks so the
code is portable and the worker logic is testable without Apple Silicon or microphones.
The native imports are lazy so importing the package never requires PortAudio / MLX.

## D4 — `session.json` is canonical; SQLite is a rebuildable index
**Choice:** Each session folder owns the truth in `session.json`. A SQLite database
(`opencallnotes.sqlite`) is an index used to make `sessions list` fast and is upserted
on every write. `sessions reindex` rebuilds it by scanning session folders.

**Reasoning:** `02_ARCHITECTURE.md` lists both a SQLite index and per-session folders.
Folder-as-truth keeps sessions portable/recoverable (delete the DB, reindex). All SQL
is parameterized (security requirement).

## D5 — Storage root resolution / portability
**Choice:** Default storage root is `~/Library/Application Support/OpenCallNotes` on
macOS, `$XDG_DATA_HOME/OpenCallNotes` (or `~/.local/share/OpenCallNotes`) elsewhere,
and is always overridable with `OPENCALLNOTES_HOME`.

**Reasoning:** Matches the architecture doc on macOS while keeping the worker runnable
and testable on Linux/CI. Tests point `OPENCALLNOTES_HOME` at a temp dir.

## D6 — Untrusted `SESSION_ID` is validated against path traversal
**Choice:** Any session id received from the CLI must match `^[A-Za-z0-9_.\-]+$` and the
resolved session directory must stay inside the recordings directory; otherwise the
command fails with `invalid_session_id`.

**Reasoning:** Security requirement — prevents path traversal (e.g. `../../etc`).

## D7 — Machine-readable JSON contract
**Choice:** Every command accepts `--json/--no-json` (default `--json`). In JSON mode it
prints exactly one JSON object to stdout; on failure it prints
`{"error": {"code", "message"}}` and exits non-zero. The SwiftUI client always uses JSON.

**Reasoning:** `05_WORKER_API.md` requires `--json` output and a stable contract for the
Swift subprocess bridge. A single JSON object per call is the simplest robust protocol.

## D8 — Transcribe writes all four formats
**Choice:** `transcribe` writes `transcript.json` plus `.txt`, `.md`, `.srt`. `export`
re-renders a single requested format on demand.

**Reasoning:** Convenience for the UI (`06_UI_SPEC.md` shows all export buttons) at
negligible cost; `export` remains available for re-generation.

## D9 — License: GNU GPL v3.0
The spec (`10_DECISION_POLICY.md`) defaults to MIT, and earlier drafts of this repo's
docs claimed MIT — but the `LICENSE` file actually committed in the initial commit is
**GNU GPL v3.0**, and the project owner chose to **keep GPL‑3.0** (strong copyleft).
All docs and `worker/pyproject.toml` are aligned to GPL‑3.0; the canonical spec under
`wiretap-agent-docs/` is left unedited (it records the original MIT recommendation).

## D10 — Xcode project via XcodeGen; unsandboxed dev-mode app
**Choice:** The Xcode project is defined by `app-macos/project.yml` and generated
with XcodeGen (`xcodegen generate`) rather than hand-maintaining a `.pbxproj`. The
MVP app runs in developer mode with the **App Sandbox disabled** and Hardened Runtime
enabled.

**Reasoning:** This work was authored on Linux where Xcode cannot run, so a
hand-written `.pbxproj` could not be compiled or verified — shipping an unverified
binary project file would violate the "no fake validation" rule. A declarative
`project.yml` is reviewable, regenerable, and avoids `.pbxproj` merge pain. The
sandbox is disabled because the app spawns the Python worker subprocess and reads the
recordings folder directly; sandboxing + notarization is explicitly deferred per
`03_TECH_STACK.md` ("Do not block on perfect app signing/notarization") and
`12_RISKS_AND_LIMITATIONS.md`.

**Honesty note:** The Swift code has NOT been compiled or run (no macOS available in
the build environment). It is written to be portable and is accompanied by a manual
validation procedure in `docs/dev-guide.md`. macOS functionality must be verified by a
human on an Apple Silicon Mac before being claimed as working.

## D11 — Worker launch is shell-free
**Choice:** `WorkerClient` launches the worker with `Process` using an explicit
executable URL + argv array, never `/bin/sh -c`. The default executable is
`/usr/bin/env` with leading arg `opencallnotes-worker` (resolved from `PATH`);
Preferences let a developer point at `scripts/run-worker.sh` instead.

**Reasoning:** Passing a fixed argv means user-entered session titles cannot inject
shell commands (security requirement). `OPENCALLNOTES_HOME` is passed via the child
environment, not interpolated into a command string.

## D12 — Transcription progress via a polled progress file
**Choice:** `transcribe` is a single blocking call, so for live progress the worker
runs Whisper with `verbose=True`, captures the per-segment lines it prints (keeping the
worker's real stdout a clean JSON object), parses each segment's end timestamp, and
writes `<session>/transcribe.progress` = `{processed_seconds, total_seconds, fraction}`.
The app polls that file (every 0.4s) during the call and shows a determinate progress
bar. Progress = processed audio seconds ÷ total duration.

**Alternatives:** (a) streaming incremental JSON from the worker — breaks the
one-object-per-call contract; (b) chunking the audio ourselves to report progress —
risks cutting words mid-segment and degrading accuracy; (c) an indeterminate spinner —
poor UX for long meetings.

**Reasoning:** A file poll is the simplest thing that yields *true* progress without
changing the CLI contract or touching transcription quality. It degrades gracefully:
if the verbose format is unrecognized the bar simply stays at 0% (the call still works).
During the first-run model download no segments are emitted, so the UI shows a
"Preparing… first run downloads the model" message while the fraction is 0.

**Honesty note:** the fake backend's progress path is unit-tested on Linux; the MLX
stdout-parsing path could not be verified on Apple Silicon here and is best-effort.
