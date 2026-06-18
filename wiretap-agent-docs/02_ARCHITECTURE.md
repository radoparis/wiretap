# Architecture

## High-level system

```text
OpenCallNotes.app
  SwiftUI UI
    ├── Recording controls
    ├── Session library
    ├── Transcript viewer
    └── Preferences

  Local worker bridge
    ├── start recording
    ├── stop recording
    ├── list audio devices
    ├── transcribe session
    └── export transcript

  Python worker
    ├── audio capture
    ├── ffmpeg normalization
    ├── mlx-whisper transcription
    ├── whisper.cpp fallback later
    ├── session metadata
    └── exporters

  Local storage
    ├── SQLite index
    └── session folders
```

## Why SwiftUI + Python
SwiftUI gives a native macOS app and better handling of macOS permissions. Python gives the fastest path to local AI transcription using MLX Whisper.

## Process model
For MVP, SwiftUI launches Python worker commands as subprocesses.

Later, replace with a long-running local daemon if needed.

## Data flow

```text
User clicks Start
  -> SwiftUI calls Python worker start-recording
  -> Worker creates session folder
  -> Worker records WAV
  -> SwiftUI shows timer

User clicks Stop
  -> SwiftUI calls worker stop-recording
  -> Worker closes WAV
  -> Session appears in list

User clicks Transcribe
  -> SwiftUI calls worker transcribe
  -> Worker runs mlx-whisper
  -> Worker writes transcript.json/txt/md/srt
  -> SwiftUI reloads session detail
```

## Audio capture strategy
### MVP
Use Python `sounddevice` or equivalent PortAudio binding.

Supported input modes:
- Microphone only.
- System audio if user selects BlackHole as input.
- Combined audio if the user creates a macOS aggregate/multi-output device.

### Later
Add a native Swift ScreenCaptureKit helper for system audio capture without requiring BlackHole.

## Storage layout

```text
~/Library/Application Support/OpenCallNotes/
  opencallnotes.sqlite
  recordings/
    2026-06-18_22-15-03_client-call/
      session.json
      audio.wav
      transcript.json
      transcript.txt
      transcript.md
      transcript.srt
```

## Session metadata

```json
{
  "id": "2026-06-18_22-15-03_client-call",
  "title": "Client call",
  "created_at": "2026-06-18T22:15:03+02:00",
  "duration_seconds": 2531,
  "audio_file": "audio.wav",
  "language": "auto",
  "model": "mlx-community/whisper-large-v3-turbo",
  "status": "recorded|transcribing|transcribed|failed"
}
```

