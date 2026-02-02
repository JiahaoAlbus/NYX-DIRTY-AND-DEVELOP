#!/bin/bash

# NYX No-Fake-UI Gate
# Fails if runtime code contains banned markers.

BANNED_MARKERS=("TODO" "mock" "placeholder" "coming soon" "fake" "sample-data")
EXIT_CODE=0

echo "🔍 Checking for banned markers in runtime code..."

for marker in "${BANNED_MARKERS[@]}"; do
    # Search in apps/ and packages/ and nyx-world/
    # Exclude docs/, tests/, and node_modules/
    FOUND=$(grep -RiE "$marker" apps packages nyx-world --exclude-dir={node_modules,.git,dist,build,release_artifacts,tests} --exclude="*.md" | grep -v "TODO:" || true)
    
    if [ ! -z "$FOUND" ]; then
        echo "❌ Found banned marker '$marker' in:"
        echo "$FOUND"
        EXIT_CODE=1
    fi
done

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ No banned markers found in runtime code."
else
    echo "❌ Banned markers found. Please clean up before release."
fi

exit $EXIT_CODE
