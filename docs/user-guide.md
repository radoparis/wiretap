# User Guide

OpenCallNotes records conversations on your Mac and transcribes them on-device. No
account, no cloud upload.

## First run

1. Launch **OpenCallNotes**.
2. Open **Settings** (Cmd-,) and set the **Worker path** (see
   [dev-guide](dev-guide.md) — for a source checkout, point it at
   `scripts/run-worker.sh`).
3. Pick your **default language** and **model**.

## Recording

Pick a **mode**:

### Just me (v0.1)
1. Type a **session title** and choose your **microphone**.
2. Click **Start Recording**. A red timer shows elapsed time.
3. Click **Stop Recording**. The session appears in the list.

### Call — mic + system (v0.2)
Records **both sides of a call** with no BlackHole setup: your microphone as **"Me"**
and the call's audio as **"Them"**, on separate tracks. The transcript is then labeled
by speaker.
1. Switch the mode to **Call (mic + system)** and title it.
2. Click **Start Call Recording**. The first time, macOS asks for the **Screen
   Recording** permission — grant it in System Settings → Privacy & Security → Screen
   Recording, then start again.
3. Click **Stop**. Transcribe to get a **Me / Them** labeled transcript.

> OpenCallNotes records audio locally on your Mac. Make sure you have the right to
> record the conversation under the laws and rules that apply to you.

## Transcribing

1. Select a session.
2. Click **Transcribe**. Transcription runs locally and may take a while the first
   time (the model is downloaded once).
3. The transcript appears with timestamps. Use **Re-transcribe** to run again (e.g.
   after changing the model or language in Settings).

## Exporting

In the session detail, click **TXT**, **MD**, **SRT**, or **JSON**. The file is
written into the session folder and revealed in Finder. Use **Open recordings folder**
to browse all sessions.

## System audio (BlackHole)

macOS does not let apps capture other apps' audio without help. For the MVP:

1. Install [BlackHole 2ch](https://github.com/ExistentialAudio/BlackHole).
2. Route your call/app audio to BlackHole (a Multi-Output Device lets you still hear
   it), or create an Aggregate Device combining your mic + BlackHole.
3. Select BlackHole (or the aggregate) as the input device in OpenCallNotes.

Native system-audio capture (ScreenCaptureKit) is planned for a later version.

## Privacy

Everything stays on your Mac. See [privacy.md](privacy.md).
