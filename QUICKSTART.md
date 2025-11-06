# IPTV Saba Android - Quick Start Guide

Get the app running in 5 minutes!

## 🚀 Test on Desktop First (Recommended)

Before building for Android, test on your computer:

### Windows:

```bash
# 1. Install dependencies
pip install kivy[base] pillow requests aiohttp chardet pyyaml python-dateutil

# 2. Run the app
python main.py
```

### Linux/macOS:

```bash
# 1. Install dependencies
pip3 install kivy[base] pillow requests aiohttp chardet pyyaml python-dateutil

# 2. Run the app
python3 main.py
```

**That's it!** The app opens in a window. Test all features before building APK.

---

## 📱 Build Android APK

Once desktop testing works:

### Prerequisites (One-Time Setup):

**Ubuntu/Debian:**
```bash
sudo apt install -y python3-pip build-essential git ffmpeg \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev \
    zlib1g-dev openjdk-11-jdk unzip autoconf libtool pkg-config
```

**Install Buildozer:**
```bash
pip3 install --user --upgrade buildozer cython
```

### Build APK:

```bash
# Navigate to project
cd IPTV-Saba

# Build (first time: 30-60 min, downloads SDK/NDK)
buildozer android debug

# APK created at:
# bin/iptvsaba-1.0.0-debug.apk
```

### Install on Device:

```bash
# Connect Android device via USB (enable USB debugging)
adb install bin/iptvsaba-1.0.0-debug.apk

# Or use buildozer
buildozer android deploy run
```

---

## ✅ Feature Checklist

Before building APK, verify on desktop:

- [ ] App starts without errors
- [ ] Can create/delete profiles
- [ ] Can load M3U playlists
- [ ] Channels display correctly
- [ ] Search works
- [ ] Favorites toggle works
- [ ] Video plays in fullscreen
- [ ] Download button works
- [ ] Record button works
- [ ] Downloads list shows files

---

## 🐛 Troubleshooting

### Desktop Issues:

**Black screen / No UI:**
```bash
# Windows
set KIVY_GL_BACKEND=angle_sdl2
python main.py

# Linux/macOS
KIVY_GL_BACKEND=sdl2 python3 main.py
```

**Video won't play:**
- Install ffmpeg: `sudo apt install ffmpeg` (Linux) or download from ffmpeg.org (Windows)
- Or install: `pip install ffpyplayer`

**Module not found:**
```bash
# Make sure you're in the right directory
cd IPTV-Saba

# Install missing dependency
pip install <module-name>
```

### Build Issues:

**Java version error:**
```bash
# Ubuntu: Install Java 11
sudo apt install openjdk-11-jdk

# Set as default
sudo update-alternatives --config java
```

**Permission denied:**
```bash
# Fix ownership
sudo chown -R $USER:$USER .buildozer

# Never run buildozer as root!
```

**Build fails:**
```bash
# Clean and retry
buildozer android clean
buildozer -v android debug  # -v for verbose output
```

---

## 📊 Build Configuration

The app is configured with:

- **NDK**: 25b (latest)
- **SDK API**: 33 (Android 13)
- **Python**: 3.11.6
- **Kivy**: 2.3.0
- **Min Android**: API 21 (Android 5.0+)
- **Architectures**: arm64-v8a, armeabi-v7a

All settings in `buildozer.spec` are production-ready!

---

## 📖 More Documentation

- **TESTING.md** - Comprehensive testing guide
- **ANDROID_BUILD.md** - Detailed build instructions
- **README_ANDROID.md** - Full user documentation

---

## 🎯 Common Commands

```bash
# Desktop testing
python main.py

# Build APK
buildozer android debug

# Install on device
adb install bin/iptvsaba-1.0.0-debug.apk

# View Android logs
adb logcat -s python

# Clean build
buildozer android clean
```

---

## 💡 Tips

1. **Always test on desktop first** - much faster than building APK
2. **First build takes 30-60 minutes** - be patient, downloads SDK/NDK/dependencies
3. **Subsequent builds take 5-10 minutes** - much faster after first time
4. **Use `-v` flag** for verbose output if build fails: `buildozer -v android debug`
5. **Check logs** in `~/.kivy/logs/` if app crashes

---

## 🆘 Need Help?

1. Check error message in console
2. Look in `~/.kivy/logs/` for detailed logs
3. Try `buildozer android clean` and rebuild
4. Check TESTING.md for more troubleshooting
5. Open issue on GitHub with full error log

---

**Ready to build? Run:** `python main.py` to test, then `buildozer android debug` to build APK! 🚀
