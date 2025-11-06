# IPTV Saba - Android Build Guide

This guide will help you build the IPTV Saba Android app and generate an APK file.

## Overview

This branch contains a complete Android conversion of the IPTV-Saba desktop application. The app has been rebuilt using:
- **Kivy**: Cross-platform UI framework for Python
- **Python for Android (p4a)**: Toolchain for packaging Python apps for Android
- **Buildozer**: Build automation tool for creating APK files

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu/Debian recommended) or macOS
- **Python**: 3.9 or higher
- **Java JDK**: Version 11 or higher
- **Android SDK**: Will be downloaded automatically by Buildozer
- **Android NDK**: Will be downloaded automatically by Buildozer

### Required System Packages (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y \
    python3-pip \
    build-essential \
    git \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev \
    libgstreamer1.0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    openjdk-11-jdk \
    unzip \
    zip \
    autoconf \
    libtool \
    pkg-config \
    cmake \
    ninja-build \
    ccache
```

### Required System Packages (macOS)

```bash
brew install \
    python3 \
    pkg-config \
    autoconf \
    automake \
    libtool \
    ccache \
    openjdk@11
```

## Installation Steps

### 1. Install Buildozer

```bash
pip3 install --user --upgrade buildozer
pip3 install --user --upgrade cython
```

### 2. Install Kivy (for testing on desktop)

```bash
pip3 install --user kivy[base]
```

### 3. Clone and Navigate to the Project

```bash
cd /path/to/IPTV-Saba
git checkout claude/android-app-conversion-011CUsFXJuNkkTuUgr5uaMXD
```

## Building the APK

### First-Time Build

The first build will take a significant amount of time (30-60 minutes) as Buildozer downloads and compiles all necessary dependencies:

```bash
# Initialize buildozer (creates .buildozer directory)
buildozer init

