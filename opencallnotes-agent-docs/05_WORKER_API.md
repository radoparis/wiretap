# Worker API

The SwiftUI app calls the Python worker as a subprocess.

All commands should support `--json` output.

## Commands

### List devices
```bash
opencallnotes-worker devices --json
```

Output:
```json
{
  "devices": [
    {"id": "0", "name": "MacBook Pro Microphone", "input_channels": 1},
    {"id": "3", "name": "BlackHole 2ch", "input_channels": 2}
  ]
}
```

### Start recording
```bash
opencallnotes-worker record start --device-id 0 --title "Client call" --json
```

Output:
```json
{
  "session_id": "2026-06-18_22-15-03_client-call",
  "status": "recording"
}
```

### Stop recording
```bash
opencallnotes-worker record stop --session-id SESSION_ID --json
```

Output:
```json
{
  "session_id": "SESSION_ID",
  "status": "recorded",
  "duration_seconds": 1234
}
```

### List sessions
```bash
opencallnotes-worker sessions list --json
```

### Read session
```bash
opencallnotes-worker sessions get SESSION_ID --json
```

### Transcribe
```bash
opencallnotes-worker transcribe SESSION_ID --model mlx-community/whisper-large-v3-turbo --language auto --json
```

### Export
```bash
opencallnotes-worker export SESSION_ID --format md --json
```

## Implementation note
If persistent background recording is hard via stateless subprocesses, implement a small worker daemon and keep the CLI as client commands. Do not ask. Decide and document.

