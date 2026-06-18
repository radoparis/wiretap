#!/usr/bin/env bash
# Run the OpenCallNotes worker from the source checkout via uv.
#
# Point the app's Preferences -> "Worker path" at this script (and clear the
# leading args) to drive the worker without installing it system-wide.
#
#   ./scripts/run-worker.sh devices --json
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec uv run --project "${REPO_ROOT}/worker" opencallnotes-worker "$@"
