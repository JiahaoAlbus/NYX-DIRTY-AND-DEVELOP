#!/usr/bin/env bash
set -euo pipefail

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RELEASE_DIR="release_artifacts"
SEED=123
RUN_ID="smoke-${TIMESTAMP}"
SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git log -1 --format=%ct 2>/dev/null || date +%s)}"
export TZ=UTC

touch_epoch() {
  local epoch="$1"
  shift
  local test_file
  test_file="$(mktemp)"
  if touch -d "@${epoch}" "${test_file}" 2>/dev/null; then
    find "$@" -type f -exec touch -d "@${epoch}" {} +
  else
    local ts
    ts="$(date -u -r "${epoch}" +"%Y%m%d%H%M.%S")"
    find "$@" -type f -exec touch -t "${ts}" {} +
  fi
  rm -f "${test_file}"
}

mkdir -p "${RELEASE_DIR}/web" "${RELEASE_DIR}/backend" "${RELEASE_DIR}/extension" "${RELEASE_DIR}/ios" "${RELEASE_DIR}/proof"

echo "--- Phase 1: Verification ---"
bash scripts/nyx_verify_all.sh --seed "$SEED" --run-id "$RUN_ID"
bash scripts/nyx_pack_proof_artifacts.sh

echo "--- Phase 2: Web Portal Build ---"
cd nyx-world
npm install
npm run build
cd ..
rm -f "${RELEASE_DIR}/web/nyx-portal-dist.zip"
touch_epoch "${SOURCE_DATE_EPOCH}" nyx-world/dist
(
  cd nyx-world
  find dist -type f | LC_ALL=C sort | zip -X -@ "../${RELEASE_DIR}/web/nyx-portal-dist.zip"
)
cat <<EOF > ${RELEASE_DIR}/web/INSTALL_WEB.md
# NYX Portal Web Installation
1. Extract nyx-portal-dist.zip
2. Serve static files using any web server (e.g., 'npx serve -s dist')
3. Ensure backend is running at http://127.0.0.1:8091
EOF

echo "--- Phase 2b: Update iOS WebBundle ---"
bash scripts/build_nyx_world.sh

echo "--- Phase 3: Extension Build ---"
rm -f "${RELEASE_DIR}/extension/nyx-extension.zip"
find packages/extension -type f | LC_ALL=C sort | zip -X -@ "${RELEASE_DIR}/extension/nyx-extension.zip"
cat <<EOF > ${RELEASE_DIR}/extension/INSTALL_EXTENSION.md
# NYX Extension Installation
1. Extract nyx-extension.zip
2. Open Chrome -> Extensions -> Enable Developer Mode
3. Click 'Load unpacked' and select the extracted folder
4. Verify 'window.ethereum' is available in console
EOF

echo "--- Phase 4: iOS Build (Simulator) ---"
IOS_BUILD_STATUS="skipped"
if command -v xcodebuild >/dev/null 2>&1; then
  if xcodebuild -license check >/dev/null 2>&1; then
    DERIVED_DATA="$(pwd)/build_ios/DerivedData-${TIMESTAMP}"
    rm -rf "$DERIVED_DATA"
    xcodebuild -project apps/nyx-ios/NYXPortal.xcodeproj -scheme NYXPortal -destination 'generic/platform=iOS Simulator' -derivedDataPath "$DERIVED_DATA" build
    APP_PATH="$(find "$DERIVED_DATA" -name "NYXPortal.app" -type d | head -n 1 || true)"
    if [[ -z "${APP_PATH:-}" ]]; then
      echo "WARN: NYXPortal.app not found under $DERIVED_DATA" >&2
    else
      rm -rf "${RELEASE_DIR}/ios/NYXPortal.app"
      cp -R "$APP_PATH" "${RELEASE_DIR}/ios/NYXPortal.app"
      IOS_BUILD_STATUS="built"
    fi
  else
    echo "WARN: Xcode license not accepted. Skipping iOS simulator build." >&2
  fi
