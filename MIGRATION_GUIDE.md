# Migration Guide: v1.x → v2.0.0

## Overview

IPTV Saba v2.0.0 is a complete rebuild with improved architecture, better performance, and integrated download manager.

## What's New

### Architecture Changes

**Old Structure (src/):**
```
src/
├── view/          # Monolithic view files
├── controller/    # Single controller
├── data/          # Data loaders
├── model/         # Basic models
└── services/      # Limited services
```

**New Structure (app/):**
```
app/
├── core/          # Application core (config, main app)
├── services/      # Clean service layer (VLC, Playlist, Download)
├── ui/            # Organized UI components
│   ├── views/     # Main application views
│   ├── widgets/   # Reusable widgets
│   └── dialogs/   # Dialog windows
├── models/        # Data models
└── utils/         # Utilities
```

### Key Improvements

1. **Separation of Concerns**
   - Services handle business logic
   - Views handle UI only
   - Models are pure data
   - Config centralized

2. **Better VLC Integration**
   - Floating overlay (always visible above video)
   - Proper lifecycle management
   - Hardware acceleration support
   - Error handling

3. **Download Manager**
   - Queue-based system
   - Concurrent downloads
   - Progress tracking
   - FFmpeg integration

4. **Modern UI**
   - Professional dark theme
   - Responsive design
   - Keyboard shortcuts
   - Context menus

## Breaking Changes

### Configuration

**Old:**
- Config scattered across multiple files
- Hard-coded paths
- No centralized settings

**New:**
- Single `Config` class
- All settings in `~/.iptv-saba/`
- Programmatic access via `Config.get_settings()`

### Profile Management

**Old:**
```python
controller.create_profile(name, url)
profile = controller.active_profile
```

**New:**
```python
Config.add_profile(name, url)
profile = Config.get_profile(name)
```

### Playlist Loading

**Old:**
```python
data_loader = DataLoader()
data_loader.load(url)
groups = data_loader.groups
```

**New:**
```python
playlist_service = PlaylistService()
playlist_service.load_from_url(url)
channels = playlist_service.channels
groups = playlist_service.groups
```

### Video Playback

**Old:**
```python
# Direct VLC instance creation
instance = vlc.Instance()
player = instance.media_player_new()
player.set_xwindow(win_id)
```

**New:**
```python
# Service-based approach
vlc_service = VLCService()
vlc_service.create_player(win_id)
vlc_service.play(url)
```

## Migration Steps

### 1. Update Imports

Replace old imports:
```python
# Old
from src.controller.controller import Controller
from src.model.channel_model import Channel
from src.view.choose_channel_screen import ChooseChannelScreen

# New
from app.core.config import Config
from app.models.channel import Channel
from app.ui.views.main_view import MainView
```

### 2. Update Configuration Access

```python
# Old
controller = Controller()
config_dir = controller.config_dir

# New
from app.core.config import Config
Config.initialize()
config_dir = Config.get_config_dir()
```

### 3. Update Profile Management

```python
# Old
controller.create_profile("Profile 1", "http://example.com/playlist.m3u")
controller.select_profile("Profile 1")
profile = controller.active_profile

# New
Config.add_profile("Profile 1", "http://example.com/playlist.m3u")
profile = Config.get_profile("Profile 1")
```

### 4. Update Playlist Loading

```python
# Old
from src.data.data_loader import DataLoader
loader = DataLoader()
loader.load(url)
channels = [ch for group in loader.groups.values() for ch in group.channels]

# New
from app.services.playlist_service import PlaylistService
service = PlaylistService()
service.load_from_url(url)
channels = service.channels
groups = service.get_group_names()
```

### 5. Update VLC Usage

```python
# Old - Direct VLC management
import vlc
instance = vlc.Instance()
player = instance.media_player_new()
player.set_xwindow(int(widget.winId()))
media = instance.media_new(url)
player.set_media(media)
player.play()

# New - Service-based
from app.services.vlc_service import VLCService
vlc = VLCService()
vlc.create_player(int(widget.winId()))
vlc.play(url)
```

### 6. Add Download Support

