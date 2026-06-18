# Privacy

OpenCallNotes is local-first by design.

- **Audio stays on your Mac.** Recordings are written to
  `~/Library/Application Support/OpenCallNotes/recordings/` and are never uploaded.
- **Transcription is on-device.** The default flow uses MLX Whisper running locally on
  Apple Silicon. No transcript or audio is sent to any server.
- **No paid APIs, no accounts, no telemetry.** The app makes no network calls in its
  default flow. (Downloading a Whisper model the first time you transcribe is the only
  network access, and it comes from the model host you configure.)
- **Recording is never hidden.** A red indicator and live timer are shown while
  recording. There is no secret/background recording mode.
- **Audio is never deleted automatically.** You control your files.

## Legal note

Recording laws vary by jurisdiction and may require the consent of some or all
participants. Make sure you have the right to record under the laws and rules that
apply to you.
