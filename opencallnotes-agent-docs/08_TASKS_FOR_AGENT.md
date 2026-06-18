# Tasks for Autonomous Agent

## Operating instruction
Do not ask the user questions. Make reasonable decisions and keep going.

## Task 1 — Bootstrap repository
Create the full repo structure from `04_REPO_STRUCTURE.md`.

Acceptance criteria:
- `README.md` exists.
- `LICENSE` exists.
- `DECISIONS.md` exists.
- `worker` package installs with `uv sync`.
- SwiftUI app opens in Xcode.

## Task 2 — Implement worker device listing
Implement:
```bash
opencallnotes-worker devices --json
```

Acceptance criteria:
- Lists macOS input devices.
- Does not crash if BlackHole is missing.

## Task 3 — Implement recording
Implement:
```bash
opencallnotes-worker record start ...
opencallnotes-worker record stop ...
```

Acceptance criteria:
- Produces `audio.wav`.
- Writes `session.json`.
- Handles Ctrl+C safely.

## Task 4 — Implement transcription
Implement local transcription with `mlx-whisper`.

Acceptance criteria:
- Produces `transcript.json`.
- Produces readable `transcript.txt`.
- Handles Polish/English/French.

## Task 5 — Implement exporters
Formats:
- TXT
- Markdown
- SRT
- JSON

Acceptance criteria:
- Exports are written to session folder.

## Task 6 — Build SwiftUI main screen
Acceptance criteria:
- Device dropdown works.
- Start/stop button works.
- Session appears after stop.

## Task 7 — Build session detail
Acceptance criteria:
- Shows metadata.
- Shows transcript after transcription.
- Export buttons work.

## Task 8 — Polish MVP
Acceptance criteria:
- Clear errors.
- README install/run instructions work.
- All core flows documented.

