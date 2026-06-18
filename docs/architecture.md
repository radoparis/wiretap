# Architecture (as built)

This summarizes the **implemented** architecture. The canonical design lives in
[`../opencallnotes-agent-docs/02_ARCHITECTURE.md`](../opencallnotes-agent-docs/02_ARCHITECTURE.md);
build-time choices are in [`../DECISIONS.md`](../DECISIONS.md).

```
OpenCallNotes.app (SwiftUI, app-macos/)
  Views/        RecordingPanel, SessionListView, SessionDetailView, PreferencesView
  Services/     WorkerClient (subprocess + JSON), SessionStore (state), Preferences
        │  spawns, one JSON object per call (no shell)
        ▼
opencallnotes-worker (Python, worker/)
  cli.py        typer commands, JSON contract
  audio.py      detached recorder subprocess; synthetic + sounddevice backends
  transcribe.py mlx-whisper + fake backends
  export.py     TXT / Markdown / SRT / JSON
  store.py      session.json (canonical) + SQLite index
  paths.py      storage-root resolution + path-traversal safety
        │
        ▼
~/Library/Application Support/OpenCallNotes/
  opencallnotes.sqlite
  recordings/<session-id>/
    session.json  audio.wav  transcript.{json,txt,md,srt}  recorder.log
```

## Process & data flow

1. **Start** — the app calls `record start`. The worker creates the session folder,
   writes `session.json` (`status=recording`), and spawns a *detached recorder
   subprocess* (`_record-run`) whose PID is stored in `recording.pid` (D1). The call
   returns immediately so the UI can show a live timer.
2. **Stop** — `record stop` sends the recorder `SIGTERM`, waits for it to close the
   WAV cleanly, computes the duration, and sets `status=recorded`.
3. **Transcribe** — `transcribe` runs the selected backend on `audio.wav`, writes
   `transcript.json` plus all export formats, and sets `status=transcribed`.
4. **Export** — `export` re-renders a single format on demand.

## Backend isolation

Native dependencies are behind small interfaces so the worker is portable and fully
testable without hardware (D3):

| Concern       | Real backend           | Test backend | Selector env var                    |
| ------------- | ---------------------- | ------------ | ----------------------------------- |
| Audio capture | `SoundDeviceRecorder`  | `Synthetic`  | `OPENCALLNOTES_AUDIO_BACKEND`       |
| Transcription | `MlxWhisperBackend`    | `Fake`       | `OPENCALLNOTES_TRANSCRIBE_BACKEND`  |
