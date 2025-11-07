# Testing Guide - Netflix-Style UI

## What's Been Completed

### ✅ Netflix-Style UI/UX Redesign
- **Horizontal group selector**: Easy browsing between many channel groups
- **Card-based layout**: 2-column grid with Netflix-style channel cards
- **Dark theme**: Netflix-inspired color scheme (#141414 background, #E50914 accent)
- **Auto-play**: Tap channel card to play immediately
- **Modern top bar**: Logo, profile, logout, and quick play button
- **Integrated search**: Clean search with favorites button
- **Player controls**: Comprehensive overlay with play/pause, volume, back button

### ✅ Build Fixes
- **Removed pyjnius/plyer**: Fixed Android build errors
- **python-vlc embedded player**: Desktop video playback integrated within app
- **External VLC fallback**: Automatic fallback if embedding fails
- **Optional download/record**: Made features optional when pyjnius unavailable

### ✅ Documentation
- `NETFLIX_UI.md` - Complete UI/UX design guide
- `PLAYER_CONTROLS.md` - Video player overlay controls
- `BUILD_APK.md` - APK build guide with troubleshooting
- `DESKTOP_SETUP.md` - Desktop video setup guide

---

## Testing on Desktop (Windows)

### 1. Prerequisites
```bash
# Open PowerShell or Command Prompt
cd C:\Users\roial\Documents\Fun-Repos\IPTV-APP-V2

# Activate virtual environment
venv\Scripts\activate

# Install/update requirements
pip install -r requirements-desktop.txt
```

**Important**: Make sure VLC media player is installed from https://www.videolan.org/vlc/

### 2. Run the App
```bash
python main.py
```

### 3. What to Test

#### Netflix UI Features
- [ ] **Top bar displays**: Logo (red), profile name, logout, and play buttons
- [ ] **Horizontal group scroll**: Browse by Category section with scrollable buttons
- [ ] **Group buttons work**: Click different category buttons to filter channels
- [ ] **Active group highlighted**: Selected category shows in Netflix red
- [ ] **Channel cards display**: 2-column grid with rounded corners
- [ ] **Channel thumbnails**: Initial letter shown in each card
- [ ] **Favorites indicator**: ♥ symbol on favorited channels
- [ ] **Search works**: Type in search box to filter channels
- [ ] **Favorites button**: Shows only favorited channels

#### Video Playback
- [ ] **Auto-play on card tap**: Click channel card → video plays immediately
- [ ] **Embedded video**: Video plays within the app window (not external VLC)
- [ ] **Player controls visible**: Control overlay displays with channel name
- [ ] **[X] button works**: Closes player and returns to channel list
- [ ] **[< Channels] works**: Returns to channel selection
- [ ] **[Play/Pause] works**: Toggles playback state
- [ ] **[Stop] works**: Stops video completely
- [ ] **Volume slider works**: Drag to adjust volume 0-100%
- [ ] **Volume percentage updates**: Shows current volume level

#### Profile Management
- [ ] **Create profile**: Add new profile with M3U URL
- [ ] **Load channels**: Channels load successfully from M3U
- [ ] **Add to favorites**: Click channel, add to favorites
- [ ] **View favorites**: Favorites button shows correct channels
- [ ] **Channel history**: Recently played channels tracked

---

## Building Android APK

### 1. Switch to WSL
```bash
# Open WSL terminal
cd ~/IPTV-Saba
```

### 2. Clean Previous Build
```bash
# Remove old build files to ensure clean build
rm -rf .buildozer/ ~/.buildozer/
```

### 3. Build APK
```bash
# Build debug APK (verbose output)
buildozer -v android debug
```

**Build time**: ~15-30 minutes first time, ~5-10 minutes after that

### 4. Expected Output
```
# BUILD SUCCESSFUL
BUILD SUCCESSFUL in 3m 45s
# APK created at:
bin/iptvapp-0.1-arm64-v8a-debug.apk
```

### 5. Install on Android Device
```bash
# Connect device via USB with Developer Mode enabled
adb install bin/iptvapp-0.1-arm64-v8a-debug.apk
```

Or copy `bin/iptvapp-0.1-arm64-v8a-debug.apk` to your device and install manually.

---

## Testing on Android

### What to Test

#### Netflix UI on Mobile
- [ ] **Top bar responsive**: All buttons visible and tappable
- [ ] **Horizontal group scroll**: Swipe left/right through categories
- [ ] **Group buttons touch-friendly**: Easy to tap, proper spacing
- [ ] **Card grid**: 2 columns display correctly
- [ ] **Cards touch-friendly**: 140dp height, easy to tap
- [ ] **Search keyboard**: Keyboard opens for search input
- [ ] **Smooth scrolling**: Channel list scrolls smoothly

#### Video Playback on Android
- [ ] **Video plays**: Native Android video widget works
- [ ] **Controls appear**: Overlay displays on video start
- [ ] **Controls auto-hide**: After 3 seconds of inactivity
- [ ] **Tap to show/hide**: Touch screen toggles controls
- [ ] **All buttons work**: Close, back, play/pause, stop
- [ ] **Volume control**: Slider adjusts Android system volume
- [ ] **Fullscreen works**: Video fills screen

#### Android-Specific Features
- [ ] **Orientation changes**: App handles rotation properly
- [ ] **Back button**: Android back button works correctly
- [ ] **App resume**: Resumes correctly after switching apps
- [ ] **Network handling**: Handles network changes gracefully

---

## Common Issues & Solutions

### Desktop Issues

#### "VLC library not found"
**Solution**:
```bash
pip install python-vlc
```
Also ensure VLC media player is installed system-wide.

#### "Window handle error"
**Solution**:
- App automatically falls back to external VLC
- Try restarting the app
- Check if VLC works standalone

#### Black screen on video
**Solutions**:
- Test stream URL in VLC standalone first
- Check internet connection
- Verify M3U URL is correct and accessible

#### Cards not displaying
**Solution**:
- Check if channels loaded successfully
- Look for error popups
- Verify M3U format is correct

### Android Build Issues

#### Build fails immediately
**Solution**:
```bash
# Check buildozer version
buildozer --version

# Update buildozer
pip install --upgrade buildozer

# Clean and retry
rm -rf .buildozer/
buildozer -v android debug
```

#### "NDK not found"
**Solution**: Buildozer will auto-download NDK 25b on first build. Be patient.

#### "SDK not found"
**Solution**: Buildozer auto-downloads SDK. Ensure ~5GB free disk space.

#### Build times out
**Solution**:
```bash
# Increase timeout in buildozer.spec
# android.gradle_build_timeout = 600
```

### Android App Issues

#### App crashes on startup
**Solution**:
- Check logcat: `adb logcat | grep python`
- Verify M3U URL is accessible from mobile network
- Check Android version (minimum API 21 / Android 5.0)

#### Video won't play
**Solutions**:
- Check stream URL works in browser
- Try different channel
- Verify internet connection
- Some streams may not be mobile-compatible

#### UI elements too small
**Solution**: Kivy uses `dp()` for proper scaling, but may need adjustment for tablets

---

## Performance Testing

### Desktop Performance
- [ ] **App startup**: < 3 seconds
- [ ] **Channel load**: < 5 seconds for typical M3U
- [ ] **Search responsiveness**: Instant filtering
- [ ] **Group switching**: Instant filter update
- [ ] **Video start time**: < 3 seconds for good streams
- [ ] **UI smoothness**: No lag when scrolling

### Android Performance
- [ ] **App startup**: < 5 seconds
- [ ] **Channel load**: < 10 seconds on mobile network
- [ ] **Scroll performance**: Smooth scrolling without lag
- [ ] **Memory usage**: Check if app is killed in background
- [ ] **Battery usage**: Reasonable power consumption

---

## Next Steps After Testing

### If Everything Works
1. ✅ Commit any final tweaks
2. ✅ Push to branch: `claude/android-app-conversion-011CUsFXJuNkkTuUgr5uaMXD`
3. ✅ Create PR when ready (DO NOT merge to main without approval)

### If Issues Found
1. 📝 Note specific issues with steps to reproduce
2. 📝 Check error logs (desktop: terminal, Android: adb logcat)
3. 📝 Report issues with screenshots if possible

### Future Enhancements
Consider adding:
- [ ] Actual channel logos/thumbnails
- [ ] Channel preview on long-press
- [ ] "Continue Watching" row
- [ ] Recently added channels
- [ ] Smooth transitions/animations
- [ ] Keyboard shortcuts (desktop)
- [ ] Night/day mode toggle
- [ ] Picture-in-picture mode
- [ ] Chromecast support

---

## Summary

The Netflix-style UI provides a modern, user-friendly interface for browsing many channel groups:

**Key Improvements**:
- ✅ Horizontal group browsing (vs dropdown)
- ✅ Visual card layout (vs text list)
- ✅ Auto-play on tap (vs separate button)
- ✅ Clean, dark theme (vs cluttered UI)
- ✅ Easy navigation (vs multiple action rows)

**Technical Stack**:
- Desktop: python-vlc for embedded video
- Android: Native Kivy Video widget
- UI: Kivy 2.3.0 with custom Netflix-style components
- Build: Buildozer with NDK 25b, API 33

**Branch**: `claude/android-app-conversion-011CUsFXJuNkkTuUgr5uaMXD`

Ready to test! 🚀
