#!/usr/bin/env bash
# Build a downloadable, self-contained OpenCallNotes.app + .dmg (macOS, Apple Silicon).
#
# Produces dist/OpenCallNotes-<version>.dmg containing OpenCallNotes.app with the
# Python worker bundled inside it (PyInstaller), so end users need no Python/uv.
#
# Runs in CI (.github/workflows/release.yml) and locally:
#   ./scripts/build-release.sh [version]
#
# Requirements: macOS, Xcode, uv, xcodegen. (brew install uv xcodegen)
#
# NOTE: the app is ad-hoc signed (no paid Apple Developer ID). Gatekeeper will
# quarantine it on download; users open it via right-click -> Open once, or run
#   xattr -dr com.apple.quarantine /Applications/OpenCallNotes.app
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-${RELEASE_VERSION:-0.0.0-dev}}"
APP_NAME="OpenCallNotes"
DIST="${REPO_ROOT}/dist"
APP_BUILD="${REPO_ROOT}/app-macos/build"

echo "==> Building ${APP_NAME} ${VERSION}"
rm -rf "${DIST}" "${APP_BUILD}" "${REPO_ROOT}/worker/dist" "${REPO_ROOT}/worker/build"
mkdir -p "${DIST}"

# 1) Standalone worker binary (with real audio + MLX transcription) ------------
echo "==> [1/5] Building standalone worker (PyInstaller)"
pushd "${REPO_ROOT}/worker" >/dev/null
uv sync --extra audio --extra mlx --group packaging
# Only --collect-all packages that are actually importable, so a missing optional
# transitive dependency cannot hard-fail the freeze.
COLLECT_ARGS=()
for pkg in mlx mlx_whisper sounddevice tiktoken numba scipy numpy; do
    if uv run python -c "import ${pkg}" 2>/dev/null; then
        COLLECT_ARGS+=(--collect-all "${pkg}")
        echo "    bundling: ${pkg}"
    else
        echo "    skipping (not importable): ${pkg}"
    fi
done
# mlx-whisper pulls torch as a transitive dep, but only its weight-conversion path
# (torch_whisper.py) uses it; the MLX transcription path does not. Excluding torch &
# friends roughly halves the bundle. If transcription ever breaks with a torch
# ImportError, drop the matching --exclude-module line.
EXCLUDE_ARGS=(
    --exclude-module torch
    --exclude-module torchvision
    --exclude-module torchaudio
    --exclude-module tensorboard
)
uv run pyinstaller --noconfirm --clean --onedir \
    --name opencallnotes-worker \
    "${COLLECT_ARGS[@]}" \
    "${EXCLUDE_ARGS[@]}" \
    packaging/entry.py
popd >/dev/null
WORKER_DIST="${REPO_ROOT}/worker/dist/opencallnotes-worker"
test -x "${WORKER_DIST}/opencallnotes-worker" || {
    echo "ERROR: worker binary not produced at ${WORKER_DIST}" >&2
    exit 1
}

# 2) Generate + build the app (unsigned, no hardened runtime for ad-hoc) -------
echo "==> [2/5] Generating Xcode project and building the app"
pushd "${REPO_ROOT}/app-macos" >/dev/null
xcodegen generate
xcodebuild \
    -project "${APP_NAME}.xcodeproj" \
    -scheme "${APP_NAME}" \
    -configuration Release \
    -derivedDataPath build \
    CODE_SIGNING_ALLOWED=NO \
    CODE_SIGNING_REQUIRED=NO \
    ENABLE_HARDENED_RUNTIME=NO \
    MARKETING_VERSION="${VERSION}" \
    build
popd >/dev/null
APP="${APP_BUILD}/Build/Products/Release/${APP_NAME}.app"
test -d "${APP}" || { echo "ERROR: app not built at ${APP}" >&2; exit 1; }

# 3) Embed the worker inside the app bundle -----------------------------------
echo "==> [3/5] Embedding worker into ${APP_NAME}.app"
RES_WORKER="${APP}/Contents/Resources/worker"
rm -rf "${RES_WORKER}"
mkdir -p "${RES_WORKER}"
cp -R "${WORKER_DIST}/." "${RES_WORKER}/"
chmod +x "${RES_WORKER}/opencallnotes-worker"

# 4) Ad-hoc sign the whole bundle so it launches ------------------------------
echo "==> [4/5] Ad-hoc signing"
codesign --force --deep --sign - "${APP}"
codesign --verify --deep --strict "${APP}" && echo "    signature OK"

# 5) Package a drag-to-Applications DMG ---------------------------------------
echo "==> [5/5] Creating DMG"
STAGING="$(mktemp -d)"
cp -R "${APP}" "${STAGING}/"
ln -s /Applications "${STAGING}/Applications"

# Quarantine helper: the app is ad-hoc signed (not notarized), so a downloaded
# build is quarantined and macOS blocks it from launching its bundled worker.
# This one-click helper clears the quarantine flag and opens the app.
cat > "${STAGING}/Fix & Open OpenCallNotes.command" <<'CMD'
#!/bin/bash
APP="/Applications/OpenCallNotes.app"
if [ ! -d "$APP" ]; then
  echo "Drag OpenCallNotes onto the Applications folder first, then run this again."
  read -r -p "Press Return to close…"
  exit 1
fi
echo "Clearing macOS quarantine on OpenCallNotes…"
xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true
echo "Opening OpenCallNotes…"
open "$APP"
CMD
chmod +x "${STAGING}/Fix & Open OpenCallNotes.command"

cat > "${STAGING}/READ ME FIRST.txt" <<'TXT'
OpenCallNotes — install
=======================

1. Drag OpenCallNotes onto the Applications folder (in this window).

2. Because OpenCallNotes is open-source and not notarized by Apple, macOS
   quarantines it and will otherwise show errors like "Could not parse worker
   output". To fix this in one step:

     • Double-click "Fix & Open OpenCallNotes.command".
       (If macOS blocks it: right-click it → Open → Open.)

   That clears the quarantine flag and launches the app. You only need to do
   this once per install.

   Prefer the terminal? Run:
     xattr -dr com.apple.quarantine /Applications/OpenCallNotes.app

3. On first launch, grant the microphone permission prompt, then record.
   The first transcription downloads the Whisper model once (~a few hundred MB).

Everything runs locally on your Mac. No cloud, no account.
TXT

DMG="${DIST}/${APP_NAME}-${VERSION}.dmg"
hdiutil create -volname "${APP_NAME}" -srcfolder "${STAGING}" -ov -format UDZO "${DMG}"
rm -rf "${STAGING}"

echo ""
echo "==> Done: ${DMG}"
ls -lh "${DMG}"
