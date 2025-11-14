# IPTV Saba v2.0.0

Professional IPTV player with integrated download manager and modern UI.

## Features

### Core Features
- ✅ M3U/M3U8 playlist support
- ✅ Multi-profile management
- ✅ Channel browsing and search
- ✅ Group organization
- ✅ Full-featured video player
- ✅ Integrated download manager
- ✅ Fullscreen mode
- ✅ Auto-login support
- ✅ Favorites and history tracking

### Player Features
- Hardware-accelerated playback via VLC
- Floating overlay controls
- Auto-hide controls
- Keyboard shortcuts
- Context menu
- Volume control
- Playback position tracking

### Download Features
- Queue-based download manager
- Concurrent downloads (configurable)
- Progress tracking with speed/ETA
- FFmpeg integration
- Download history

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python -m app.main
```

## Building Executable

See [EXPORT_GUIDE.md](../EXPORT_GUIDE.md) for complete instructions.

```bash
pip install pyinstaller
pyinstaller --onefile --windowed app/main.py
```

## Documentation

- **Export Guide**: Complete build and distribution guide
- **Architecture**: See source code docstrings
- **API**: Services are self-documented

## Support

GitHub: https://github.com/Roialfassi/IPTV-Saba
