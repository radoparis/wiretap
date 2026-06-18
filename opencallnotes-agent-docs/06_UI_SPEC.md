# UI Specification

## Main window

### Header
- App title: OpenCallNotes
- Recording status indicator
- Preferences button

### Recording panel
Fields:
- Session title text field
- Input device dropdown
- Language dropdown: Auto, English, Polish, French, Spanish, German, Italian
- Model dropdown

Primary button:
- Start Recording
- Stop Recording while active

Secondary:
- Open recordings folder

### Recent sessions list
Each row:
- Title
- Date/time
- Duration
- Status
- Transcript availability

## Session detail
- Title editable later; MVP can be static.
- Audio file path.
- Buttons:
  - Transcribe
  - Re-transcribe
  - Export TXT
  - Export Markdown
  - Export SRT
  - Export JSON
- Transcript viewer with timestamps.

## Preferences
- Recordings folder.
- Default language.
- Default model.
- Worker path.
- ffmpeg path.
- BlackHole detection status.

## Empty states
No sessions:
> No recordings yet. Start your first recording.

No BlackHole:
> System audio capture requires BlackHole or an aggregate input device in MVP.

