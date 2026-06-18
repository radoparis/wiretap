# Implementation Plan

## Phase 0 — Repo bootstrap
- Create repo structure.
- Add MIT or Apache-2.0 license. Default: MIT.
- Add README.
- Add worker `pyproject.toml` with `uv`.
- Add SwiftUI macOS project.

## Phase 1 — Python worker MVP
- Implement device listing.
- Implement session folder creation.
- Implement microphone recording to WAV.
- Implement stop recording.
- Implement session metadata.
- Implement session listing.
- Implement transcription with `mlx-whisper`.
- Implement exports.

Definition of Done:
- CLI can record and transcribe a local session.

## Phase 2 — SwiftUI UI MVP
- Build main window.
- Call worker `devices`.
- Start/stop recording from UI.
- List sessions.
- Open session detail.
- Trigger transcription.
- Display transcript.
- Export transcript.

Definition of Done:
- Full end-to-end flow works from UI.

## Phase 3 — Usability
- Recording timer.
- Progress indicator during transcription.
- Better error messages.
- Auto-detect BlackHole.
- Open recordings folder.

## Phase 4 — Packaging
- Bundle worker.
- Add bootstrap script.
- Add signed/notarized build later, not required for MVP.

## Phase 5 — Advanced
- Live chunked transcription.
- Native ScreenCaptureKit helper.
- Speaker labels.
- Search across transcripts.
- Summaries using local LLM.

