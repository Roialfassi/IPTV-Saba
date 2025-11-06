# Testing IPTV Saba Android App

This guide shows how to test the Android app on your desktop before building the APK.

## Desktop Testing (Windows/Linux/macOS)

### 1. Install Python Requirements

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Kivy and dependencies
pip install kivy[base] pillow requests aiohttp chardet pyyaml python-dateutil
```

### 2. Run the App

```bash
# From the project root directory
python main.py
```

The app will run in a desktop window and store data in:
- **Windows**: `C:\Users\<username>\.IPTV-Saba\`
- **Linux/macOS**: `~/.IPTV-Saba/`

### 3. Test Features

**Login Screen:**
- ✅ Create profile
- ✅ Delete profile
- ✅ Select profile
- ✅ Auto-login checkbox

**Channel Screen:**
- ✅ Search channels
- ✅ Filter by group
- ✅ Add to favorites
- ✅ View history
- ✅ Play channel (opens fullscreen)
- ✅ Download media files
- ✅ Record livestreams
- ✅ View downloads

**Fullscreen Player:**
- ✅ Video playback
- ✅ Volume control
- ✅ Play/pause
- ✅ Back button
- ✅ Auto-hiding controls

**Easy Mode:**
- ✅ Previous/Next buttons
- ✅ Shows only favorites
- ✅ Large buttons

### 4. Known Desktop vs Android Differences

| Feature | Desktop | Android |
|---------|---------|---------|
| **Storage** | `~/.IPTV-Saba/` | `/sdcard/IPTV-Saba/` |
| **Downloads** | Uses requests library | Uses Android DownloadManager |
| **Notifications** | None | Android notifications for downloads |
| **Permissions** | Auto-granted | Requested on startup |
| **Video Player** | Kivy Video (limited codecs) | Same (GStreamer) |

### 5. Common Desktop Testing Issues

#### Issue: "No module named 'android'"
**Solution**: This is normal on desktop. The app detects the platform and only imports Android modules when running on Android.

#### Issue: Video not playing
**Solution**:
- Install ffmpeg and make sure it's in PATH
- Install GStreamer (recommended for better codec support)
- Or install ffpyplayer: `pip install ffpyplayer`

#### Issue: "Permission denied" on downloads
**Solution**: Check that the download directory is writable.

#### Issue: Window is too small/large
**Solution**: Edit main.py and add after `Window.clearcolor`:
```python
Window.size = (400, 700)  # Phone-like dimensions
```

### 6. Debug Mode

To see detailed logs:

```bash
# Set environment variable before running
# Windows:
set KIVY_LOG_LEVEL=debug
python main.py

# Linux/macOS:
KIVY_LOG_LEVEL=debug python main.py
```

Logs are saved to:
- **Windows**: `C:\Users\<username>\.kivy\logs\`
- **Linux/macOS**: `~/.kivy/logs/`

### 7. Testing Download/Record Features

**To test downloads:**
1. Create a profile with an M3U URL that has media files
2. Select a channel that points to a .mp4, .mkv, etc.
3. Click "⬇ Download"
4. Check `~/.IPTV-Saba/Downloads/` for the file

**To test recording:**
1. Select a livestream channel
2. Click "⏺ Record"
3. Wait a few seconds
4. Click "⏹ Stop"
5. Check `~/.IPTV-Saba/Downloads/` for the recording

### 8. Performance Testing

The app should:
- ✅ Start in < 2 seconds
- ✅ Load M3U playlists in < 5 seconds (for ~1000 channels)
- ✅ Search should be instant
- ✅ Switching screens should be smooth
- ✅ Video playback should start in < 3 seconds

If performance is slow:
- Check your M3U playlist size
- Make sure caching is working (check for `*data.json` files)
- Run with `--profile` to find bottlenecks

### 9. Preparing for Android Build

Once desktop testing is successful:

1. **Fix any issues** found during desktop testing
2. **Commit changes**: `git add . && git commit -m "Fixes from desktop testing"`
3. **Build APK**: See [ANDROID_BUILD.md](ANDROID_BUILD.md) for instructions

### 10. Testing Checklist

Before building for Android, verify:

- [ ] App starts without errors
- [ ] Can create and delete profiles
- [ ] Can load M3U playlists
- [ ] Channels display correctly
- [ ] Search works
- [ ] Favorites work
- [ ] Video plays in fullscreen
- [ ] Download button works for media files
- [ ] Record button works for livestreams
- [ ] Downloads list shows files
- [ ] Auto-login works
- [ ] Easy mode displays correctly
- [ ] No Python errors in console

---

## Android Testing (After APK Build)

### 1. Install APK on Device

```bash
# Connect Android device via USB
# Enable Developer Options and USB Debugging on device

# Install APK
adb install bin/iptvsaba-1.0.0-debug.apk

# Or use buildozer
buildozer android deploy run
```

### 2. View Logs

```bash
# View all logs
adb logcat

# View only Python logs
adb logcat -s python

# Save logs to file
adb logcat > android_logs.txt
```

### 3. Check File Storage

```bash
# List app files
adb shell ls -la /sdcard/IPTV-Saba/

# View config
adb shell cat /sdcard/IPTV-Saba/config.json

# View profiles
adb shell cat /sdcard/IPTV-Saba/profiles.json

# Check downloads
adb shell ls -la /sdcard/IPTV-Saba/Downloads/
```

### 4. Debugging on Android

```bash
# Clear app data
adb shell pm clear com.iptvsaba

# Uninstall app
adb uninstall com.iptvsaba

# Reinstall
adb install -r bin/iptvsaba-1.0.0-debug.apk
```

### 5. Performance Monitoring

```bash
# Monitor CPU/Memory
adb shell top | grep iptvsaba

# Check battery usage
adb shell dumpsys batterystats | grep iptvsaba
```

---

## Troubleshooting

### Desktop Issues

**Problem**: Black screen / No UI
**Solution**: Update graphics drivers, or set:
```bash
export KIVY_GL_BACKEND=angle_sdl2  # Windows
export KIVY_GL_BACKEND=sdl2        # Linux/macOS
```

**Problem**: Slow performance
**Solution**:
- Check M3U playlist size (> 5000 channels may be slow)
- Enable caching (automatic after first load)
- Use SSD for better file I/O

**Problem**: Video codec not supported
**Solution**: Install ffmpeg or GStreamer with full codec packs

### Android Issues

**Problem**: App crashes on startup
**Solution**: Check logcat for Python errors, ensure all permissions granted

**Problem**: Downloads not working
**Solution**: Check storage permissions, verify external storage is available

**Problem**: Video not playing
**Solution**: Check stream URL works in browser, some codecs may not be supported

---

## Need Help?

1. Check logs (desktop: `~/.kivy/logs/`, Android: `adb logcat`)
2. Review error messages
3. Open an issue on GitHub with:
   - Full error log
   - Steps to reproduce
   - Platform (desktop OS or Android version)
   - M3U URL format (if applicable)

---

**Happy Testing! 🧪**
