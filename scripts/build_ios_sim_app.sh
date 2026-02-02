#!/bin/bash
set -e

# NYX iOS Simulator Build Script
# Builds the iOS app for the x86_64/arm64 simulator.

PROJECT_PATH="apps/nyx-ios/NYXPortal.xcodeproj"
SCHEME="NYXPortal"
DESTINATION="platform=iOS Simulator,name=iPhone 15,OS=latest"
BUILD_DIR="release_artifacts/ios"

mkdir -p "$BUILD_DIR"

echo "📱 Building iOS App for Simulator..."

# Use xcodebuild to build for simulator
# We use -quiet to reduce log noise, but remove it if debugging
xcodebuild build \
    -project "$PROJECT_PATH" \
    -scheme "$SCHEME" \
    -destination "$DESTINATION" \
    -configuration Debug \
    -derivedDataPath "build_ios" \
    CODE_SIGNING_ALLOWED=NO

# Copy the built .app to the artifacts directory
APP_PATH=$(find build_ios -name "NYXPortal.app" -type d | head -n 1)
if [ -z "$APP_PATH" ]; then
    echo "❌ Build failed: .app not found."
    exit 1
fi

cp -R "$APP_PATH" "$BUILD_DIR/NYXPortal-Simulator.app"

echo "✅ iOS Simulator app ready at: $BUILD_DIR/NYXPortal-Simulator.app"
