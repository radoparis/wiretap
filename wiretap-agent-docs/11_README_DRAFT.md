# OpenCallNotes

OpenCallNotes is a local-first macOS app for recording conversations and generating transcripts on your Mac without paid APIs or cloud upload.

## Goals
- Record conversations locally.
- Transcribe locally.
- Keep user data private.
- Provide a simple macOS UI.
- Stay open source.

## MVP features
- macOS SwiftUI app.
- Local Python worker.
- Microphone recording.
- Optional system audio capture via BlackHole.
- Local transcription using MLX Whisper.
- Export TXT, Markdown, SRT, JSON.

## Development setup

```bash
brew install ffmpeg
brew install uv
cd worker
uv sync
uv run opencallnotes-worker devices --json
```

## System audio capture
For MVP, install BlackHole 2ch and configure your call audio to route through it.

Later versions may include native ScreenCaptureKit system audio capture.

## Privacy
OpenCallNotes stores recordings and transcripts locally. The default workflow does not upload audio or transcript data.

## Legal note
Make sure you have the right to record a conversation under the laws and rules that apply to you.

## License
MIT

