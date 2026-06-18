# Tech Stack

## macOS app
- Swift 5+
- SwiftUI
- macOS 14+ target unless compatibility is easy

## Python worker
- Python 3.11+
- `uv` for environment management
- `sounddevice` for audio capture
- `numpy`
- `soundfile` or `wave`
- `ffmpeg` for conversion/normalization
- `mlx-whisper` for transcription on Apple Silicon
- `pydantic` for session metadata
- `typer` for worker CLI

## Optional/fallback
- `whisper.cpp` for portable transcription
- BlackHole 2ch for system audio routing

## Packaging
MVP can run in developer mode.
Do not block on perfect app signing/notarization.

Later:
- Bundle Python worker inside app.
- Add installer instructions.
- Add Homebrew cask if useful.

