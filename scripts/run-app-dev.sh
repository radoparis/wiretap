#!/usr/bin/env bash
# Generate the Xcode project from app-macos/project.yml and open it.
# Requires XcodeGen (brew install xcodegen) and Xcode.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="${REPO_ROOT}/app-macos"

command -v xcodegen >/dev/null 2>&1 || {
    echo "xcodegen is required. Install with: brew install xcodegen" >&2
    exit 1
}

echo "==> Generating OpenCallNotes.xcodeproj"
(cd "${APP_DIR}" && xcodegen generate)

echo "==> Opening in Xcode"
open "${APP_DIR}/OpenCallNotes.xcodeproj"

cat <<'NOTE'

Next steps in Xcode:
  1. Select the OpenCallNotes scheme and your team for signing (Automatic).
  2. Build & Run (Cmd-R).
  3. In the app, open Settings (Cmd-,) and set the Worker path to
     <repo>/scripts/run-worker.sh, leaving "Worker leading args" empty.
  4. Grant the microphone permission prompt on first record.
NOTE
