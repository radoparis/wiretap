# Product Specification

## Product name
OpenCallNotes

## One-liner
A free, local-first macOS app for recording conversations and generating transcripts on-device.

## Target user
People who want private meeting/call notes without subscriptions or uploading audio to cloud services.

## MVP scope
### Must have
- Native macOS UI.
- Start/stop recording.
- Record microphone.
- Support system audio via BlackHole input device if installed.
- Session list.
- Session detail view.
- Local transcription.
- Export transcript as TXT, Markdown, JSON, and SRT.
- Basic preferences: model, language, input device.

### Should have
- Auto-detect BlackHole.
- Show recording timer.
- Show transcription progress.
- Keep audio and transcript together in one session folder.
- Re-run transcription.

### Not in MVP
- Perfect speaker diarization.
- Live transcription.
- Cloud sync.
- Mobile app.
- Team accounts.
- Automatic meeting bot joining calls.

## UX principles
- One big obvious button: Start Recording / Stop Recording.
- No account.
- No onboarding wall.
- Explain that everything is local.
- Never delete audio automatically.
- Always make files discoverable.

## Compliance and privacy copy
The app should include a short notice:

> OpenCallNotes records audio locally on your Mac. Make sure you have the right to record the conversation under the laws and rules that apply to you.

Do not build secret recording features.
Do not hide recording status.

