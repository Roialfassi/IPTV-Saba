# Download & Record Feature Documentation

## Overview

The IPTV-Saba app now supports downloading media files and recording live streams directly from the interface!

## Features

### 📥 Download Media Files
- **Automatic Detection**: The app automatically detects if a channel URL points to a downloadable media file (.mp4, .mkv, .avi, etc.)
- **One-Click Download**: Right-click any channel and select "📥 Download"
- **Progress Tracking**: Real-time download progress with byte-level tracking
- **Automatic Naming**: Files are automatically named with channel name + timestamp

### 🔴 Record Live Streams
- **Stream Recording**: Record any live stream in real-time
- **Start/Stop Control**: Easy start and stop recording from the context menu
- **VLC-Powered**: Uses VLC's recording capabilities for high-quality captures
- **Background Recording**: Continue watching while recording runs in the background

## Usage

### Download a Media File

1. **Find a Channel**: Browse your channels in the main screen
2. **Right-Click**: Right-click on any channel
3. **Select Download**: If it's a media file, you'll see "📥 Download"
4. **Confirm**: Click "Yes" to start downloading
5. **Wait**: The download runs in the background
6. **Done**: You'll get a notification when complete!

### Record a Live Stream

1. **Find a Stream**: Browse your channels
2. **Right-Click**: Right-click on a live stream channel
3. **Start Recording**: Select "🔴 Start Recording"
4. **Confirm**: Click "Yes" to begin recording
5. **Stop When Done**: Right-click again and select "⏹️ Stop Recording"
6. **Save Complete**: You'll be notified where the recording was saved!

## File Locations

All downloads and recordings are saved to:
```
<Your IPTV-Saba Folder>/downloads/
```

Example locations:
- **Windows**: `C:\Users\YourName\IPTV-Saba\downloads\`
- **Linux**: `/home/username/IPTV-Saba/downloads/`
- **Mac**: `/Users/YourName/IPTV-Saba/downloads/`

## File Naming Convention

Files are automatically named using this pattern:
```
{channel_name}_{type}_{timestamp}.{ext}
```

Examples:
- `CNN_News_download_20250104_143022.mp4`
- `Sports_HD_recording_20250104_150145.ts`

## Supported Media Formats

### Downloads
- `.mp4` - MPEG-4 Video
- `.mkv` - Matroska Video
- `.avi` - Audio Video Interleave
- `.mov` - QuickTime Movie
- `.flv` - Flash Video
- `.wmv` - Windows Media Video
- `.m4v` - iTunes Video
- `.mpg` / `.mpeg` - MPEG Video
- `.ts` - Transport Stream

### Recordings
- Recordings are saved in `.mp4` format by default
- Compatible with all major video players

## Technical Details

### Architecture

```
User Action (Right-Click)
        ↓
Context Menu Detection
        ↓
DownloadRecordManager
        ↓
┌────────────────┬────────────────┐
│   Download     │    Recording   │
│   (Thread)     │   (VLC)        │
└───────┬────────┴────────┬───────┘
        │                 │
    Progress            Status
    Signals             Signals
        │                 │
        └────────┬────────┘
                 ↓
          UI Notifications
```

### Download Manager Features

1. **Thread-Safe Operations**: All downloads run in separate threads
2. **Concurrent Downloads**: Multiple downloads can run simultaneously
3. **Cancel Support**: Downloads can be cancelled mid-way
4. **Error Handling**: Robust error handling with user notifications
5. **Cleanup**: Partial files are automatically removed on failure

### Recording Manager Features

1. **VLC Integration**: Uses VLC's proven recording engine
2. **Live Monitoring**: Track active recordings
3. **Graceful Shutdown**: Properly finalizes recordings on stop
4. **Multiple Recordings**: Record multiple streams simultaneously

## UI Integration

### Context Menu
- **Dynamic Menu**: Menu items change based on stream type
- **Visual Indicators**: Emojis show current state (📥, 🔴, ⏹️)
- **Smart Detection**: Automatically knows if it's a file or stream

### Notifications
- **Download Started**: Confirmation when download begins
- **Download Complete**: Shows save location
- **Recording Started**: Confirmation with instructions
- **Recording Stopped**: Shows save location
- **Errors**: Clear error messages with details

## Bug Fixes

### Dual Stream Bug - FIXED! ✅

**Problem**: When entering fullscreen, two streams would play simultaneously:
1. Original stream in choose_channel_screen
2. New stream in fullscreen_view

**Solution**:
- FullScreenView now reuses the existing VLC player instance
- Player is properly detached/reattached when switching views
- Seamless transition with no audio/video duplication

**Technical Implementation**:
```python
# Old (buggy):
fullscreen_view = FullScreenView(channel)  # Creates new player

# New (fixed):
fullscreen_view = FullScreenView(
    channel,
    existing_player=self.player,  # Reuse player
    existing_instance=self.instance
)
```

## Troubleshooting

### Download Not Starting
- **Check Internet**: Ensure you have a working internet connection
- **Check URL**: Some URLs may require authentication
- **Check Space**: Ensure you have sufficient disk space

### Recording Not Working
- **VLC Required**: Ensure VLC is properly installed
- **Permissions**: Check folder write permissions
- **Stream Type**: Some encrypted streams may not record

### File Not Found
- **Check Downloads Folder**: Navigate to the downloads directory
- **Check Completion**: Ensure download/recording finished
- **Check Logs**: Look at console logs for error messages

## Performance

### Download Speed
- **Optimized Chunks**: Uses 64KB chunks for efficient downloading
- **Progress Updates**: Real-time progress without performance impact
- **Network Adaptive**: Adjusts to available bandwidth

### Recording Performance
- **Low CPU**: VLC handles recording efficiently
- **Low Memory**: Minimal memory overhead
- **Background Operation**: Won't affect UI responsiveness

## Safety & Privacy

### Data Handling
- **Local Storage**: All files saved locally
- **No Cloud**: No uploads to external servers
- **User Control**: User has full control over files

### Cleanup
- **Auto-Cleanup**: Failed downloads automatically removed
- **Manual Cleanup**: Users can delete files anytime
- **Stop Protection**: Confirmation required before stopping recordings

## Future Enhancements

Potential future features:
- **Progress Bar**: Visual progress bar in UI
- **Scheduled Recording**: Set start/end times
- **Quality Selection**: Choose recording quality
- **Format Conversion**: Convert recordings to different formats
- **Cloud Backup**: Optional cloud storage integration
- **Playlist Download**: Download entire playlists

## API Reference

### DownloadRecordManager

```python
# Initialize
manager = DownloadRecordManager(downloads_dir="path/to/downloads")

# Check if URL is downloadable
is_file = manager.is_media_file(url)

# Start download
manager.start_download(download_id, channel_name, url)

# Start recording
manager.start_recording(recording_id, channel_name, url)

# Stop recording
manager.stop_recording(recording_id)

# Cleanup all
manager.cleanup_all()
```

### Signals

```python
# Connect to signals
manager.download_progress.connect(on_progress)
manager.download_complete.connect(on_complete)
manager.download_error.connect(on_error)
manager.recording_started.connect(on_recording_start)
manager.recording_stopped.connect(on_recording_stop)
```

## Credits

Download and recording functionality implemented with:
- **VLC Media Player**: Recording engine
- **Python Requests**: Download handling
- **PyQt5**: UI integration
- **Threading**: Concurrent operations
