# Definition of Done

## MVP is done when
- App launches on macOS.
- User can record audio.
- User can stop recording.
- Session is saved locally.
- User can transcribe locally without paid API.
- Transcript is visible in UI.
- User can export transcript.
- README explains setup.
- Known limitations are documented.

## Quality gates
- No cloud calls in default flow.
- No paid service dependency.
- Audio files are never uploaded.
- No hidden recording.
- Errors are user-readable.
- Core code has basic tests where practical.

## Manual test script
1. Install dependencies.
2. Launch app.
3. Select MacBook microphone.
4. Record 30 seconds.
5. Stop recording.
6. Transcribe.
7. Export Markdown.
8. Verify transcript file exists.
9. If BlackHole is installed, repeat using BlackHole input.

