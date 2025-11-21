# CLAUDE.md - AI Assistant Guide for IPTV-Saba

**Last Updated**: 2025-11-21
**Version**: 1.0.0

This document provides comprehensive guidance for AI assistants working on the IPTV-Saba codebase. It covers architecture, conventions, workflows, and best practices to ensure consistent, high-quality contributions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Directory Structure](#directory-structure)
4. [Development Setup](#development-setup)
5. [Key Components](#key-components)
6. [Coding Conventions](#coding-conventions)
7. [Data Management](#data-management)
8. [UI Framework and Patterns](#ui-framework-and-patterns)
9. [Video Playback](#video-playback)
10. [Testing Guidelines](#testing-guidelines)
11. [Common Development Tasks](#common-development-tasks)
12. [Git Workflow](#git-workflow)
13. [Important Files Reference](#important-files-reference)
14. [Known Issues and Solutions](#known-issues-and-solutions)

---

## Project Overview

**IPTV-Saba** is a desktop IPTV streaming application built with Python and PyQt5, featuring profile management, channel favorites, and a simplified "Easy Mode" for elderly users.

### Key Features
- Multiple user profiles with separate M3U playlists
- Channel browsing with categories and search
- Favorites and watch history tracking
- Full-screen video playback with VLC
- Easy Mode (simplified UI for elderly users)
- Download and record streaming content

### Technology Stack
- **Language**: Python 3.8+
- **UI Framework**: PyQt5 (5.15.11)
- **Video Playback**: python-vlc (3.0.21203)
- **Data Format**: JSON for persistence
- **Networking**: requests, aiohttp
- **Architecture**: MVC (Model-View-Controller)

### Target Platforms
- Windows (primary)
- Linux (tested)
- macOS (supported)

---

## Architecture

### MVC Pattern

The application follows a clean MVC architecture with an additional service layer:

```
┌──────────────────────────────────────────────────────┐
│                    IPTVApp (Main)                     │
│  • Application entry point and lifecycle manager     │
│  • Screen transition orchestration                   │
└──────────────────────┬───────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────┐
│                  Controller Layer                     │
│  • Central coordinator (controller.py)               │
│  • Signal/slot event handling                        │
│  • Business logic orchestration                      │
└────┬────────────┬─────────────┬──────────────────────┘
     │            │             │
     ▼            ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│  Model  │  │   View   │  │  Data Layer  │
│ Layer   │  │  Layer   │  │              │
└─────────┘  └──────────┘  └──────────────┘
```

### Component Relationships

```
Controller
├── ProfileManager    # Profile CRUD operations
├── DataLoader        # M3U playlist parsing
├── ConfigManager     # App configuration
└── DownloadRecordManager  # Download/record orchestration

Model
├── Profile           # User profile entity
├── Channel           # Channel entity (dataclass)
└── Group             # Channel group entity (dataclass)

View
├── LoginScreen       # Profile selection
├── ChooseChannelScreen  # Main channel browser
├── FullScreenView    # Fullscreen player
└── EasyModeScreen    # Simplified UI
```

### Design Patterns Used

1. **MVC Pattern**: Separation of concerns
2. **Observer Pattern**: PyQt5 signals/slots for event-driven communication
3. **Repository Pattern**: ProfileManager, DataLoader abstract data access
4. **Worker Thread Pattern**: Background data loading to keep UI responsive
5. **Singleton-like Controller**: Central coordinator for application state

---

## Directory Structure

```
/home/user/IPTV-Saba/
│
├── src/                          # Main source code
│   ├── iptv_app.py              # Application entry point (MAIN)
│   │
│   ├── controller/              # Controller layer
│   │   └── controller.py        # Central application controller
│   │
│   ├── model/                   # Data models
│   │   ├── channel_model.py    # Channel entity (dataclass)
│   │   ├── group_model.py      # Channel group entity (dataclass)
│   │   └── profile.py          # User profile entity
│   │
│   ├── view/                    # UI layer (PyQt5)
│   │   ├── login_view.py       # Profile selection screen
│   │   ├── choose_channel_screen.py  # Main channel browser
│   │   ├── full_screen_view.py # Fullscreen player
│   │   ├── easy_mode_screen.py # Simplified UI for elderly
│   │   └── ccs_v2.py           # Additional view components
│   │
│   ├── data/                    # Data access layer
│   │   ├── config_manager.py   # Application configuration
│   │   ├── data_loader.py      # M3U playlist parser (CRITICAL)
│   │   ├── profile_manager.py  # Profile CRUD operations
│   │   ├── recorder.py         # Stream recording
│   │   └── downloader.py       # Media downloading
│   │
│   ├── services/                # Business logic services
│   │   └── download_record_manager.py  # Download/record orchestration
│   │
│   └── Assets/                  # Application resources
│       └── iptv-logo2.ico      # Application icon
│
├── requirements.txt             # Python dependencies (PINNED VERSIONS)
│
├── test_simple.py              # Basic functionality tests
├── test_optimized_loader.py    # Performance benchmarks
├── test_sample.m3u             # Test M3U playlist
│
├── README.md                   # User-facing documentation
├── OPTIMIZATION_DETAILS.md     # DataLoader optimization docs
├── DOWNLOAD_RECORD_FEATURE.md  # Download/record feature docs
├── FULLSCREEN_FIX_DETAILS.md   # Fullscreen bug fix details
│
└── .gitignore                  # Git exclusions
```

### Data Storage Location

**Runtime data**: `/home/user/IPTV-Saba/IPTV-Saba/` (configurable)

```
IPTV-Saba/
├── profiles.json               # User profiles with favorites/history
├── config.json                 # App configuration
├── {profile_name}data.json     # Cached channel data (24h TTL)
└── downloads/                  # Downloaded/recorded media
```

---

## Development Setup

### Prerequisites

1. **Python 3.8+** installed
2. **VLC Media Player** installed on the system
3. **pip** for package management

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/Roialfassi/IPTV-Saba.git
cd IPTV-Saba

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application

```bash
cd src
python iptv_app.py
```

### Development Tools

- **Editor**: Any Python IDE (VS Code, PyCharm recommended)
- **Debugger**: Built-in Python debugger or IDE debugger
- **Logging**: Application uses Python's `logging` module at DEBUG level

---

## Key Components

### 1. Controller (`src/controller/controller.py`)

**Purpose**: Central coordinator for application logic and state management.

**Key Responsibilities**:
- Manage active profile and current channels
- Coordinate between ProfileManager, DataLoader, and ConfigManager
- Emit signals for UI updates
- Handle profile CRUD operations
- Manage favorites and history

**Important Methods**:
```python
select_profile(profile_name: str)  # Load and activate a profile
create_profile(name: str, url: str)  # Create new profile
delete_profile(name: str)  # Remove profile
add_to_favorites(channel_name: str)  # Add channel to favorites
add_to_history(channel_name: str)  # Track watch history
search_channels(query: str)  # Search channels by name
```

**Signals**:
- `profiles_updated`: Emitted when profile list changes
- `profile_selected`: Emitted when profile is activated
- `data_loaded`: Emitted when channel data is loaded
- `error_occurred(str)`: Emitted on errors

**Usage Pattern**:
```python
from controller.controller import Controller

controller = Controller()
controller.profiles_updated.connect(self.on_profiles_updated)
controller.select_profile("User1")
```

### 2. DataLoader (`src/data/data_loader.py`)

**Purpose**: Parse M3U playlists efficiently with optimization for large files.

**Key Features**:
- Streaming parser (64KB chunks)
- Parallel processing with 4 worker threads
- Encoding detection (chardet)
- Caching to JSON for performance
- Handles 10+ MB playlists

**Important Methods**:
```python
load_from_url(url: str) -> List[Group]  # Parse M3U from URL
load_from_file(file_path: str) -> List[Group]  # Parse local M3U
save_to_json(file_path: str)  # Cache parsed data
load_from_json(file_path: str) -> List[Group]  # Load from cache
```

**Performance Note**: The optimized loader is 2-5x faster than traditional parsing. See `OPTIMIZATION_DETAILS.md` for details.

**Usage Pattern**:
```python
from data.data_loader import DataLoader

loader = DataLoader()
groups = loader.load_from_url("https://example.com/playlist.m3u")
loader.save_to_json("/path/to/cache.json")  # Cache for future use
```

### 3. ProfileManager (`src/data/profile_manager.py`)

**Purpose**: Thread-safe profile management with persistence.

**Key Features**:
- Atomic file operations with rollback
- Thread-safe with RLock
- Import/export functionality
- Dual data structures (dict + list) for fast lookup

**Important Methods**:
```python
create_profile(name: str, url: str) -> Profile  # Create profile
get_profile(name: str) -> Optional[Profile]  # Retrieve profile
delete_profile(name: str) -> bool  # Remove profile
list_profiles() -> List[str]  # Get all profile names
update_profile(name: str, profile: Profile)  # Save changes
export_profile(name: str, file_path: str)  # Backup profile
import_profile(file_path: str) -> Profile  # Restore profile
```

**Thread Safety**:
```python
with self.lock:  # Uses RLock for thread-safe operations
    self.profiles_dict[name] = profile
```

### 4. ConfigManager (`src/data/config_manager.py`)

**Purpose**: Manage application-wide configuration with persistence.

**Configuration Properties**:
- `last_active_profile_id`: Last selected profile
- `auto_login_enabled`: Auto-login on startup
- `theme`: UI theme (currently "default")
- `app_version`: Application version
- `first_run`: First-time setup flag
- `log_level`: Logging verbosity

**Usage Pattern**:
```python
from data.config_manager import ConfigManager

config = ConfigManager()
config.auto_login_enabled = True
config.last_active_profile_id = "User1"
# Changes are automatically saved to config.json
```

### 5. DownloadRecordManager (`src/services/download_record_manager.py`)

**Purpose**: Manage concurrent downloads and recordings with progress tracking.

**Key Features**:
- Thread-safe concurrent operations
- Progress signals for UI updates
- Sanitized filenames with timestamps
- Detects media files vs live streams

**Important Methods**:
```python
start_download(channel: Channel, save_path: str)  # Download media
start_recording(channel: Channel, save_path: str)  # Record live stream
stop_download(channel_name: str)  # Cancel download
stop_recording(channel_name: str)  # Stop recording
```

**Signals**:
- `download_started(str)`: Download/record initiated
- `download_progress(str, int)`: Progress update (0-100)
- `download_completed(str)`: Download/record finished
- `download_error(str, str)`: Error occurred

---

## Coding Conventions

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `ProfileManager`, `DataLoader` |
| Functions/Methods | snake_case | `load_profiles()`, `add_to_favorites()` |
| Constants | UPPER_SNAKE_CASE | `MEDIA_EXTENSIONS`, `DEFAULT_CONFIG` |
| Private methods | Leading underscore | `_parse_extinf()`, `_validate_profile_data()` |
| PyQt5 Signals | Descriptive past tense | `profiles_updated`, `login_success` |
| Module files | snake_case | `profile_manager.py`, `data_loader.py` |

### Code Style

**Follow PEP 8** with these specifics:

1. **Indentation**: 4 spaces (no tabs)
2. **Line Length**: Aim for 79 characters, max 100 for readability
3. **Imports**: Group standard library, third-party, local imports
   ```python
   import os
   import logging

   from PyQt5.QtCore import QObject, pyqtSignal

   from model.channel_model import Channel
   ```

4. **Docstrings**: Use triple quotes, describe Args and Returns
   ```python
   def search_channels(self, query: str) -> List[Channel]:
       """Search channels by name using fuzzy matching.

       Args:
           query: Search string to match against channel names

       Returns:
           List of matching Channel objects
       """
   ```

5. **Type Hints**: Use for method signatures
   ```python
   def find_channel_by_name(self, channel_name: str) -> Optional[Channel]:
       pass
   ```

6. **Error Handling**: Always log errors and emit signals
   ```python
   try:
       # Operation
       logger.info("Operation successful")
   except Exception as e:
       logger.error(f"Error occurred: {e}")
       self.error_occurred.emit(str(e))
   ```

### PyQt5 Patterns

**Signal/Slot Declaration**:
```python
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class MyController(QObject):
    # Declare signals
    data_ready = pyqtSignal()
    error_occurred = pyqtSignal(str)

    @pyqtSlot(str)
    def on_user_action(self, data: str):
        # Handle action
        self.data_ready.emit()
```

**Worker Thread Pattern**:
```python
class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)

    def run(self):
        # Heavy work here
        for i in range(100):
            # Process
            self.progress.emit(i)
        self.finished.emit()

# Usage
worker = Worker()
thread = QThread()
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.finished.connect(thread.quit)
thread.start()
```

### Dataclass Usage

Use `@dataclass` for simple data models:

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Channel:
    name: str
    stream_url: str
    tvg_id: str = ""
    tvg_logo: str = ""
    channel_type: str = ""
```

**When NOT to use dataclasses**:
- Complex initialization logic required (like `Profile`)
- Need custom `__init__` with validation

---

## Data Management

### Data Storage Format

**All data stored as JSON** in `IPTV-Saba/` directory.

#### profiles.json Structure

```json
[
  {
    "name": "User1",
    "url": "https://example.com/playlist.m3u",
    "favorites": [
      {
        "name": "CNN",
        "stream_url": "http://stream.url",
        "tvg_id": "cnn.us",
        "tvg_logo": "http://logo.url",
        "channel_type": ""
      }
    ],
    "history": [...],
    "last_loaded": 1700000000
  }
]
```

#### config.json Structure

```json
{
  "last_active_profile_id": "User1",
  "auto_login_enabled": true,
  "theme": "default",
  "app_version": "1.0.0",
  "first_run": false,
  "log_level": "INFO"
}
```

### Data Persistence Strategy

1. **Profiles**: Always in memory + JSON file (atomic writes)
2. **Channels**: Cached JSON with 24-hour TTL
3. **Config**: Immediate save on any change
4. **Downloads**: Stream directly to disk

### Thread Safety

**Always use locks for shared data**:

```python
from threading import RLock

class ProfileManager:
    def __init__(self):
        self.lock = RLock()

    def update_profile(self, name: str, profile: Profile):
        with self.lock:
            self.profiles_dict[name] = profile
            self.save()
```

### Atomic File Operations

**Pattern for safe file writes**:

```python
import tempfile
import os

def save_data(self, data, file_path):
    """Save data atomically with rollback capability."""
    # Write to temporary file first
    with tempfile.NamedTemporaryFile('w', delete=False) as tmp_file:
        json.dump(data, tmp_file, indent=2)
        tmp_path = tmp_file.name

    try:
        # Atomic replace
        os.replace(tmp_path, file_path)
    except Exception as e:
        # Cleanup on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise e
```

---

## UI Framework and Patterns

### PyQt5 Basics

**Window Structure**:
```python
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton

class MyScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        button = QPushButton("Click Me")
        button.clicked.connect(self.on_button_clicked)

        layout.addWidget(button)
        self.setLayout(layout)

    def on_button_clicked(self):
        print("Button clicked!")
```

### Styling Guidelines

**Color Palette** (Netflix-inspired):
- Primary Red: `#E50914`
- Hover Red: `#FF0909`
- Dark Background: `#141414`
- Secondary Dark: `#222222`
- Facebook Blue: `#1877F2` (secondary actions)

**Stylesheet Pattern**:
```python
button.setStyleSheet("""
    QPushButton {
        background-color: #e50914;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #ff0909;
    }
    QPushButton:pressed {
        background-color: #b00710;
    }
""")
```

**Gradient Backgrounds**:
```python
self.setStyleSheet("""
    QWidget {
        background: qlineargradient(
            x1:0, y1:0, x2:1, y2:1,
            stop:0 #141414,
            stop:1 #000000
        );
    }
""")
```

### Responsive UI Patterns

**Auto-hiding Controls** (used in FullScreenView):
```python
from PyQt5.QtCore import QTimer

class FullScreenView(QWidget):
    def __init__(self):
        super().__init__()
        self.controls_visible = True
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.hide_controls)

    def mouseMoveEvent(self, event):
        """Show controls on mouse movement."""
        self.show_controls()
        self.hide_timer.start(3000)  # Hide after 3 seconds

    def show_controls(self):
        self.controls_widget.show()
        self.controls_visible = True

    def hide_controls(self):
        self.controls_widget.hide()
        self.controls_visible = False
```

### Layout Best Practices

1. **Use QSplitter** for resizable sections
2. **Use QScrollArea** for long content
3. **Use QStackedWidget** for multi-page interfaces
4. **Use spacers** for flexible layouts:
   ```python
   layout.addStretch()  # Flexible space
   ```

---

## Video Playback

### VLC Integration

**Platform-Specific Window Attachment**:

```python
import vlc
import sys

def attach_player_to_widget(player, widget):
    """Attach VLC player to a Qt widget."""
    window_id = int(widget.winId())

    if sys.platform == "win32":
        player.set_hwnd(window_id)
    elif sys.platform.startswith('linux'):
        player.set_xwindow(window_id)
    elif sys.platform == "darwin":
        player.set_nsobject(window_id)
```

### Player Lifecycle

**IMPORTANT**: Reuse player instance to avoid dual streams.

```python
class ChooseChannelScreen(QWidget):
    def __init__(self):
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()

    def play_channel(self, channel: Channel):
        """Play a channel using the existing player."""
        media = self.vlc_instance.media_new(channel.stream_url)
        self.player.set_media(media)
        self.player.play()

    def transition_to_fullscreen(self):
        """Pass player to fullscreen view."""
        fullscreen = FullScreenView(self.player, self.vlc_instance)
        fullscreen.show()
```

### Critical Pattern: showEvent Attachment

**Problem**: Window ID not valid until widget is shown.
**Solution**: Attach player in `showEvent()`:

```python
class FullScreenView(QWidget):
    def __init__(self, player, vlc_instance):
        super().__init__()
        self.player = player
        self.vlc_instance = vlc_instance
        self.player_attached = False

    def showEvent(self, event):
        """Attach player when window is shown."""
        super().showEvent(event)
        if not self.player_attached:
            # Add small delay for window system
            QTimer.singleShot(100, self.attach_player)

    def attach_player(self):
        attach_player_to_widget(self.player, self.video_frame)
        self.player_attached = True
```

**See `FULLSCREEN_FIX_DETAILS.md` for the full fix explanation.**

### VLC Controls

```python
# Playback
self.player.play()
self.player.pause()
self.player.stop()

# Volume (0-100)
self.player.audio_set_volume(50)

# Position (0.0-1.0)
self.player.set_position(0.5)  # 50% through video

# Recording
self.player.set_record(True)  # Start recording
self.player.set_record(False)  # Stop recording
```

---

## Testing Guidelines

### Current Testing Approach

**Manual Testing** is the primary approach. No formal test framework (pytest/unittest) is currently used.

### Running Existing Tests

```bash
# Basic functionality test
python test_simple.py

# Performance benchmark
python test_optimized_loader.py
```

### Adding New Tests

**Pattern for manual tests**:

```python
import logging
from data.data_loader import DataLoader

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_channel_loading():
    """Test that channels load correctly from M3U."""
    loader = DataLoader()
    groups = loader.load_from_url("https://example.com/playlist.m3u")

    assert len(groups) > 0, "No groups loaded"
    assert all(len(g.channels) > 0 for g in groups), "Empty groups found"

    logger.info(f"✓ Loaded {len(groups)} groups successfully")

if __name__ == "__main__":
    test_channel_loading()
```

### Logging Best Practices

**Use structured logging throughout**:

```python
import logging

logger = logging.getLogger(__name__)

# At module level, configure once
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# In code
logger.debug(f"Loading profile: {profile_name}")
logger.info(f"Profile loaded successfully: {profile_name}")
logger.warning(f"Profile not found: {profile_name}")
logger.error(f"Failed to load profile: {e}")
```

### Performance Testing

**Benchmark pattern** (see `test_optimized_loader.py`):

```python
import time

def benchmark_loader(loader, url):
    start = time.time()
    groups = loader.load_from_url(url)
    elapsed = time.time() - start

    logger.info(f"Loaded {sum(len(g.channels) for g in groups)} channels in {elapsed:.2f}s")
    return elapsed
```

### Manual Testing Checklist

When making changes, manually test:

- [ ] Profile creation and deletion
- [ ] M3U playlist loading (small and large files)
- [ ] Channel playback (live streams and VOD)
- [ ] Favorites management
- [ ] History tracking
- [ ] Search functionality
- [ ] Fullscreen transitions
- [ ] Easy Mode activation
- [ ] Download/record features
- [ ] Auto-login functionality
- [ ] Cross-profile switching

---

## Common Development Tasks

### Adding a New View/Screen

1. **Create view file** in `src/view/`:
   ```python
   # src/view/my_new_screen.py
   from PyQt5.QtWidgets import QWidget
   from PyQt5.QtCore import pyqtSignal

   class MyNewScreen(QWidget):
       back_clicked = pyqtSignal()

       def __init__(self, controller):
           super().__init__()
           self.controller = controller
           self.init_ui()

       def init_ui(self):
           # Build UI here
           pass
   ```

2. **Register in IPTVApp** (`src/iptv_app.py`):
   ```python
   from view.my_new_screen import MyNewScreen

   self.my_screen = MyNewScreen(self.controller)
   self.my_screen.back_clicked.connect(self.show_previous_screen)
   ```

3. **Add transition logic**:
   ```python
   def show_my_screen(self):
       self.setCentralWidget(self.my_screen)
   ```

### Adding a New Model Field

1. **Update model** (`src/model/`):
   ```python
   @dataclass
   class Channel:
       name: str
       stream_url: str
       new_field: str = ""  # Add with default value
   ```

2. **Update serialization** (if custom):
   ```python
   def to_dict(self) -> dict:
       return {
           "name": self.name,
           "stream_url": self.stream_url,
           "new_field": self.new_field
       }
   ```

3. **Update ProfileManager** if needed for migration:
   ```python
   def _migrate_profile_data(self, profile_dict):
       if "new_field" not in profile_dict:
           profile_dict["new_field"] = ""  # Default value
       return profile_dict
   ```

### Adding a New Configuration Option

1. **Update ConfigManager** (`src/data/config_manager.py`):
   ```python
   class ConfigManager:
       DEFAULT_CONFIG = {
           # ... existing ...
           "my_new_option": False
       }

       @property
       def my_new_option(self) -> bool:
           return self.config.get("my_new_option", False)

       @my_new_option.setter
       def my_new_option(self, value: bool):
           self.config["my_new_option"] = value
           self.save()
   ```

2. **Use in application**:
   ```python
   if self.config_manager.my_new_option:
       # Do something
       pass
   ```

### Optimizing M3U Loading

If working on `data_loader.py`:

1. **Profile current performance**:
   ```python
   import cProfile
   cProfile.run('loader.load_from_url(url)', 'stats.prof')
   ```

2. **Key optimization points**:
   - Streaming parsing (64KB chunks)
   - Parallel worker threads
   - Efficient regex patterns
   - Caching to JSON

3. **Benchmark changes**:
   ```bash
   python test_optimized_loader.py
   ```

### Adding Download/Record Features

When extending `download_record_manager.py`:

1. **Emit progress signals**:
   ```python
   self.download_progress.emit(channel_name, progress_percent)
   ```

2. **Handle errors gracefully**:
   ```python
   try:
       # Download logic
       self.download_completed.emit(channel_name)
   except Exception as e:
       self.download_error.emit(channel_name, str(e))
   ```

3. **Use thread-safe operations**:
   ```python
   with self.lock:
       self.active_downloads[channel_name] = worker
   ```

---

## Git Workflow

### Branch Strategy

- **Main branch**: Stable releases
- **Feature branches**: `claude/feature-name-{session-id}`
- **Bug fix branches**: `claude/fix-description-{session-id}`

### Commit Message Format

Use conventional commit format:

```
<type>: <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `test`: Adding tests
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples**:
```
feat: add Easy Mode for elderly users

Implement simplified interface that shows only favorite channels
with large buttons and simplified navigation.

fix: resolve fullscreen black screen issue

Fix VLC player attachment timing by using showEvent() and
platform-specific window ID handling.

refactor: optimize M3U parsing with streaming approach

Improve performance by 2-5x using 64KB chunks and parallel
processing with 4 worker threads.
```

### Pre-commit Checklist

Before committing:

- [ ] Code follows PEP 8 style guide
- [ ] All imports are organized properly
- [ ] No commented-out code (unless intentional)
- [ ] Logging statements added for debugging
- [ ] Manual testing completed
- [ ] No hardcoded paths or credentials
- [ ] Documentation updated if needed

### Push Process

```bash
# Check status
git status

# Stage changes
git add src/path/to/changed/files

# Commit with descriptive message
git commit -m "feat: add new feature description"

# Push to feature branch
git push -u origin claude/feature-name-{session-id}
```

**IMPORTANT**: Always push to branches starting with `claude/` and ending with the session ID.

---

## Important Files Reference

### Critical Files (DO NOT BREAK)

| File | Purpose | Caution Level |
|------|---------|---------------|
| `src/data/data_loader.py` | M3U parsing | ⚠️ HIGH - affects all data loading |
| `src/controller/controller.py` | Central coordinator | ⚠️ HIGH - breaks entire app |
| `src/data/profile_manager.py` | Profile persistence | ⚠️ HIGH - data loss risk |
| `src/view/choose_channel_screen.py` | Main UI | ⚠️ MEDIUM - primary interface |
| `src/view/full_screen_view.py` | Video playback | ⚠️ MEDIUM - affects streaming |

### Configuration Files

| File | Purpose | Format |
|------|---------|--------|
| `requirements.txt` | Dependencies (PINNED) | Plain text |
| `profiles.json` | User profiles | JSON |
| `config.json` | App configuration | JSON |
| `.gitignore` | Git exclusions | Plain text |

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | User-facing guide |
| `OPTIMIZATION_DETAILS.md` | DataLoader optimization |
| `DOWNLOAD_RECORD_FEATURE.md` | Download/record docs |
| `FULLSCREEN_FIX_DETAILS.md` | Fullscreen fix details |
| `CLAUDE.md` | AI assistant guide (this file) |

### Test Files

| File | Purpose |
|------|---------|
| `test_simple.py` | Basic functionality tests |
| `test_optimized_loader.py` | Performance benchmarks |
| `test_sample.m3u` | Test playlist |

---

## Known Issues and Solutions

### Issue: Black Screen in Fullscreen Mode

**Status**: FIXED
**Solution**: Use `showEvent()` for player attachment with platform-specific window ID handling.
**Reference**: `FULLSCREEN_FIX_DETAILS.md`

### Issue: Slow M3U Loading

**Status**: FIXED
**Solution**: Implemented streaming parser with parallel processing.
**Performance**: 2-5x faster than traditional parsing.
**Reference**: `OPTIMIZATION_DETAILS.md`

### Issue: Duplicate Streams When Transitioning to Fullscreen

**Status**: FIXED
**Solution**: Reuse existing player instance instead of creating new one.
**Pattern**:
```python
# Pass existing player to fullscreen view
fullscreen = FullScreenView(self.player, self.vlc_instance)
```

### Common Pitfall: Thread Safety

**Problem**: Race conditions when accessing shared data.
**Solution**: Always use locks:
```python
with self.lock:
    # Access shared data here
    pass
```

### Common Pitfall: Window ID Timing

**Problem**: Widget window ID not available until shown.
**Solution**: Use `showEvent()` or `QTimer.singleShot()`:
```python
def showEvent(self, event):
    super().showEvent(event)
    QTimer.singleShot(100, self.attach_player)
```

### Common Pitfall: Large Playlist Memory

**Problem**: Loading entire M3U into memory.
**Solution**: Use streaming parser in `DataLoader`:
```python
loader.load_from_url(url)  # Uses streaming by default
```

---

## Development Best Practices

### 1. Always Use Controller

**DO**:
```python
self.controller.add_to_favorites(channel.name)
self.controller.select_profile(profile_name)
```

**DON'T**:
```python
# Direct manipulation bypasses signals and updates
self.profile.favorites.append(channel)
```

### 2. Emit Signals for UI Updates

**DO**:
```python
self.data_updated.emit()  # Let UI react to changes
```

**DON'T**:
```python
# Direct UI manipulation from controller
self.view.update_channel_list()  # Tight coupling
```

### 3. Handle All Errors

**DO**:
```python
try:
    result = operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    self.error_occurred.emit(str(e))
```

**DON'T**:
```python
result = operation()  # Unhandled exception crashes app
```

### 4. Log Extensively

**DO**:
```python
logger.debug(f"Starting operation with {param}")
result = operation(param)
logger.info(f"Operation completed: {result}")
```

**DON'T**:
```python
result = operation(param)  # Silent operation, hard to debug
```

### 5. Use Type Hints

**DO**:
```python
def process_channel(self, channel: Channel) -> bool:
    """Process a channel and return success status."""
    pass
```

**DON'T**:
```python
def process_channel(self, channel):  # Unclear what type expected
    pass
```

### 6. Keep UI Responsive

**DO**:
```python
worker = LoaderWorker(controller)
thread = QThread()
worker.moveToThread(thread)
thread.start()
```

**DON'T**:
```python
# Long operation on main thread freezes UI
groups = loader.load_from_url(url)
```

### 7. Atomic File Operations

**DO**:
```python
# Write to temp file, then atomic replace
with tempfile.NamedTemporaryFile('w', delete=False) as tmp:
    json.dump(data, tmp)
os.replace(tmp.name, target_path)
```

**DON'T**:
```python
# Direct write can corrupt on failure
with open(target_path, 'w') as f:
    json.dump(data, f)
```

---

## Quick Reference

### Import Paths

```python
# Controller
from controller.controller import Controller

# Models
from model.profile import Profile
from model.channel_model import Channel
from model.group_model import Group

# Data layer
from data.profile_manager import ProfileManager
from data.data_loader import DataLoader
from data.config_manager import ConfigManager
from data.recorder import Recorder
from data.downloader import Downloader

# Services
from services.download_record_manager import DownloadRecordManager

# Views
from view.login_view import LoginScreen
from view.choose_channel_screen import ChooseChannelScreen
from view.full_screen_view import FullScreenView
from view.easy_mode_screen import EasyModeScreen
```

### Common PyQt5 Imports

```python
from PyQt5.QtWidgets import (
    QApplication, QWidget, QMainWindow,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QListWidget, QComboBox, QCheckBox,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QMessageBox, QDialog, QFileDialog,
    QScrollArea, QSplitter, QFrame
)
from PyQt5.QtCore import (
    Qt, QObject, QThread, QTimer,
    pyqtSignal, pyqtSlot
)
from PyQt5.QtGui import (
    QFont, QIcon, QPixmap,
    QKeySequence, QCursor
)
```

### Useful Commands

```bash
# Run application
cd src && python iptv_app.py

# Run tests
python test_simple.py
python test_optimized_loader.py

# Check code style
flake8 src/

# Format code
black src/

# Check dependencies
pip list
pip freeze > requirements.txt
```

---

## Additional Resources

### External Documentation

- **PyQt5 Docs**: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **python-vlc Docs**: https://www.olivieraubert.net/vlc/python-ctypes/doc/
- **M3U Format**: https://en.wikipedia.org/wiki/M3U

### Internal Documentation

- See `OPTIMIZATION_DETAILS.md` for performance optimization techniques
- See `DOWNLOAD_RECORD_FEATURE.md` for download/record implementation
- See `FULLSCREEN_FIX_DETAILS.md` for VLC player attachment details
- See `README.md` for user-facing features and usage

---

## Updating This Document

**When to update CLAUDE.md**:

1. New architecture patterns introduced
2. New major features added
3. Critical bugs fixed with lessons learned
4. Development workflows change
5. New dependencies added
6. Testing approach evolves

**How to update**:

1. Keep sections organized and scannable
2. Add examples for new patterns
3. Update version number at top
4. Update "Last Updated" date
5. Keep tone professional and concise
6. Test code examples before adding

---

**End of CLAUDE.md**

*This document is maintained for AI assistants working on IPTV-Saba. For user-facing documentation, see README.md.*
