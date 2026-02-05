#!/usr/bin/env bash
set -euo pipefail

# NYX iOS IPA Build Script (Real Device)
# Builds a signed .xcarchive and exports an installable IPA.

PROJECT_PATH="apps/nyx-ios/NYXPortal.xcodeproj"
SCHEME="NYXPortal"
BUILD_DIR="release_artifacts/ios"
ARCHIVE_PATH="$BUILD_DIR/NYXPortal.xcarchive"
EXPORT_PATH="$BUILD_DIR/IPA"
EXPORT_OPTIONS_PLIST="${NYX_IOS_EXPORT_OPTIONS_PLIST:-build_ios/ExportOptions.plist}"

TEAM_ID="${NYX_IOS_TEAM_ID:-}"
EXPORT_METHOD="${NYX_IOS_EXPORT_METHOD:-development}" # development | ad-hoc | app-store | enterprise
SIGNING_STYLE="${NYX_IOS_SIGNING_STYLE:-automatic}"   # automatic | manual
ALLOW_PROVISIONING_UPDATES="${NYX_IOS_ALLOW_PROVISIONING_UPDATES:-1}"

mkdir -p "$BUILD_DIR" "build_ios"

detect_team_id() {
  local candidate=""
  if command -v security >/dev/null 2>&1; then
    candidate="$(security find-identity -v -p codesigning 2>/dev/null | awk -F'[()]' '/Apple Development|iPhone Developer|Apple Distribution/ {print $2; exit}')"
  fi
  if [[ -z "$candidate" ]] && command -v xcodebuild >/dev/null 2>&1; then
    candidate="$(xcodebuild -project "$PROJECT_PATH" -scheme "$SCHEME" -showBuildSettings 2>/dev/null | awk -F' = ' '/DEVELOPMENT_TEAM/ {print $2; exit}')"
  fi
  echo "$candidate"
}

if [[ -z "$TEAM_ID" ]]; then
  TEAM_ID="$(detect_team_id)"
fi

if [[ -z "$TEAM_ID" && -z "${NYX_IOS_EXPORT_OPTIONS_PLIST:-}" ]]; then
  echo "❌ No Team ID detected for real-device signing."
  echo "   Fix: sign in to Xcode (Settings → Accounts) and re-run."
  echo "   Or export NYX_IOS_TEAM_ID=ABCDE12345"
  echo "   Optional: NYX_IOS_EXPORT_METHOD=development|ad-hoc|app-store|enterprise"
  exit 1
fi

ALLOW_FLAG=()
if [[ "${ALLOW_PROVISIONING_UPDATES}" == "1" ]]; then
  ALLOW_FLAG=(-allowProvisioningUpdates)
fi
TEAM_FLAG=()
if [[ -n "$TEAM_ID" ]]; then
  TEAM_FLAG=(DEVELOPMENT_TEAM="${TEAM_ID}")
fi

echo "📱 Archiving iOS App for Real Device..."
xcodebuild archive \
  -project "$PROJECT_PATH" \
  -scheme "$SCHEME" \
  -configuration Release \
  -destination "generic/platform=iOS" \
  -archivePath "$ARCHIVE_PATH" \
  "${ALLOW_FLAG[@]}" \
  "${TEAM_FLAG[@]}"

echo "✅ Archive created at: $ARCHIVE_PATH"

if [[ -z "${NYX_IOS_EXPORT_OPTIONS_PLIST:-}" ]]; then
  if [[ -z "$TEAM_ID" ]]; then
    echo "❌ Export requires a Team ID or a custom ExportOptions plist."
    exit 1
  fi
  cat > "$EXPORT_OPTIONS_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>method</key>
  <string>${EXPORT_METHOD}</string>
  <key>signingStyle</key>
  <string>${SIGNING_STYLE}</string>
  <key>teamID</key>
  <string>${TEAM_ID}</string>
  <key>compileBitcode</key>
  <false/>
  <key>stripSwiftSymbols</key>
  <true/>
</dict>
</plist>
EOF
fi

echo "📦 Exporting IPA..."
xcodebuild -exportArchive \
  -archivePath "$ARCHIVE_PATH" \
  -exportPath "$EXPORT_PATH" \
  -exportOptionsPlist "$EXPORT_OPTIONS_PLIST" \
  "${ALLOW_FLAG[@]}"

IPA_PATH="$(find "$EXPORT_PATH" -name "*.ipa" -type f | head -n 1 || true)"
if [[ -z "$IPA_PATH" ]]; then
  echo "❌ IPA export failed (no IPA found). Check provisioning/profile settings."
  exit 1
fi

cp -f "$IPA_PATH" "$BUILD_DIR/NYXPortal.ipa"
echo "✅ IPA ready at: $BUILD_DIR/NYXPortal.ipa"