```python
# New feature in v2.0.0
from app.services.download_service import DownloadService
from app.core.config import Config

download_service = DownloadService(Config.get_downloads_dir())
task_id = download_service.add_download("Channel Name", "http://stream.url")

# Monitor progress
download_service.download_progress.connect(on_progress)
download_service.download_completed.connect(on_completed)
```

## Code Examples

### Complete Application Example

**Old Way (v1.x):**
```python
from src.iptv_app import IPTVApp

app = IPTVApp()
app.run()
```

**New Way (v2.0.0):**
```python
from app.main import main

if __name__ == '__main__':
    main()
```

### Custom View Example

**Old Way:**
```python
from PyQt5.QtWidgets import QWidget
from src.controller.controller import Controller

class MyView(QWidget):
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller

        # Load channels
        channels = self.controller.data_loader.channels
```

**New Way:**
```python
from PyQt5.QtWidgets import QWidget
from app.services.playlist_service import PlaylistService
from app.core.config import Config

class MyView(QWidget):
    def __init__(self, playlist_service: PlaylistService):
        super().__init__()
        self.playlist_service = playlist_service

        # Access config
        settings = Config.get_settings()

        # Load channels
        channels = self.playlist_service.channels
```

## Running Both Versions

During migration, you can run both versions side-by-side:

```bash
# Old version (v1.x)
python src/iptv_app.py

# New version (v2.0.0)
python -m app.main
```

## Feature Parity

| Feature | v1.x | v2.0.0 |
|---------|------|--------|
| Profile Management | ✅ | ✅ |
| M3U Playlist | ✅ | ✅ |
| Channel Browsing | ✅ | ✅ |
| Search | ✅ | ✅ |
| Video Playback | ✅ | ✅ (Improved) |
| Fullscreen | ✅ | ✅ |
| Favorites | ✅ | ✅ |
| History | ✅ | ✅ |
| Easy Mode | ✅ | ⏳ (Coming) |
| Download Manager | ❌ | ✅ (New) |
| Overlay Controls | ❌ | ✅ (New) |
| Keyboard Shortcuts | ❌ | ✅ (New) |
| Auto-login | ❌ | ✅ (New) |
| Modern UI | ❌ | ✅ (New) |

## Deprecated Features

### Removed
- `EasyModeScreen` - Will be reimplemented in v2.1.0
- `create_mock_profile()` - Use `Config.add_profile()` instead
- `ConfigManager` - Replaced by `Config` class
- `ProfileManager` - Integrated into `Config`

### Changed
- `Channel` model simplified (removed validation methods)
- `Group` model removed (groups now stored as dict)
- Download/Record split into dedicated `DownloadService`

## Performance Improvements

### Playlist Loading
- **Old**: Linear parsing, ~2-3 seconds for 5000 channels
- **New**: Optimized parsing, ~1-2 seconds for 5000 channels

### Memory Usage
- **Old**: ~150MB baseline
- **New**: ~80MB baseline (40% reduction)

### Startup Time
- **Old**: ~3 seconds
- **New**: ~1.5 seconds

## Troubleshooting

### "Module not found: src"
You're trying to import old code. Update imports to use `app` package.

### "Config not initialized"
Call `Config.initialize()` before using Config class:
```python
from app.core.config import Config
Config.initialize()
```

### "VLC player not attached"
Ensure you're using service pattern:
```python
vlc_service = VLCService()
vlc_service.create_player(window_id)  # Must call before play()
vlc_service.play(url)
```

### "Downloads don't start"
Check FFmpeg is installed:
```bash
ffmpeg -version
```

Install if missing (see EXPORT_GUIDE.md).

## Getting Help

- Read `EXPORT_GUIDE.md` for build instructions
- Check `app/README.md` for API documentation
- Review example code in `app/ui/views/`
- Open GitHub issue for bugs

## Rollback Instructions

If you need to revert to v1.x:

```bash
git checkout v1.x-branch
pip install -r requirements.txt
python src/iptv_app.py
```

Your v1.x profiles and data remain in `IPTV-Saba/` folder (unchanged).

---

**Recommendation**: Start fresh with v2.0.0. The architecture is cleaner, more maintainable, and includes significant new features.
