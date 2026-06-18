# Decision Policy for Agent

## General rule
Do not block on preference questions. Decide and continue.

## Decision hierarchy
1. Working product beats elegant design.
2. Local-first beats convenience.
3. Free/open-source beats paid dependency.
4. Native macOS UX beats cross-platform abstraction for MVP.
5. Simpler implementation beats broader compatibility.

## Defaults
- License: MIT.
- App name: OpenCallNotes.
- SwiftUI for UI.
- Python worker.
- MLX Whisper for Apple Silicon.
- Store under `~/Library/Application Support/OpenCallNotes`.
- Use JSON subprocess protocol.

## When blocked
Only stop if:
- Required OS permission cannot be granted by the agent.
- Hardware/audio device is missing.
- Dependency cannot be installed.

If blocked, write:
- What failed.
- Exact command/output.
- Best next workaround.

