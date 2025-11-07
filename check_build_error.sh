#!/bin/bash
# Script to diagnose buildozer build errors

echo "=== Buildozer Build Error Diagnostic ==="
echo ""

# Find the correct python-for-android build directory
# Look for directories with 'build' in the name but exclude NDK build directories
BUILD_DIR=$(find ~/.buildozer/android/platform/ -type d -path "*/python-for-android/build/*" -o -path "*/build-arm*" | grep -v "ndk" | grep -v "vulkan" | head -1)

# If not found, try alternative locations
if [ -z "$BUILD_DIR" ]; then
    BUILD_DIR=$(find ./.buildozer/android/platform/ -type d -name "build-arm*" 2>/dev/null | head -1)
fi

if [ -z "$BUILD_DIR" ]; then
    echo "No build directory found. Have you run buildozer yet?"
    echo "Checking for any .buildozer directory..."
    if [ -d ".buildozer" ] || [ -d "$HOME/.buildozer" ]; then
        echo "Buildozer directory exists. Listing structure:"
        find ./.buildozer ~/.buildozer -maxdepth 4 -type d 2>/dev/null | head -20
    fi
    exit 1
fi

echo "Build directory: $BUILD_DIR"
echo ""

# Check for Python compilation errors
echo "=== Checking for Python compilation errors ==="
if [ -f "$BUILD_DIR/build.log" ]; then
    grep -i "error:" "$BUILD_DIR/build.log" | tail -20
    echo ""
fi

# Check for recipe failures
echo "=== Checking for recipe failures ==="
find "$BUILD_DIR" -name "*.log" -exec grep -l "FAILED" {} \; 2>/dev/null | while read logfile; do
    echo "Error found in: $logfile"
    tail -30 "$logfile"
    echo "---"
done

# Check for Cython errors
echo "=== Checking for Cython errors ==="
find "$BUILD_DIR" -name "*.c" -o -name "*.log" | xargs grep -l "undeclared\|implicit declaration" 2>/dev/null | head -5 | while read errfile; do
    echo "Compilation error in: $errfile"
    grep -A 3 -B 3 "error:" "$errfile" | head -20
    echo "---"
done

# Check p4a version
echo "=== Python-for-Android Info ==="
P4A_DIR="$BUILD_DIR/packages/python-for-android"
if [ -d "$P4A_DIR" ]; then
    cd "$P4A_DIR"
    echo "P4A branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
    echo "P4A commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    echo "P4A remote: $(git remote get-url origin 2>/dev/null || echo 'unknown')"
fi

echo ""
echo "=== Environment ==="
echo "NDK: $ANDROID_NDK_HOME"
echo "SDK: $ANDROIDSDK"
echo "Python: $(python3 --version)"

echo ""
echo "=== Recommendations ==="
echo "1. Check the errors above for specific issues"
echo "2. Try: buildozer android clean"
echo "3. If Cython errors, try: rm -rf ~/.buildozer/android/packages/*"
echo "4. For full clean: rm -rf .buildozer/ ~/.buildozer/"
echo "5. See BUILDOZER_DEBUG.md for more solutions"
