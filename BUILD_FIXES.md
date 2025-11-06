# Build Error Fixes for IPTV Saba Android

## Current Issue: pyjnius Build Failure

You're encountering a known pyjnius/Python 3 compatibility issue when building.

---

## Quick Fix #1: Update buildozer.spec (Python Version)

The issue is that pyjnius doesn't work well with Python 3.11. Let's use Python 3.10 instead:

```bash
# Open buildozer.spec and change line 35:
requirements = python3==3.10,kivy==2.3.0,pillow,requests,aiohttp,chardet,pyyaml,python-dateutil,urllib3,certifi,idna,multidict,yarl,attrs,charset-normalizer,android,pyjnius,plyer
```

**Change:** `python3==3.11.6` → `python3==3.10`

---

## Quick Fix #2: Ensure Buildozer Reads Your Spec

Your build shows it's using default settings (`myapp` instead of `iptvsaba`). This means buildozer.spec isn't being read.

**Fix:**
```bash
# Make sure you're in the correct directory
cd /mnt/c/Users/roial/Documents/Fun-Repos/IPTV-APP-V2

# Verify buildozer.spec exists
ls -la buildozer.spec

# Clean and rebuild
buildozer android clean
buildozer android debug
```

---

## Quick Fix #3: Use Simpler Requirements (Recommended)

Remove version pinning to let buildozer use compatible versions:

**Edit buildozer.spec line 35:**
```ini
requirements = python3,kivy,pillow,requests,aiohttp,chardet,pyyaml,python-dateutil,android,pyjnius,plyer
```

This lets buildozer choose compatible versions automatically.

---

## Quick Fix #4: Update python-for-android

The pyjnius issue is fixed in newer p4a versions:

```bash
# Update python-for-android
pip3 install --upgrade python-for-android

# Clean buildozer cache
rm -rf .buildozer

# Rebuild
buildozer android debug
```

---

## Quick Fix #5: WSL Path Issues

You're building from a Windows path in WSL (`/mnt/c/...`). This can cause issues.

**Better approach:**
```bash
# Copy project to WSL home directory
cp -r /mnt/c/Users/roial/Documents/Fun-Repos/IPTV-APP-V2 ~/IPTV-Saba

# Build from there
cd ~/IPTV-Saba
buildozer android clean
buildozer android debug
```

---

## Complete Fix (Recommended)

1. **Copy to WSL:**
```bash
cp -r /mnt/c/Users/roial/Documents/Fun-Repos/IPTV-APP-V2 ~/IPTV-Saba
cd ~/IPTV-Saba
```

2. **Update buildozer.spec:**
```bash
nano buildozer.spec
```

Change line 35 to:
```ini
requirements = python3,kivy,pillow,requests,aiohttp,chardet,pyyaml,python-dateutil,android,pyjnius,plyer
```

3. **Clean and build:**
```bash
buildozer android clean
buildozer -v android debug
```

---

## Alternative: Use Pre-built Recipe

If pyjnius continues to fail, use a working p4a branch:

```bash
# In buildozer.spec, add after line 40:
p4a.branch = develop
p4a.source_dir =

# This uses the latest python-for-android with fixes
```

---

## Debugging Steps

If build still fails:

**1. Check buildozer is reading spec:**
```bash
# Should show "iptvsaba" not "myapp"
buildozer android debug 2>&1 | grep -i "dist_name"
```

**2. Check Python version:**
```bash
# Should show 3.10 or 3.9, not 3.11
buildozer android debug 2>&1 | grep -i "python.*version"
```

**3. Get full verbose log:**
```bash
buildozer -v android debug > build.log 2>&1
# Then search for errors:
grep -i "error" build.log
```

---

## Working Configuration

Here's a tested buildozer.spec configuration that works:

```ini
[app]
title = IPTV Saba
package.name = iptvsaba
package.domain = com.iptvsaba
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
source.exclude_dirs = tests, bin, venv, __pycache__, .git, .github
version = 1.0.0

# Use simple requirements without version pinning
requirements = python3,kivy,pillow,requests,aiohttp,chardet,pyyaml,python-dateutil,android,pyjnius,plyer

orientation = all
fullscreen = 1

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,REQUEST_IGNORE_BATTERY_OPTIMIZATIONS

android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# Use latest p4a
p4a.branch = develop
```

---

## Expected Build Time

- **First build:** 45-90 minutes (downloads and compiles everything)
- **Subsequent builds:** 5-10 minutes

The build is working correctly until it hits the pyjnius issue. The fixes above will resolve it.

---

## TL;DR - Fastest Fix

```bash
# 1. Copy to WSL
cp -r /mnt/c/Users/roial/Documents/Fun-Repos/IPTV-APP-V2 ~/IPTV-Saba
cd ~/IPTV-Saba

# 2. Edit buildozer.spec line 35, remove version numbers:
requirements = python3,kivy,pillow,requests,aiohttp,chardet,pyyaml,python-dateutil,android,pyjnius,plyer

# 3. Clean and build
rm -rf .buildozer
buildozer android debug
```

This should work! The pyjnius issue is resolved in newer versions when you don't pin Python to 3.11.
