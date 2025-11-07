# Buildozer Debug Guide

## Finding the Actual Build Error

When buildozer fails, it often hides the real error in the log. Here's how to find it:

### Method 1: Run with verbose logging

```bash
cd ~/IPTV-Saba
buildozer -v android debug 2>&1 | tee build_log.txt
```

This will save all output to `build_log.txt`. Then search for errors:

```bash
# Search for common error patterns
grep -i "error" build_log.txt | tail -20
grep -i "failed" build_log.txt | tail -20
grep -i "fatal" build_log.txt | tail -20
```

### Method 2: Check buildozer log level

Edit `buildozer.spec` and set:
```ini
log_level = 2
```

Then run:
```bash
buildozer android debug
```

### Method 3: Check specific error logs

Look in these locations:
```bash
# Python-for-Android build log
cat .buildozer/android/platform/build-*/build.log | tail -100

# Last command output
cat .buildozer/android/platform/build-*/compile.log | tail -100
```

## Common Build Errors and Solutions

### 1. Python 3 Compilation Errors

**Error**: `undeclared name: long` or similar C compilation errors

**Solution**:
- Make sure you're using the master branch of p4a
- Check `buildozer.spec`: `p4a.branch = master`

### 2. NDK Version Mismatch

**Error**: NDK version not found or incompatible

**Solution**:
```bash
# Verify NDK installation
ls ~/Android/ndk/

# Update buildozer.spec to match your NDK version
android.ndk = 25b
```

### 3. Missing Dependencies

**Error**: Package not found during build

**Solution**:
```bash
# Install missing system dependencies (Ubuntu/WSL)
sudo apt-get update
sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip \
                        autoconf libtool pkg-config zlib1g-dev \
                        libncurses5-dev libncursesw5-dev libtinfo5 \
                        cmake libffi-dev libssl-dev
```

### 4. Out of Memory

**Error**: Build killed or crashes

**Solution** (for WSL):
- Create/edit `.wslconfig` in Windows user directory:
```ini
[wsl2]
memory=8GB
processors=4
```
- Restart WSL: `wsl --shutdown` in Windows PowerShell

### 5. Cython Compilation Errors

**Error**: Cython build failures

**Solution**:
```bash
# Clean buildozer cache completely
buildozer android clean

# Remove old packages
rm -rf ~/.buildozer/android/packages/*

# Try build again
buildozer android debug
```

## Full Clean Build (Nuclear Option)

If nothing else works:

```bash
cd ~/IPTV-Saba

# Delete all buildozer data
rm -rf .buildozer/
rm -rf ~/.buildozer/

# Clean pip cache
pip cache purge

# Reinstall buildozer
pip install --upgrade --force-reinstall buildozer

# Try building again
buildozer android debug
```

## Checking Your Build Environment

Run this to verify your setup:

```bash
echo "=== Build Environment Check ==="
echo "Python version: $(python3 --version)"
echo "Java version: $(java -version 2>&1 | head -1)"
echo "Buildozer version: $(buildozer --version)"
echo "NDK path: $ANDROID_NDK_HOME"
echo "NDK exists: $([ -d "$ANDROID_NDK_HOME" ] && echo "YES" || echo "NO")"
echo "SDK path: $(grep 'ANDROIDSDK' ~/.buildozer/android/platform/build-*/state.db 2>/dev/null || echo 'Not built yet')"
```

## Getting Help

If you're still stuck, provide these files:
1. Full build log: `buildozer -v android debug 2>&1 | tee build_log.txt`
2. Buildozer spec: `cat buildozer.spec`
3. Environment: Run the environment check above
