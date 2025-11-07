# Buildozer Build Troubleshooting Guide

## Error: "Buildozer failed to execute the last command"

This generic error means the actual error is in the build log. Follow these steps:

### Step 1: Find the Real Error

```bash
cd ~/IPTV-Saba
./diagnose_build.sh
```

Or manually check:
```bash
# Find build log
find ~/.buildozer -name "build.log" -type f

# View last 100 lines
tail -100 ~/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build.log

# Search for errors
grep -i "error" ~/.buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build.log | tail -20
```

---

## Common Errors and Solutions

### 1. "Recipe for X not found"

**Error Example**: `No such recipe: aiohttp`

**Solution**: Some packages don't have Android recipes. Replace or remove them:

```ini
# In buildozer.spec, simplify requirements:
requirements = python3,kivy,pillow,requests,android

# Remove: aiohttp, chardet, pyyaml, python-dateutil if they cause issues
```

**Alternative**: Use pure-Python versions or find working recipes.

---

### 2. "Cython compilation error"

**Error Example**: `Cython.Compiler.Errors.CompileError`

**Solution**: Update Cython version:

```bash
pip install --upgrade cython==0.29.36
```

---

### 3. "NDK/SDK not found"

**Error Example**: `Android NDK is not installed`

**Solution**: Let buildozer auto-download:

```bash
# Clean and rebuild
rm -rf ~/.buildozer/android/platform/android-ndk*
rm -rf ~/.buildozer/android/platform/android-sdk*

buildozer android debug
```

---

### 4. "Gradle build failed"

**Error Example**: `BUILD FAILED` from Gradle

**Solutions**:

```bash
# 1. Clean gradle cache
rm -rf ~/.gradle

# 2. Increase build timeout in buildozer.spec
# android.gradle_dependencies =
# android.gradle_build_timeout = 600

# 3. Update Java version (needs Java 8 or 11)
java -version
```

---

### 5. "Permission denied" errors

**Solution**:

```bash
# Fix permissions
chmod -R 755 ~/.buildozer
chmod +x ~/.buildozer/android/platform/apache-ant-*/bin/ant
```

---

### 6. Requirements Installation Fails

**Error Example**: `Could not install requirement X`

**Quick Fix - Minimal Requirements**:

Edit `buildozer.spec`:

```ini
# Ultra-minimal working requirements
requirements = python3,kivy==2.3.0,pillow,android

# Add back one at a time:
# requirements = python3,kivy==2.3.0,pillow,requests,android
# requirements = python3,kivy==2.3.0,pillow,requests,pyyaml,android
```

---

### 7. "Could not find function xmlCheckVersion"

**Error Example**: libxml2 errors

**Solution**:

```bash
# Install libxml2 dependencies
sudo apt-get update
sudo apt-get install -y libxml2-dev libxslt-dev
```

---

### 8. "No space left on device"

**Solution**:

```bash
# Check disk space
df -h

# Clean old builds
buildozer android clean
rm -rf ~/.buildozer/android/platform/build-*

# WSL specific - check Windows disk space
```

---

## Recommended Build Process

### Option 1: Minimal Build (Fastest)

```bash
cd ~/IPTV-Saba

# Edit buildozer.spec - use minimal requirements
# requirements = python3,kivy==2.3.0,pillow,android

# Clean build
rm -rf .buildozer/
buildozer android debug
```

### Option 2: Full Build with Network Libraries

```bash
cd ~/IPTV-Saba

# Edit buildozer.spec
# requirements = python3,kivy==2.3.0,pillow,requests,android

# Clean and build
rm -rf .buildozer/
buildozer -v android debug 2>&1 | tee build.log
```

### Option 3: Debug Build Issues

```bash
# Run with maximum verbosity
buildozer -v android debug

# If it fails, run diagnostic
./diagnose_build.sh

# Check specific package
buildozer android p4a -- recipes --compact
```

---

## Current Requirements Analysis

Your current `buildozer.spec` has:
```ini
requirements = python3,kivy,pillow,requests,aiohttp,chardet,pyyaml,python-dateutil,android
```

**Potential Issues**:

1. **aiohttp**: Requires complex C dependencies, may not have working Android recipe
2. **chardet**: Should work but may have issues
3. **pyyaml**: Requires PyYAML recipe which can be problematic
4. **python-dateutil**: Usually works but adds complexity

**Recommendation**: Start minimal and add back:

```ini
# Phase 1: Test basic build
requirements = python3,kivy==2.3.0,pillow,android

# Phase 2: Add networking (if Phase 1 works)
requirements = python3,kivy==2.3.0,pillow,requests,android

# Phase 3: Add data handling (if Phase 2 works)
requirements = python3,kivy==2.3.0,pillow,requests,pyyaml,python-dateutil,android

# Phase 4: Try complex libs (if Phase 3 works)
requirements = python3,kivy==2.3.0,pillow,requests,pyyaml,python-dateutil,aiohttp,chardet,android
```

---

## Quick Diagnostic Commands

```bash
# Check python-for-android recipes available
buildozer android p4a -- recipes

# Check buildozer version
buildozer --version

# Check python version in buildozer
python3 --version

# List what's been built
ls -la ~/.buildozer/android/platform/build-*/

# Check Android tools
ls ~/.buildozer/android/platform/android-*/
```

---

## If All Else Fails

### Nuclear Option - Complete Clean

```bash
# Remove everything buildozer-related
rm -rf ~/.buildozer/
rm -rf .buildozer/

# Update buildozer
pip uninstall buildozer
pip install buildozer

# Update Cython
pip install --upgrade cython==0.29.36

# Minimal build
buildozer android debug
```

---

## Next Steps

1. **Run diagnostic**: `./diagnose_build.sh`
2. **Identify error**: Look for specific error message
3. **Apply fix**: Match error to solution above
4. **Test build**: Try minimal requirements first
5. **Add features**: Gradually add back requirements

**Remember**: Copy the actual error message from the build log to get specific help!
