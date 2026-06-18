# Risks and Limitations

## macOS system audio
MVP relies on BlackHole or aggregate devices for system audio. This is acceptable for v0.1 but not ideal for non-technical users.

Mitigation:
- Add BlackHole detection.
- Add setup instructions.
- Later build native ScreenCaptureKit helper.

## Python packaging inside macOS app
Bundling Python can be annoying.

Mitigation:
- Start with dev-mode worker path.
- Package later.

## Speaker diarization
MVP cannot reliably separate speakers.

Mitigation:
- Use channel labels if mic/system are separate.
- Add diarization later.

## Performance
Large Whisper models may be slow on older Macs.

Mitigation:
- Offer model choices.
- Default to turbo/small depending on hardware.

## Legal/privacy
Recording laws vary.

Mitigation:
- Do not hide recording status.
- Show privacy/legal reminder.
- Keep everything local.

