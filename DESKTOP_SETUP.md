# Desktop Setup Guide

## Quick Start (Windows)

### 1. Install Python Dependencies

```bash
cd C:\Users\roial\Documents\Fun-Repos\IPTV-APP-V2
venv\Scripts\activate
pip install -r requirements-desktop.txt
```

### 2. Install VLC

Download and install VLC from: https://www.videolan.org/vlc/

**Important**: Install the standard VLC media player, not just the python-vlc library.

### 3. Run the App

```bash
python main.py
```

### 4. Test Video Playback

1. Create a profile with an M3U URL
2. Select a channel
3. Click "Play" or "Fullscreen"
4. Video should play embedded within the app

## How It Works

**Desktop (Windows/Linux/Mac):**
- Uses `python-vlc` library to embed VLC player within Kivy window
- Renders video directly in the app window
- Supports pause/play controls
- No need for GStreamer or ffpyplayer

**Android:**
- Uses native Kivy Video widget
- Works with Android's built-in MediaPlayer
- Full touch controls

## Troubleshooting

### "VLC library not found"

**Solution**:
```bash
pip install python-vlc
```

Make sure VLC media player is also installed on your system.

### Video shows black screen

**Windows**:
- Make sure you installed the regular VLC media player (not just python-vlc)
- Try reinstalling VLC
- Check if VLC works standalone with the stream URL

**Linux**:
```bash
sudo apt-get install vlc libvlc-dev
pip install python-vlc
```

**Mac**:
```bash
brew install vlc
pip install python-vlc
```

### "Window handle error"

This can happen if Kivy's window isn't fully initialized. Try:
- Restarting the app
- Making the window fullscreen before playing

### Stream doesn't load

- Test the stream URL in VLC standalone first
- Check your internet connection
- Some streams may require specific headers (not currently supported)

## Platform Differences

| Feature | Desktop | Android |
|---------|---------|---------|
| Video Backend | python-vlc (embedded) | Native Video widget |
| Installation | pip install python-vlc | Built-in |
| Controls | Play/Pause, Back | Play/Pause, Back, Volume |
| Setup Required | VLC media player | None |

## Android Build

For building the Android APK, see [BUILDOZER_DEBUG.md](BUILDOZER_DEBUG.md).

The Android version does NOT require python-vlc - it uses Kivy's native video support.
