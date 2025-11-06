# IPTV Saba - Android Edition

<div align="center">

**A Full-Featured IPTV Streaming App for Android**

[![Platform](https://img.shields.io/badge/Platform-Android-green.svg)](https://www.android.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Kivy](https://img.shields.io/badge/Kivy-2.2.1-orange.svg)](https://kivy.org/)
[![License](https://img.shields.io/badge/License-See%20Original-lightgrey.svg)](LICENSE)

</div>

---

## 📱 About This Version

This is a **complete Android conversion** of the IPTV-Saba desktop application. The entire UI has been rebuilt using Kivy framework to provide a native Android experience while maintaining all core functionality from the desktop version.

### ✨ Key Features

- 📺 **Stream IPTV Channels** - Watch live TV from M3U playlists
- 👤 **Multi-Profile Support** - Create and manage multiple user profiles
- ⭐ **Favorites & History** - Save your favorite channels and track viewing history
- 🎯 **Easy Mode** - Simplified interface for elderly users with large buttons
- 🔍 **Smart Search** - Quickly find channels by name
- 📁 **Group Organization** - Channels organized by categories
- 🎬 **Fullscreen Playback** - Immersive fullscreen video player with touch controls
- 🌐 **Auto-Login** - Remember your profile and login automatically
- 💾 **Offline Caching** - 24-hour cache for faster loading

---

## 🏗️ Architecture

This Android app is built using:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **UI Framework** | Kivy 2.2.1 | Cross-platform Python UI toolkit |
| **Video Player** | Kivy Video (GStreamer) | Hardware-accelerated video playback |
| **Build Tool** | Buildozer | Python to APK packaging |
| **Backend** | Python 3.9 | Core business logic |
| **Data Storage** | JSON | Profile and channel data |
| **Network** | aiohttp/requests | Async HTTP for M3U downloads |

---

## 📸 Screenshots

### Login Screen
- Select or create profiles
- Auto-login option
- Modern dark theme

### Channel Browser
- Browse channels by group
- Search functionality
- Add to favorites with one tap
- View history

### Easy Mode
- Large, simple controls
- Perfect for elderly users
- Auto-hiding interface
- Quick channel switching

### Fullscreen Player
- Full-screen video playback
- Touch controls
- Volume control
- Auto-hiding controls overlay

---

## 🚀 Quick Start

### For Users (Installing APK)

1. **Download** the APK file from releases
2. **Enable** "Install from Unknown Sources" in Android settings
3. **Install** the APK
4. **Launch** IPTV Saba
5. **Create** a profile with your M3U playlist URL
6. **Enjoy** streaming!

### For Developers (Building from Source)

See [**ANDROID_BUILD.md**](ANDROID_BUILD.md) for comprehensive build instructions.

**TL;DR:**

```bash
# Install buildozer
pip3 install --user buildozer

# Build APK
buildozer android debug

# Find APK at: bin/iptvsaba-1.0.0-debug.apk
```

---

## 📋 Requirements

### Runtime Requirements
- **Android Version**: 5.0 (Lollipop) or higher (API 21+)
- **Storage**: ~50MB for app + data storage
- **Internet**: Required for streaming
- **Permissions**:
  - Internet access
  - Storage (read/write)
  - Wake lock (prevent sleep during playback)

### Build Requirements
- Linux or macOS
- Python 3.9+
- Java JDK 11+
- Build tools (see ANDROID_BUILD.md)

---

## 🎯 Usage Guide

### 1. Creating a Profile

On first launch:
1. Tap **"Create Profile"**
2. Enter a **profile name** (e.g., "John's Profile")
3. Enter your **M3U playlist URL**
4. Tap **"Create"**

### 2. Selecting Channels

After profile creation:
1. Browse channels by scrolling
2. Use the **group filter** dropdown to filter by category
3. Use the **search bar** to find channels by name
4. Tap the **star icon** to add/remove from favorites

### 3. Playing Channels

- **Tap a channel** to select it (highlighted in red)
- Tap **"Play"** for embedded playback
- Tap **"Fullscreen"** for fullscreen mode

### 4. Fullscreen Controls

- **Tap screen** to show/hide controls
- **Back button** returns to channel list
- **Volume slider** adjusts volume
- **Play/Pause** button controls playback
- Controls **auto-hide** after 3 seconds

### 5. Easy Mode (For Elderly Users)

1. From channel screen, tap **"Easy Mode"**
2. Use **large "Previous"/"Next" buttons** to change channels
3. **Tap screen** to show/hide controls
4. Only shows **favorite channels** for simplicity

---

## 🔧 Configuration

### App Settings

Settings are stored in:
```
/sdcard/IPTV-Saba/config.json
```

Available settings:
- `auto_login_enabled`: Auto-login on app start
- `last_active_profile_id`: Last used profile
- `theme`: App theme (currently "default")

### Profile Data

Profiles are stored in:
```
/sdcard/IPTV-Saba/profiles.json
```

Each profile contains:
- `name`: Profile name
- `url`: M3U playlist URL
- `favorites[]`: List of favorite channels
- `history[]`: Recent viewing history (max 50)

### Channel Cache

Channel data is cached per profile:
```
/sdcard/IPTV-Saba/{ProfileName}data.json
```

Cache is refreshed:
- Every 24 hours
- When playlist fails to load (uses cached version)
- Manually by deleting cache file

---

## 🎨 Customization

### App Icon

Replace:
```
android/icon.png
```

Then rebuild. Icon should be 512x512 PNG.

### Splash Screen

Replace:
```
android/presplash.png
```

Then rebuild. Recommended size: 800x1280 PNG.

### Theme Colors

Edit color values in screen files:
- Netflix Red: `(0.898, 0.035, 0.078, 1)`
- Facebook Blue: `(0.098, 0.467, 0.949, 1)`
- Dark Background: `(0.1, 0.1, 0.1, 1)`

---

## ⚠️ Known Limitations

1. **Video Codec Support**: Limited to Android GStreamer codecs
   - Most HLS and RTSP streams work
   - Some exotic formats may not play

2. **Background Playback**: Not implemented
   - Playback stops when app is minimized
   - Future enhancement planned

3. **Offline Viewing**: Not available
   - Requires internet connection
   - Download feature planned for future

4. **Chromecast**: Not supported
   - Future enhancement

---

## 🐛 Troubleshooting

### App Won't Install
- Enable "Unknown Sources" in Settings → Security
- Ensure you have enough storage space

### Video Won't Play
- Check internet connection
- Verify M3U playlist URL is valid
- Try a different channel (codec may not be supported)
- Clear app data and reload playlist

### App Crashes on Startup
- Check Android version (5.0+ required)
- Clear app data
- Reinstall the app

### Channels Not Loading
- Verify internet connection
- Check M3U URL is accessible
- Try deleting cache: `/sdcard/IPTV-Saba/{ProfileName}data.json`

### Blank Screen in Fullscreen
- Some streams take time to buffer
- Try changing orientation
- Check if stream works in browser first

---

## 🔒 Privacy & Security

- **No Analytics**: This app does NOT collect any user data
- **No Ads**: Completely ad-free
- **Local Storage**: All data stored locally on your device
- **No Account Required**: No registration or account needed
- **Open Source**: Full source code available for audit

### Permissions Explained

| Permission | Why Needed |
|-----------|------------|
| `INTERNET` | Stream channels from M3U URLs |
| `READ_EXTERNAL_STORAGE` | Read configuration files |
| `WRITE_EXTERNAL_STORAGE` | Save profiles and channel cache |
| `WAKE_LOCK` | Prevent screen sleep during playback |
| `ACCESS_NETWORK_STATE` | Check internet connectivity |

---

## 🆚 Differences from Desktop Version

| Feature | Desktop (PyQt5) | Android (Kivy) |
|---------|----------------|----------------|
| **UI Framework** | PyQt5 | Kivy |
| **Video Player** | VLC | GStreamer |
| **Platform** | Windows/Linux/macOS | Android only |
| **Storage** | `~/.IPTV-Saba/` | `/sdcard/IPTV-Saba/` |
| **Controls** | Mouse/Keyboard | Touch |
| **Download/Record** | ✅ Available | ❌ Not implemented |

---

## 🛣️ Roadmap

### Version 1.1 (Planned)
- [ ] Background audio playback
- [ ] Picture-in-Picture mode
- [ ] Better video buffering
- [ ] Chromecast support

### Version 1.2 (Future)
- [ ] Download channels for offline viewing
- [ ] Android TV support
- [ ] Multiple subtitle tracks
- [ ] EPG (Electronic Program Guide) integration

### Version 2.0 (Vision)
- [ ] Native Android (Kotlin) rewrite
- [ ] ExoPlayer integration
- [ ] Material Design 3
- [ ] Cloud sync for profiles

---

## 🤝 Contributing

This is an experimental branch. Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on multiple Android devices
5. Submit a pull request

---

## 📜 License

This Android version maintains the same license as the original IPTV-Saba project.

---

## 🙏 Acknowledgments

- **Original Desktop App**: IPTV-Saba by [original author]
- **Kivy Team**: For the amazing cross-platform framework
- **Python for Android**: For making Python on Android possible
- **GStreamer**: For video playback capabilities

---

## 📞 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check the build documentation: [ANDROID_BUILD.md](ANDROID_BUILD.md)

---

<div align="center">

**Made with ❤️ using Python and Kivy**

[⬆ Back to Top](#iptv-saba---android-edition)

</div>
