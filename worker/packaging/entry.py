"""PyInstaller entry point: produces a standalone `opencallnotes-worker` binary.

Bundled inside the macOS .app so end users need no Python/uv install.
"""

from __future__ import annotations

from opencallnotes_worker.cli import app

if __name__ == "__main__":
    app()
