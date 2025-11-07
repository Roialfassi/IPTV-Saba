# Video Playback Guide

## Desktop (Windows/Linux/Mac)

Kivy requires a video backend to play streams. You have two options:

### Option 1: GStreamer (Recommended)

**Windows:**
1. Download GStreamer runtime installer from: https://gstreamer.freedesktop.org/download/
2. Install both the runtime AND development packages
3. Make sure to select "Add to PATH" during installation
4. Restart your terminal/IDE after installation

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
                     gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
                     gstreamer1.0-libav python3-gst-1.0
```

**Mac:**
```bash
brew install gstreamer gst-plugins-base gst-plugins-good \
             gst-plugins-bad gst-plugins-ugly gst-libav
```

### Option 2: ffpyplayer

Install via pip:
```bash
pip install ffpyplayer
```

**Note:** ffpyplayer may have issues with HLS/M3U8 streams. GStreamer is more reliable.

## Android

Video playback works automatically on Android using the native MediaPlayer. No additional setup required.

## Troubleshooting

### "Video backend not available" error
- On Windows: Make sure GStreamer is installed and added to PATH
- Try reinstalling Kivy after installing GStreamer: `pip install --force-reinstall kivy`

### HLS/M3U8 streams not playing
- HLS streams require proper codec support
- Make sure you installed the "ugly" and "bad" plugins for GStreamer (they contain the codecs)
- On Windows, restart your computer after installing GStreamer

### Video shows black screen
- Check if the stream URL is accessible in a browser/VLC first
- Some streams may require headers or authentication
- Try a different stream to verify the video backend is working

## Testing Video Backend

Run this Python script to test if video backend is available:

```python
from kivy.core.video import Video
print(f"Available video providers: {Video.providers}")
```

You should see something like:
- Windows: `['gstplayer', 'ffpyplayer']`
- Linux: `['gstplayer', 'ffpyplayer']`
- Android: `['android']`
