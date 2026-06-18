"""Audio input device enumeration.

Uses ``sounddevice`` (PortAudio) when available. Never crashes if PortAudio or
BlackHole is missing (Task 2 acceptance criteria) — it returns whatever it can,
plus the always-present synthetic device.
"""

from __future__ import annotations

import os

from .models import Device

# A virtual device that the synthetic audio backend records from. Always listed
# so the worker is usable (and testable) without any real input hardware.
SYNTHETIC_DEVICE = Device(id="synthetic", name="Synthetic (silent test input)", input_channels=1)


def list_input_devices() -> list[Device]:
    """Return available audio input devices.

    The synthetic device is included only when the audio backend is synthetic, so
    production listings show real hardware while tests/CI still have an input.
    """
    devices: list[Device] = []
    devices.extend(_list_real_input_devices())
    if os.environ.get("OPENCALLNOTES_AUDIO_BACKEND", "sounddevice") == "synthetic":
        devices.append(SYNTHETIC_DEVICE)
    return devices


def _list_real_input_devices() -> list[Device]:
    try:
        import sounddevice
    except Exception:
        # PortAudio not installed / not available. Not an error (Task 2).
        return []

    try:
        raw = sounddevice.query_devices()
    except Exception:
        return []

    result: list[Device] = []
    for index, info in enumerate(raw):
        channels = int(info.get("max_input_channels", 0))
        if channels < 1:
            continue
        result.append(
            Device(id=str(index), name=str(info.get("name", f"Device {index}")),
                   input_channels=channels)
        )
    return result
