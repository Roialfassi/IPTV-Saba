#!/bin/bash
# Build diagnostics script to find the actual error

echo "=== Buildozer Build Diagnostics ==="
echo ""

# Find the build log
BUILD_LOG=$(find ~/.buildozer -name "build.log" -type f 2>/dev/null | head -1)

if [ -z "$BUILD_LOG" ]; then
    echo "❌ No build.log found. The build may not have started properly."
    echo ""
    echo "Checking for other log files..."
    find ~/.buildozer -name "*.log" -type f 2>/dev/null
    exit 1
fi

echo "✓ Found build log: $BUILD_LOG"
echo ""

# Check for common error patterns
echo "=== Checking for ERROR messages ==="
grep -i "error:" "$BUILD_LOG" | tail -20

echo ""
echo "=== Checking for FAILED messages ==="
grep -i "failed" "$BUILD_LOG" | tail -20

echo ""
echo "=== Checking for recipe issues ==="
grep -i "recipe" "$BUILD_LOG" | grep -i "error\|failed\|not found" | tail -10

echo ""
echo "=== Last 50 lines of build log ==="
tail -50 "$BUILD_LOG"

echo ""
echo "=== Full log location: $BUILD_LOG ==="