# Build the debug APK
buildozer -v android debug
```

### Subsequent Builds

After the first build, subsequent builds will be much faster (5-10 minutes):

```bash
buildozer android debug
```

### Build Release APK (for distribution)

To build a release version (signed and optimized):

```bash
buildozer android release
```

**Note**: Release builds require signing. You'll need to create a keystore:

```bash
keytool -genkey -v -keystore my-release-key.keystore -alias alias_name -keyalg RSA -keysize 2048 -validity 10000
```

Then update `buildozer.spec` with keystore details:
```ini
[app]
android.release_artifact = apk
android.sign_apk = True
android.keystore = /path/to/my-release-key.keystore
android.keystore_alias = alias_name
```

## Testing the App

### On Desktop (Development)

You can test the Kivy app on your desktop before building for Android:

```bash
python3 main.py
```

### On Android Device

1. Enable **Developer Options** and **USB Debugging** on your Android device
2. Connect your device via USB
3. Deploy and run the app:

```bash
buildozer android deploy run
```

This will:
- Build the APK
- Install it on your device
- Launch the app
- Show logs in the terminal

### View Logs

To view Android logcat logs:

```bash
buildozer android logcat
```

Or filter for Python logs only:

```bash
adb logcat -s python
```

## APK Location

After a successful build, the APK will be located at:

```
bin/iptvsaba-1.0.0-debug.apk
```

Or for release builds:

```
bin/iptvsaba-1.0.0-release.apk
```

## Common Build Issues and Solutions

### Issue: "No module named 'kivy'"

**Solution**: Make sure Kivy is in the requirements in `buildozer.spec`:
```ini
requirements = python3==3.9.0,kivy==2.2.1,...
```

### Issue: "SDK/NDK not found"

**Solution**: Let Buildozer download them automatically. If you have existing SDK/NDK, specify paths in `buildozer.spec`:
```ini
android.sdk_path = /path/to/android-sdk
android.ndk_path = /path/to/android-ndk
```

### Issue: Build fails with Java version error

**Solution**: Ensure Java 11 is installed and set as default:
```bash
sudo update-alternatives --config java
```

### Issue: "Permission denied" errors

**Solution**: Don't run buildozer as root. If directories were created as root, fix permissions:
```bash
sudo chown -R $USER:$USER .buildozer
```

### Issue: Video playback not working

**Solution**: The Kivy Video widget uses GStreamer on Android. Ensure your stream URLs are compatible. Some formats may not work on all devices.

## Customization

### App Icon

Replace the placeholder icon at:
```
android/icon.png  (512x512 PNG recommended)
```

Then update `buildozer.spec`:
```ini
icon.filename = %(source.dir)s/android/icon.png
```

### Presplash Screen

Replace the placeholder presplash at:
```
android/presplash.png  (800x1280 PNG recommended)
```

Then update `buildozer.spec`:
```ini
presplash.filename = %(source.dir)s/android/presplash.png
```

### App Name and Version

Edit in `buildozer.spec`:
```ini
title = IPTV Saba
package.name = iptvsaba
package.domain = com.iptvsaba
version = 1.0.0
```

### Permissions

Permissions are configured in `buildozer.spec`:
```ini
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK,ACCESS_NETWORK_STATE
```

## Architecture Overview

### File Structure

```
IPTV-Saba/
├── main.py                          # Android app entry point
├── buildozer.spec                   # Build configuration
├── android/
│   ├── icon.svg                     # App icon (placeholder)
│   └── presplash.svg                # Splash screen (placeholder)
├── src/
│   ├── android/
│   │   └── screens/
│   │       ├── login_screen.py      # Login/profile selection
│   │       ├── channel_screen.py    # Channel browsing
│   │       ├── easy_mode_screen.py  # Simplified UI for elderly
│   │       └── fullscreen_screen.py # Fullscreen video player
│   ├── controller/
│   │   └── controller.py            # App logic controller
│   ├── data/
│   │   ├── config_manager.py        # Configuration management
│   │   ├── profile_manager.py       # Profile management
│   │   └── data_loader.py           # M3U playlist parser
│   └── model/
│       ├── channel_model.py         # Channel data model
│       ├── group_model.py           # Group data model
│       └── profile.py               # Profile data model
└── .buildozer/                      # Build cache (created on first build)
```

### Key Differences from Desktop Version

1. **UI Framework**: PyQt5 → Kivy
2. **Video Player**: VLC → Kivy Video (GStreamer backend)
3. **Storage**: Uses Android external storage (`/sdcard/IPTV-Saba/`)
4. **Permissions**: Requires explicit Android permissions
5. **Lifecycle**: Implements Android app lifecycle (pause/resume)

## Performance Optimization

### Reduce APK Size

1. **Remove unused dependencies** from `buildozer.spec` requirements
2. **Optimize images**: Compress icon and presplash images
3. **Use ProGuard**: Enable in `buildozer.spec` (for release builds)

### Improve Build Speed

1. **Enable ccache**:
   ```bash
   export USE_CCACHE=1
   export CCACHE_DIR=~/.ccache
   ```

2. **Increase build resources**: If using VM, allocate more RAM/CPU

3. **Clean build cache** if experiencing issues:
   ```bash
   buildozer android clean
   ```

## Distribution

### Google Play Store

1. Build a **release APK** (see above)
2. Sign the APK with your keystore
3. Create a Google Play Developer account ($25 one-time fee)
4. Upload APK through Google Play Console
5. Fill in app details, screenshots, description
6. Submit for review

### Direct Distribution

1. Build a **release APK**
2. Host the APK on your website or file sharing service
3. Users must enable "Install from Unknown Sources" on their devices
4. Provide installation instructions

## Troubleshooting

### Enable Verbose Logging

```bash
buildozer -v android debug
```

### Clean Build

If experiencing persistent issues:

```bash
buildozer android clean
rm -rf .buildozer
buildozer -v android debug
```

### Check Device Connection

```bash
adb devices
```

Should show your device. If not:
```bash
adb kill-server
adb start-server
adb devices
```

## Support and Resources

- **Buildozer Documentation**: https://buildozer.readthedocs.io/
- **Kivy Documentation**: https://kivy.org/doc/stable/
- **Python for Android**: https://python-for-android.readthedocs.io/
- **Android Developer Guide**: https://developer.android.com/

## Known Limitations

1. **Video Codec Support**: Limited to formats supported by Android GStreamer
2. **Background Playback**: Not implemented (app stops when backgrounded)
3. **Picture-in-Picture**: Not currently supported
4. **Chromecast**: Not implemented
5. **External Subtitle Support**: Limited

## Future Enhancements

- [ ] Background audio playback
- [ ] Picture-in-Picture mode
- [ ] Download channels for offline viewing
- [ ] Better video codec support (ExoPlayer integration)
- [ ] Chromecast support
- [ ] Android TV support
- [ ] Notification controls

## License

This Android version maintains the same license as the original IPTV-Saba project.

---

**Happy Building! 🚀**

For questions or issues, please open an issue on the GitHub repository.
