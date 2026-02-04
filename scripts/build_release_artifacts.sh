#!/usr/bin/env bash
set -euo pipefail

# Configuration
VERSION="v1.0.0-testnet"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RELEASE_DIR="release_artifacts"
SEED=123
RUN_ID="smoke-${TIMESTAMP}"

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
zip -r "${RELEASE_DIR}/web/nyx-portal-dist.zip" nyx-world/dist
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
zip -r "${RELEASE_DIR}/extension/nyx-extension.zip" packages/extension
cat <<EOF > ${RELEASE_DIR}/extension/INSTALL_EXTENSION.md
# NYX Extension Installation
1. Extract nyx-extension.zip
2. Open Chrome -> Extensions -> Enable Developer Mode
3. Click 'Load unpacked' and select the extracted folder
4. Verify 'window.ethereum' is available in console
EOF

echo "--- Phase 4: iOS Build (Simulator) ---"
DERIVED_DATA="$(pwd)/build_ios/DerivedData-${TIMESTAMP}"
rm -rf "$DERIVED_DATA"
xcodebuild -project apps/nyx-ios/NYXPortal.xcodeproj -scheme NYXPortal -destination 'generic/platform=iOS Simulator' -derivedDataPath "$DERIVED_DATA" build
APP_PATH="$(find "$DERIVED_DATA" -name "NYXPortal.app" -type d | head -n 1 || true)"
if [[ -z "${APP_PATH:-}" ]]; then
  echo "WARN: NYXPortal.app not found under $DERIVED_DATA" >&2
else
  rm -rf "${RELEASE_DIR}/ios/NYXPortal.app"
  cp -R "$APP_PATH" "${RELEASE_DIR}/ios/NYXPortal.app"
fi
cat <<EOF > ${RELEASE_DIR}/ios/INSTALL_IOS.md
# NYX iOS Installation
1. Use Xcode to run on simulator or device.
2. For IPA export, Apple Developer signing is required.
3. Once signed, use 'xcodebuild -exportArchive' with ExportOptions.plist.
EOF

echo "--- Phase 5: Backend Packaging ---"
tar -czf "${RELEASE_DIR}/backend/nyx-backend.tar.gz" apps/nyx-backend apps/nyx-backend-gateway packages
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
find . -type f -not -name "SHA256SUMS.txt" -exec sha256sum {} + > SHA256SUMS.txt
cd ..

echo "--- Release Artifacts Ready in ${RELEASE_DIR}/ ---"
ls -R ${RELEASE_DIR}
