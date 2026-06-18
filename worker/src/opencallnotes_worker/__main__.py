"""Enable ``python -m opencallnotes_worker`` (used by the detached recorder, D1)."""

from __future__ import annotations

from .cli import app

if __name__ == "__main__":
    app()
