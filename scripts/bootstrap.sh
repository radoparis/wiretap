#!/usr/bin/env bash
# One-time developer setup for OpenCallNotes.
#
# Installs the Python worker environment and reports on optional native
# dependencies (ffmpeg, MLX, XcodeGen). Safe to re-run.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> Checking prerequisites"
command -v uv >/dev/null 2>&1 || {
    echo "uv is required. Install with: brew install uv" >&2
    exit 1
}

echo "==> Syncing the Python worker (worker/)"
uv sync --project "${REPO_ROOT}/worker"

echo "==> Optional dependencies"
command -v ffmpeg   >/dev/null 2>&1 && echo "  ffmpeg:   ok" || echo "  ffmpeg:   missing (brew install ffmpeg)"
command -v xcodegen >/dev/null 2>&1 && echo "  xcodegen: ok" || echo "  xcodegen: missing (brew install xcodegen)"

case "$(uname -s)" in
    Darwin)
        echo "  MLX transcription: enable with 'uv sync --project worker --extra audio --extra mlx'"
        ;;
    *)
        echo "  note: real audio capture + MLX transcription require macOS (Apple Silicon)."
        echo "        Use OPENCALLNOTES_AUDIO_BACKEND=synthetic / _TRANSCRIBE_BACKEND=fake to test."
        ;;
esac

echo "==> Done. Try: ./scripts/run-worker.sh devices --json"
