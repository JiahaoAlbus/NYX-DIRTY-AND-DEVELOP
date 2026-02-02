#!/bin/bash
set -e

# NYX iOS IPA Build Script (Real Device)
# Builds the .xcarchive and attempts to export an IPA.

PROJECT_PATH="apps/nyx-ios/NYXPortal.xcodeproj"
SCHEME="NYXPortal"
BUILD_DIR="release_artifacts/ios"
ARCHIVE_PATH="$BUILD_DIR/NYXPortal.xcarchive"
EXPORT_PATH="$BUILD_DIR/IPA"
EXPORT_OPTIONS_PLIST="scripts/ExportOptions.plist"

mkdir -p "$BUILD_DIR"

echo "📱 Archiving iOS App for Real Device..."

# 1. Build Archive
xcodebuild archive \
    -project "$PROJECT_PATH" \
    -scheme "$SCHEME" \
    -configuration Release \
    -archivePath "$ARCHIVE_PATH" \
    CODE_SIGNING_REQUIRED=NO \
    CODE_SIGNING_ALLOWED=NO

echo "✅ Archive created at: $ARCHIVE_PATH"

# 2. Check for Signing Credentials
echo "🔍 Checking for signing credentials..."
if [ ! -f "$EXPORT_OPTIONS_PLIST" ]; then
    echo "⚠️  ExportOptions.plist missing. Creating example..."
    cat > "$EXPORT_OPTIONS_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>development</string>
    <key>signingStyle</key>
    <string>automatic</string>
</dict>
</plist>
EOF
fi

echo "⚠️  To export a signed IPA, you must configure signing in Xcode and update $EXPORT_OPTIONS_PLIST."
echo "⚠️  Skipping IPA export step as signing is required for IPAs."
echo "💡 You can export the IPA manually from the archive in Xcode: Window -> Organizer"

exit 0
