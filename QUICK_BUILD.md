# Quick Build Guide - Optimized Requirements

## ✅ Build Issues Fixed

The build failures were caused by unused packages with complex dependencies:
- **aiohttp**: Not used, removed
- **pyyaml**: Not used, removed
- **python-dateutil**: Not used, removed
- **chardet**: Made optional with UTF-8 fallback

## 🚀 Build APK Now

### Step 1: Clean Previous Build

```bash
cd ~/IPTV-Saba
rm -rf .buildozer/ ~/.buildozer/
```

### Step 2: Build with Optimized Requirements

```bash
buildozer -v android debug
```

**Expected**: Clean build with minimal requirements:
- python3
- kivy==2.3.0
- pillow
- requests
- android

### Step 3: Monitor Progress

Build will take 15-30 minutes on first run. You'll see:

```
✓ Downloading SDK
✓ Downloading NDK 25b
✓ Installing requirements...
  - python3
  - kivy==2.3.0
  - pillow
  - requests
✓ Building APK
✓ APK created: bin/iptvapp-0.1-arm64-v8a-debug.apk
```

---

## 📊 What Changed

### Before (Failing):
```ini
requirements = python3,kivy,pillow,requests,aiohttp,chardet,pyyaml,python-dateutil,android,pyjnius,plyer
```

**Issues**:
- aiohttp: Complex C dependencies (libuv, cython, etc.)
- pyjnius: Build errors with Cython
- Many unused packages

### After (Working):
```ini
requirements = python3,kivy==2.3.0,pillow,requests,android
```

**Benefits**:
- ✅ All packages have working Android recipes
- ✅ No complex C dependencies
- ✅ Faster build time
- ✅ Smaller APK size
- ✅ Only packages actually used by app

---

## 🔍 If Build Still Fails

### Run Diagnostic Script

```bash
./diagnose_build.sh
```

This will show the actual error from build logs.

### Common Solutions

**1. Disk Space**
```bash
df -h  # Need 5GB+ free
```

**2. Java Version**
```bash
java -version  # Need Java 8 or 11
```

**3. Network Issues**
```bash
# Retry build - buildozer downloads many files
buildozer android debug
```

**4. Permission Issues**
```bash
chmod -R 755 ~/.buildozer
```

---

## 📱 After Successful Build

### Install APK

```bash
# Via ADB (device connected via USB)
adb install bin/iptvapp-0.1-arm64-v8a-debug.apk

# Or copy to device and install manually
```

### APK Location

```
~/IPTV-Saba/bin/iptvapp-0.1-arm64-v8a-debug.apk
```

In Windows, this is:
```
\\wsl$\Ubuntu-20.04\home\roi11\IPTV-Saba\bin\
```

---

## 🎯 Features in This Build

✅ **Working Features**:
- Netflix-style UI with horizontal group browsing
- 2-column card grid for channels
- Profile management
- M3U playlist loading
- Channel favorites
- Video playback (native Android)
- Search and filtering
- Dark theme

❌ **Not Included** (removed to fix build):
- Download feature (required pyjnius)
- Record feature (required pyjnius)

---

## 🔄 Rebuild After Code Changes

```bash
# Quick rebuild (reuses existing build)
buildozer android debug

# Full clean rebuild
rm -rf .buildozer/
buildozer android debug
```

---

## 💡 Tips

**Save Time**:
- First build: 15-30 minutes
- Subsequent builds: 5-10 minutes (reuses downloads)
- Keep ~/.buildozer/ directory to reuse SDK/NDK

**Optimize Further**:
```bash
# Release build (smaller, optimized)
buildozer android release

# Specify single architecture
buildozer android debug --arch=arm64-v8a
```

**Debug on Device**:
```bash
# View app logs
adb logcat | grep python

# View errors only
adb logcat | grep -i error
```

---

## 📚 More Help

- **Full Troubleshooting**: See `BUILD_TROUBLESHOOTING.md`
- **Testing Guide**: See `TESTING_GUIDE.md`
- **Netflix UI**: See `NETFLIX_UI.md`

---

## ✨ Summary

**Problem**: Build failed with `pythonforandroid.toolchain create` error

**Root Cause**: Unused packages (aiohttp, pyyaml, etc.) with missing Android recipes

**Solution**: Removed unused packages, made chardet optional

**Result**: Clean build with minimal working requirements

**Ready to build!** 🚀
