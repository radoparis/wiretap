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
uv run pyinstaller --noconfirm --clean --onedir \
    --name opencallnotes-worker \
    --collect-all mlx \
    --collect-all mlx_whisper \
    --collect-all sounddevice \
    --collect-all tiktoken \
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
DMG="${DIST}/${APP_NAME}-${VERSION}.dmg"
hdiutil create -volname "${APP_NAME}" -srcfolder "${STAGING}" -ov -format UDZO "${DMG}"
rm -rf "${STAGING}"

echo ""
echo "==> Done: ${DMG}"
ls -lh "${DMG}"
