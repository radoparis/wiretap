# OpenCallNotes — Autonomous Agent Mission

## Mission
Build an open-source macOS desktop app that records conversations locally and produces local transcripts without paid cloud services.

The app must have a UI. The MVP must prioritize working end-to-end over perfect architecture.

## Non-negotiables
- macOS first.
- Local-first: audio and transcript stay on the user's machine.
- No paid APIs.
- UI required from day one.
- The agent must not ask the user implementation questions unless blocked by credentials or unavailable hardware.
- Make reasonable product/technical decisions and document them in `DECISIONS.md`.
- Prefer shipping a working MVP over designing a perfect system.

## Default decisions
Use these defaults unless there is a clear technical blocker:

- UI: SwiftUI macOS app.
- Backend/worker: Python.
- Transcription: `mlx-whisper` first, `whisper.cpp` as fallback.
- MVP audio capture: microphone plus optional BlackHole system-audio input.
- Storage: local filesystem + SQLite.
- Export formats: `.txt`, `.md`, `.srt`, `.json`.
- First version: record first, transcribe after. Live transcription comes later.

## Operating rule for the agent
Do not ask “which option do you prefer?” Decide.

When uncertain:
1. Pick the simplest option that can ship.
2. Write the decision and tradeoff in `DECISIONS.md`.
3. Continue implementation.

## Completion target
A user can:
1. Launch the macOS app.
2. Select input source.
3. Start recording.
4. Stop recording.
5. See a saved session.
6. Click transcribe.
7. View transcript.
8. Export transcript.

