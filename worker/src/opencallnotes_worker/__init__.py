"""OpenCallNotes worker: local recording + on-device transcription.

The package is import-safe everywhere: native dependencies (PortAudio via
``sounddevice``, Apple Silicon ``mlx_whisper``) are imported lazily inside their
backend implementations so importing :mod:`opencallnotes_worker` never requires
audio hardware or MLX.
"""

__version__ = "0.1.0"
