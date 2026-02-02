# IPTV-Saba User Guide

## Table of Contents

1. [Getting Started](#getting-started)
2. [Profile Management](#profile-management)
3. [Browsing Channels](#browsing-channels)
4. [Video Playback](#video-playback)
5. [Favorites and History](#favorites-and-history)
6. [Easy Mode](#easy-mode)
7. [Download and Recording](#download-and-recording)
8. [Keyboard Shortcuts](#keyboard-shortcuts)
9. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements

- **Operating System:** Windows 10+, Linux, or macOS
- **Python:** 3.8 or higher
- **VLC Media Player:** Must be installed on your system
- **Internet Connection:** Required for streaming

### Installation

1. **Install VLC Media Player** from [videolan.org](https://www.videolan.org/)

2. **Clone the repository:**
   ```bash
   git clone https://github.com/Roialfassi/IPTV-Saba.git
   cd IPTV-Saba
   ```

3. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv

   # Windows
   venv\Scripts\activate

   # Linux/macOS
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application:**
   ```bash
   cd src
   python iptv_app.py
   ```

### First Launch

On first launch, the application will:
1. Create a configuration directory (`IPTV-Saba/`)
2. Create a test profile with sample channels
3. Show the login screen

---

## Profile Management

### Understanding Profiles

A profile stores:
- Your M3U playlist URL
- Favorite channels
- Watch history
- Last loaded timestamp

### Creating a Profile

1. Click **"Create Profile"** on the login screen
2. Enter a **profile name** (e.g., "My IPTV")
3. Enter your **M3U playlist URL**
4. Click **"Create"**

### Selecting a Profile

1. Click on a profile in the list
2. Optionally check **"Remember this profile"** for auto-login
3. Click **"Login"**

### Auto-Login

Enable auto-login to skip the profile selection screen:
1. Select your profile
2. Check **"Remember this profile"**
3. Log in

To disable auto-login:
1. Click **"Logout"** from the main screen
2. This disables auto-login for next launch

### Profile Data Location

Your profiles are stored in:
- **Windows:** `<current_directory>\IPTV-Saba\profiles.json`
- **Linux/macOS:** `<current_directory>/IPTV-Saba/profiles.json`

---

## Browsing Channels

### Main Interface

The main screen has three areas:
- **Left Panel:** Group list and channel list
- **Right Panel:** Video player and controls
- **Header:** Logout button

### Navigating Groups

1. Groups are listed in the top-left area
2. Click a group to show its channels
3. Use the **search bar** to filter groups

### Finding Channels

1. Select a group first
2. Channels appear below the group list
3. Use the **channel search bar** to filter
4. Click a channel to start playback

### Search Tips

- Search is case-insensitive
- Partial matches work (e.g., "news" finds "BBC News")
- Search within the current group view

---

## Video Playback

### Basic Controls

| Button | Action |
|--------|--------|
| **Play** | Resume playback |
| **Pause** | Pause playback |
| **Stop** | Stop playback |
| **Fullscreen** | Enter fullscreen mode |
| **Volume Slider** | Adjust volume (0-100) |

### Fullscreen Mode

**Enter fullscreen:**
- Click the **"Fullscreen"** button
- Or select a channel and click fullscreen

**Exit fullscreen:**
- Press **Escape**
- Or click **"Back to Channels"**

**Controls in fullscreen:**
- Move mouse to show controls
- Controls auto-hide after 3-5 seconds

### Video Player Features

- Seamless transitions between embedded and fullscreen
- Volume persistence across views
- Playback position maintained during transitions
- Connection timeout detection (15 seconds)

---

## Favorites and History

### Adding Favorites

1. **Right-click** a channel in the list
2. Select **"Add to Favorites"**

Or from the channel context menu.

### Viewing Favorites

1. Click the **"Favorites"** button
2. Channel list shows your favorites
3. Click any favorite to play

### Removing Favorites

1. **Right-click** a channel
2. Select **"Remove from Favorites"**

### Watch History

The app automatically tracks your last 10 watched channels.

**View history:**
1. Click the **"History"** button
2. Recent channels appear in order

**Note:** History is limited to 10 items (oldest removed automatically)

---

## Easy Mode

Easy Mode is designed for users who want a simplified interface.

### Requirements

- You must have **at least one favorite** channel to use Easy Mode

### Entering Easy Mode

1. From the login screen, select a profile
2. Click **"Easy Mode"**

### Easy Mode Controls

| Control | Action |
|---------|--------|
| **Previous** | Go to previous favorite |
| **Next** | Go to next favorite |
| **Fullscreen** | Toggle fullscreen |
| **Exit Easy Mode** | Return to login |
| **Volume Slider** | Adjust volume |

### Keyboard Shortcuts in Easy Mode

| Key | Action |
|-----|--------|
| **Left Arrow** | Previous channel |
| **Right Arrow** | Next channel |
| **Up Arrow** | Volume up |
| **Down Arrow** | Volume down |
| **Space** | Play/Pause |
| **F** | Toggle fullscreen |
| **Escape** | Exit fullscreen or Easy Mode |

---

## Download and Recording

### Downloading Media Files

Some channels (VOD/movies) can be downloaded:

1. **Right-click** a channel
2. If downloadable, you'll see **"Download"**
3. Confirm the download
4. File saves to `IPTV-Saba/downloads/`

### Recording Live Streams

Live streams can be recorded:

1. **Right-click** a live channel
2. Click **"Start Recording"**
3. The recording starts immediately
4. To stop: **right-click** and **"Stop Recording"**

### Download Location

Files are saved to:
```
IPTV-Saba/downloads/
├── ChannelName_download_20240101_120000.mp4
└── ChannelName_recording_20240101_130000.mp4
```

### File Naming

- **Downloads:** `{channel}_download_{timestamp}.{ext}`
- **Recordings:** `{channel}_recording_{timestamp}.mp4`

---

## Keyboard Shortcuts

### Main Screen (Choose Channel)

| Key | Action |
|-----|--------|
| **Click channel** | Start playback |
| **Right-click channel** | Context menu |

### Fullscreen View

| Key | Action |
|-----|--------|
| **Escape** | Exit fullscreen |
| **Space** | Play/Pause |
| **Up Arrow** | Volume +10 |
| **Down Arrow** | Volume -10 |

### Easy Mode

| Key | Action |
|-----|--------|
| **Left Arrow** | Previous channel |
| **Right Arrow** | Next channel |
| **Up Arrow** | Volume +5 |
| **Down Arrow** | Volume -5 |
| **Space** | Play/Pause |
| **F** | Toggle fullscreen |
| **Escape** | Exit fullscreen/Easy Mode |

---

## Troubleshooting

### Common Issues

#### "VLC not found" or "No video"

**Solution:**
1. Install VLC Media Player
2. On Windows, ensure VLC is in default location:
   `C:\Program Files\VideoLAN\VLC\`

#### Black screen in fullscreen

**Solution:**
1. Wait a moment (video reattaches)
2. If persistent, press Escape and try again

#### Channels not loading

**Possible causes:**
- Invalid M3U URL
- Network issues
- URL requires authentication

**Solutions:**
1. Check your internet connection
2. Verify the M3U URL works in a browser
3. Wait for retry (app retries 3 times)

#### "Connection timeout"

The stream failed to connect within 15 seconds.

**Solutions:**
1. Check your internet connection
2. The stream may be offline
3. Try a different channel

#### "Stream error"

The VLC player encountered an error.

**Solutions:**
1. The stream may be offline
2. The stream format may be unsupported
3. Try a different channel

### Cache Issues

Channel data is cached for 24 hours. To force refresh:

1. Wait 24 hours (automatic refresh)
2. Or manually delete the cache file:
   `IPTV-Saba/{profile_name}data.json`

### Log Files

For debugging, check the console output. The app logs:
- Profile operations
- Channel loading progress
- Playback events
- Errors and warnings

### Resetting the Application

To completely reset:
1. Close the application
2. Delete the `IPTV-Saba/` folder
3. Restart the application

---

## Tips and Tricks

### Performance Tips

1. **Large playlists:** The optimized loader handles 10+ MB playlists efficiently
2. **Cache:** Let the app cache data (24h) for faster startup
3. **Favorites:** Use favorites for quick access to frequent channels

### Organization Tips

1. Use the search feature to find channels quickly
2. Add your most-watched channels to favorites
3. Create separate profiles for different playlist sources

### Playback Tips

1. If a stream buffers, it may be the source quality
2. Use the volume slider to set comfortable levels
3. Fullscreen mode auto-hides controls for immersion

---

## Getting Help

- **GitHub Issues:** [Report bugs or request features](https://github.com/Roialfassi/IPTV-Saba/issues)
- **Documentation:** Check the `docs/` folder
- **CLAUDE.md:** Developer documentation for contributing