else
  echo "WARN: xcodebuild not found. Skipping iOS simulator build." >&2
fi
if [[ "${IOS_BUILD_STATUS}" != "built" ]]; then
  rm -rf "${RELEASE_DIR}/ios/NYXPortal.app"
fi
cat <<EOF > ${RELEASE_DIR}/ios/INSTALL_IOS.md
# NYX iOS Installation
Status: simulator build ${IOS_BUILD_STATUS}.
1. Use Xcode to run on simulator or device.
2. For an installable iPhone IPA, set a Team ID and run: 'bash scripts/build_ios_ipa.sh'.
3. Example:
   - export NYX_IOS_TEAM_ID=YOUR_TEAM_ID
   - export NYX_IOS_EXPORT_METHOD=development
   - bash scripts/build_ios_ipa.sh
4. If Team ID is unknown, sign in to Xcode (Settings → Accounts) and re-run; the script will try auto-detect.
5. Install IPA via Xcode Devices & Simulators, Apple Configurator, or ideviceinstaller.
EOF

echo "--- Phase 5: Backend Packaging ---"
TAR_BIN="tar"
if command -v gtar >/dev/null 2>&1; then
  if gtar --help 2>/dev/null | grep -q -- "--sort"; then
    TAR_BIN="gtar"
  fi
fi
touch_epoch "${SOURCE_DATE_EPOCH}" apps/nyx-backend apps/nyx-backend-gateway packages
if "${TAR_BIN}" --help 2>/dev/null | grep -q -- "--sort"; then
  "${TAR_BIN}" --sort=name --mtime="@${SOURCE_DATE_EPOCH}" --owner=0 --group=0 --numeric-owner -czf \
    "${RELEASE_DIR}/backend/nyx-backend.tar.gz" \
    apps/nyx-backend apps/nyx-backend-gateway packages
else
  echo "WARN: ${TAR_BIN} lacks --sort support; using sorted file list for deterministic ordering." >&2
  TAR_LIST="$(mktemp)"
  find apps/nyx-backend apps/nyx-backend-gateway packages -type f | LC_ALL=C sort > "${TAR_LIST}"
  if "${TAR_BIN}" --help 2>/dev/null | grep -q -- "--mtime"; then
    "${TAR_BIN}" --mtime="@${SOURCE_DATE_EPOCH}" --owner=0 --group=0 --numeric-owner -czf \
      "${RELEASE_DIR}/backend/nyx-backend.tar.gz" -T "${TAR_LIST}"
  else
    "${TAR_BIN}" --owner=0 --group=0 --numeric-owner -czf \
      "${RELEASE_DIR}/backend/nyx-backend.tar.gz" -T "${TAR_LIST}"
  fi
  rm -f "${TAR_LIST}"
fi
cat <<EOF > ${RELEASE_DIR}/backend/INSTALL_BACKEND.md
# NYX Backend Installation
1. Extract nyx-backend.tar.gz
2. Install dependencies: 'pip install -e packages/l0-identity -e apps/nyx-backend-gateway'
3. Run: 'python -m nyx_backend_gateway.server'
EOF

echo "--- Phase 6: Finalizing Release ---"
cat <<EOF > ${RELEASE_DIR}/RELEASE_NOTES_TESTNET_PORTAL_V1.md
# NYX Testnet Portal v1 Release Notes
- Native iOS shell (Home/Wallet native; Trade/Chat/Store/Proof via embedded web; Settings)
- Web Portal modules + dApp Browser (open tab + optional embed)
- Browser Extension (MV3) with EIP-1193 provider
- Backend pagination and activity feed hardening
- Verifiable proof artifacts included
EOF

cd ${RELEASE_DIR}
python ../scripts/generate_sbom.py sbom.json
python ../scripts/generate_manifest.py . manifest.json
find . -type f -not -name "SHA256SUMS.txt" -exec sha256sum {} + > SHA256SUMS.txt
cd ..

echo "--- Release Artifacts Ready in ${RELEASE_DIR}/ ---"
ls -R ${RELEASE_DIR}
