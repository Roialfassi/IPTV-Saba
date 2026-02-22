# CLAUDE.md - AI Assistant Guide for IPTV-Saba

**Last Updated**: 2026-02-22
**Version**: 2.0.0

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
10. [Scheduling System](#scheduling-system)
11. [Stream Health and Reliability](#stream-health-and-reliability)
12. [Testing Guidelines](#testing-guidelines)
13. [Common Development Tasks](#common-development-tasks)
14. [Build and Distribution](#build-and-distribution)
15. [Git Workflow](#git-workflow)
16. [Important Files Reference](#important-files-reference)
17. [Known Issues and Solutions](#known-issues-and-solutions)

---

## Project Overview

**IPTV-Saba** is a desktop IPTV streaming application built with Python and PyQt5, featuring profile management, channel favorites, scheduled recordings, stream health tracking, and a simplified "Easy Mode" for elderly users.

### Key Features
- Multiple user profiles with separate M3U playlists
- Channel browsing with categories and search
- Favorites and watch history tracking
- Full-screen video playback with VLC via SharedPlayerManager (singleton)
- Easy Mode (simplified UI for elderly users)
- Download and record streaming content
- **Scheduled recordings** with conflict detection
- **Stream health tracking** with automatic retry on failure
- **HLS quality selection** (auto-detected from master playlists)
- **Audio track and subtitle selection** (including external subtitle loading)
- **Auto-login** with remembering the last active profile
- **PyInstaller build** for standalone Windows EXE distribution

### Technology Stack
- **Language**: Python 3.8+
- **UI Framework**: PyQt5 (5.15.11)
- **Video Playback**: python-vlc (3.0.21203)
- **Data Format**: JSON for all persistence
- **Networking**: requests (HTTP), chardet (encoding detection)
- **Search**: fuzzywuzzy + rapidfuzz + python-Levenshtein (fuzzy matching)
- **Architecture**: MVC (Model-View-Controller) + Service Layer
- **Build Tool**: PyInstaller (via `build.bat` and `iptv_saba.spec`)
- **Recording Backend**: VLC sout for live streams, ffmpeg for scheduled recordings

### Target Platforms
- Windows (primary, with specific VLC crash workarounds)
- Linux (supported)
- macOS (supported)

---

## Architecture

### MVC Pattern + Service Layer

The application follows a clean MVC architecture with an additional service layer for cross-cutting concerns:

```
+---------------------------------------------------------+
|                    IPTVApp (Main)                        |
|  - Application entry point and lifecycle manager        |
|  - Screen transition orchestration                      |
|  - Cleanup via aboutToQuit signal                       |
+--------------------------+------------------------------+
                           |
                           v
+---------------------------------------------------------+
|                   Controller Layer                       |
|  - Central coordinator (controller.py)                  |
|  - Signal/slot event handling                           |
|  - Business logic orchestration                         |
+---------+-----------+-----------+-----------------------+
          |           |           |
          v           v           v
+----------+  +----------+  +--------------+
|  Model   |  |   View   |  |  Data Layer  |
|  Layer   |  |  Layer   |  |              |
+----------+  +----------+  +--------------+
                    |
                    v
+---------------------------------------------------------+
|                   Service Layer                          |
|  - SharedPlayerManager (singleton VLC player)           |
|  - DownloadRecordManager (concurrent downloads/records) |
|  - StreamHealthTracker (failure tracking)               |
|  - RecordingScheduler (QTimer-based auto-recording)     |
|  - ScheduleManager (schedule persistence)               |
|  - HLSParser (quality variant extraction)               |
+---------------------------------------------------------+
```

### Component Relationships

```
IPTVApp
+-- Controller
|   +-- ProfileManager          # Profile CRUD operations (thread-safe)
|   +-- DataLoader              # M3U playlist parsing (streaming + parallel)
|   +-- ConfigManager           # App configuration persistence
|
+-- LoginScreen                 # Profile selection + create/delete
|   +-- CreateProfileDialog     # New profile dialog
|
+-- ChooseChannelScreen         # Main channel browser
|   +-- SharedPlayerManager     # Singleton VLC player (embedded view)
|   +-- DownloadRecordManager   # Downloads and recordings
|   +-- ScheduleManager         # Schedule persistence
|   +-- RecordingScheduler      # Automatic scheduled recordings
|   +-- LoaderWorker            # Background data loading (QThread)
|   +-- LoadingOverlay          # Animated loading indicator
|   +-- RetryOverlay            # Reconnection status overlay
|   +-- ScheduleRecordingDialog # Schedule creation dialog
|   +-- FullScreenView          # Fullscreen player (transition via SharedPlayerManager)
|
+-- EasyModeScreen              # Simplified UI (own VLC instance, NOT SharedPlayerManager)

Model
+-- Profile                     # User profile entity (custom __init__)
+-- Channel                     # Channel entity (@dataclass)
+-- Group                       # Channel group entity (@dataclass)
+-- ScheduledRecording          # Scheduled recording entity (@dataclass)
+-- RecordingStatus             # Enum: PENDING, RECORDING, COMPLETED, FAILED, CANCELLED
```

### Design Patterns Used

1. **MVC Pattern**: Separation of concerns across model/view/controller
2. **Observer Pattern**: PyQt5 signals/slots for event-driven communication
3. **Singleton Pattern**: `SharedPlayerManager`, `StreamHealthTracker` (thread-safe `__new__`)
4. **Repository Pattern**: `ProfileManager`, `DataLoader`, `ScheduleManager` abstract data access
5. **Worker Thread Pattern**: `LoaderWorker` with `QThread` for background data loading
6. **State Machine Pattern**: `PlayerViewState` (IDLE -> EMBEDDED -> TRANSITIONING -> FULLSCREEN)
7. **Strategy Pattern**: `DataLoader` supports optimized streaming or traditional parsing

---

## Directory Structure

```
IPTV-APP-V2/
|
+-- src/                          # Main source code
|   +-- __init__.py
|   +-- iptv_app.py              # Application entry point (MAIN)
|   |
|   +-- controller/              # Controller layer
|   |   +-- __init__.py
|   |   +-- controller.py        # Central application controller
|   |
|   +-- model/                   # Data models
|   |   +-- __init__.py
|   |   +-- channel_model.py    # Channel entity (@dataclass)
|   |   +-- group_model.py      # Channel group entity (@dataclass)
|   |   +-- profile.py          # User profile entity (custom __init__)
|   |   +-- scheduled_recording.py  # Scheduled recording model + RecordingStatus enum
|   |
|   +-- view/                    # UI layer (PyQt5)
|   |   +-- __init__.py
|   |   +-- login_view.py       # Profile selection screen + CreateProfileDialog
|   |   +-- choose_channel_screen.py  # Main channel browser + LoaderWorker + LoadingOverlay
|   |   +-- full_screen_view.py # Fullscreen player with auto-hiding controls
|   |   +-- easy_mode_screen.py # Simplified UI for elderly users
|   |   +-- ccs_v2.py           # Additional view components
|   |   +-- retry_overlay.py    # Stream retry status overlay (animated)
|   |   +-- schedule_dialog.py  # Schedule recording dialog (QDialog)
|   |
|   +-- data/                    # Data access layer
|   |   +-- __init__.py
|   |   +-- config_manager.py   # Application configuration (JSON persistence)
|   |   +-- data_loader.py      # M3U playlist parser (streaming + parallel, CRITICAL)
|   |   +-- profile_manager.py  # Profile CRUD operations (thread-safe, atomic writes)
|   |   +-- recorder.py         # ffmpeg-based stream recording (CLI + GUI test)
|   |   +-- downloader.py       # Simple MP4 downloader (tqdm progress)
|   |
|   +-- services/                # Business logic services
|   |   +-- __init__.py
|   |   +-- shared_player_manager.py  # Singleton VLC player + state machine (CRITICAL)
|   |   +-- download_record_manager.py  # Concurrent download/record orchestration
|   |   +-- stream_health_tracker.py   # Channel failure tracking (singleton)
|   |   +-- hls_parser.py       # HLS master playlist parser (quality variants)
|   |   +-- schedule_manager.py # Scheduled recording persistence (JSON)
|   |   +-- recording_scheduler.py  # QTimer-based auto-recording scheduler
|   |
|   +-- utils/                   # Utility modules
|   |   +-- __init__.py
|   |   +-- resource_path.py    # PyInstaller resource path helper
|   |
|   +-- Assets/                  # Application resources
|       +-- iptv-logo2.ico      # Application icon
|
+-- docs/                        # Documentation directory
|   +-- API_REFERENCE.md
|   +-- ARCHITECTURE.md
|   +-- CODE_REVIEW_SUGGESTIONS.md
|   +-- CONTRIBUTING.md
|   +-- DEVELOPMENT_SETUP.md
|   +-- README.md
|   +-- USER_GUIDE.md
|
+-- build.bat                    # Windows build script (PyInstaller)
+-- requirements.txt             # Python dependencies (PINNED VERSIONS)
+-- test_simple.py              # Basic functionality tests
+-- test_optimized_loader.py    # Performance benchmarks
+-- .gitignore                  # Git exclusions
+-- CLAUDE.md                   # This file - AI assistant guide
```

### Runtime Data Storage

**Runtime data directory**: `{cwd}/IPTV-Saba/` (created automatically)

```
IPTV-Saba/
+-- profiles.json               # User profiles with favorites/history
+-- config.json                 # App configuration
+-- schedules.json              # Scheduled recordings
+-- {profile_name}data.json     # Cached channel data (24h TTL)
+-- downloads/                  # Downloaded/recorded media
```

---

## Development Setup

### Prerequisites

1. **Python 3.8+** installed
2. **VLC Media Player** installed on the system (required for python-vlc)
   - Windows: `C:\Program Files\VideoLAN\VLC\` (plugins path hardcoded in SharedPlayerManager)
3. **ffmpeg** on PATH (required for `recorder.py` scheduled recording feature)
4. **pip** for package management

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/Roialfassi/IPTV-Saba.git
cd IPTV-APP-V2

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PyQt5 | 5.15.11 | UI framework |
| python-vlc | 3.0.21203 | VLC media player bindings |
| requests | 2.32.3 | HTTP client |
| chardet | 5.2.0 | Encoding detection for M3U files |
| fuzzywuzzy | 0.18.0 | Fuzzy string matching |
| rapidfuzz | 3.9.7 | Fast fuzzy matching |
| python-Levenshtein | 0.25.1 | Levenshtein distance for fuzzy search |
| tqdm | (via pip) | Progress bars (downloader.py) |

### Running the Application

```bash
# From the project root
cd src
python iptv_app.py
```

**Important**: The application uses `src.` prefixed imports (e.g., `from src.controller.controller import Controller`), so running from within `src/` requires the parent directory to be on the Python path, or the app must be run as a module.

### Running as a Module (recommended)

```bash
# From the project root directory
python -m src.iptv_app
```

---

## Key Components

### 1. IPTVApp (`src/iptv_app.py`)

**Purpose**: Application entry point, lifecycle manager, and screen transition coordinator.

**Key Responsibilities**:
- Create `QApplication` and `Controller`
- Handle screen transitions (Login -> ChooseChannel, Login -> EasyMode)
- Manage auto-login flow via `controller.login_logic()`
- First-run setup (create mock profile)
- Application cleanup via `aboutToQuit` signal

**Screen Transitions**:
```
LoginScreen ---------> ChooseChannelScreen
    |                       |
    +-- easy_mode -----> EasyModeScreen
    |
    +-- auto_login ----> ChooseChannelScreen (skip login)
```

**Cleanup Order** (in `cleanup()` method):
1. `ChooseChannelScreen._perform_full_cleanup()`
2. EasyModeScreen player pause + release
3. `SharedPlayerManager.reset_instance()`

**Windows VLC Crash Prevention**: The cleanup method uses pause-first approach instead of `stop()` to avoid VLC access violations on Windows.

### 2. Controller (`src/controller/controller.py`)

**Purpose**: Central coordinator for application logic and state management.

**Key State**:
- `active_profile: Optional[Profile]` - Currently logged-in profile
- `config_dir: str` - Path to `IPTV-Saba/` data directory
- `profile_manager: ProfileManager` - Profile CRUD
- `data_loader: DataLoader` - M3U parser
- `config_manager: ConfigManager` - App settings

**Signals**:
- `profiles_updated` - Emitted when profile list changes
- `error_occurred(str)` - Emitted on errors
- `profile_selected(str)` - Emitted when a profile is activated
- `data_loaded(dict)` - Emitted when channel data finishes loading

**Key Methods**:
```python
login_logic() -> bool                  # Check auto-login, load profile
select_profile(name: str)              # Activate a profile
create_profile(name: str, url: str)    # Create new profile
delete_profile(name: str)              # Remove profile
add_to_favorites(channel_name: str)    # Add channel to favorites
remove_from_favorites(channel_name: str)  # Remove from favorites
add_to_history(channel: Channel)       # Track watch history
search_channels(query: str) -> List[Channel]  # Search channels
find_channel_by_name(name: str) -> Optional[Channel]  # Exact lookup
list_groups() -> List[str]             # List all group names
list_channels_in_group(name: str) -> List[str]  # Channels in group
```

### 3. SharedPlayerManager (`src/services/shared_player_manager.py`)

**Purpose**: Singleton VLC player manager enabling seamless transitions between embedded and fullscreen views without playback interruption.

**This is the most critical service component.** All VLC playback in the main app (except EasyMode) goes through this singleton.

**Singleton Access**:
```python
from src.services.shared_player_manager import get_shared_player, SharedPlayerManager

player_manager = get_shared_player()
# or
player_manager = SharedPlayerManager.get_instance()
```

**State Machine** (`PlayerViewState`):
```
IDLE ---play_channel()--> EMBEDDED
EMBEDDED ---transition_to_fullscreen()--> TRANSITIONING --> FULLSCREEN
FULLSCREEN ---transition_to_embedded()--> TRANSITIONING --> EMBEDDED
Any ---stop()--> IDLE
```

**Key Signals**:
```python
state_changed(object)               # PlayerViewState
channel_changed(object)             # Channel or None
playback_started()
playback_stopped()
error_occurred(str)
stream_error(str)                   # VLC stream errors
connection_timeout(str)             # Stream failed to connect (15s timeout)
buffering(int)                      # Buffering percentage (0-100)
audio_tracks_available(list)        # List of (id, name) tuples
subtitles_available(list)           # List of (id, name) tuples
retry_started(str, int, int)        # channel_name, attempt, max_attempts
retry_exhausted(str)                # All retries failed
quality_variants_available(list)    # List of QualityVariant objects
```

**Auto-Retry on Failure**:
- Max 3 retry attempts with exponential backoff (2s, 4s, 8s)
- Triggered on VLC errors and connection timeouts
- Can be cancelled via `cancel_retry()` or new channel selection
- Integrates with `StreamHealthTracker` for failure tracking

**HLS Quality Selection**:
- Automatically parses HLS master playlists after playback starts
- Exposes quality variants via `quality_variants_available` signal
- `set_quality(index)` switches streams while maintaining playback state

**Audio/Subtitle Support**:
- `get_audio_tracks()` / `set_audio_track(id)` - Switch audio track
- `get_subtitle_tracks()` / `set_subtitle_track(id)` - Switch subtitles
- `load_external_subtitle(path)` - Load .srt/.sub/.ass files

**Windows-Specific Workarounds**:
- VLC plugins path hardcoded: `C:\Program Files\VideoLAN\VLC\plugins`
- `stop()` uses pause-first approach, avoids calling VLC `stop()` on Windows
- `safe_stop_for_cleanup()` only pauses (never stops) to prevent crashes
- `cleanup()` detaches from window before releasing resources

### 4. DataLoader (`src/data/data_loader.py`)

**Purpose**: Parse M3U playlists efficiently with optimization for large files.

**Key Features**:
- **Streaming parser**: Downloads and parses in parallel 64KB chunks
- **4 worker threads** for channel object creation
- **Encoding detection** via chardet
- **String interning** for memory optimization on repeated group names
- **O(1) channel lookup** via `_channel_index` dict
- **Stream type detection**: Classifies channels as LIVE/VOD/SERIES/UNKNOWN
- **Retry logic**: Exponential backoff (3 retries, 1s initial delay)
- **Progress callbacks** for UI reporting
- **JSON caching** with 24h TTL

**Custom Exceptions**:
- `DataLoader.ParseError` - M3U parsing errors (with line number context)
- `DataLoader.SourceError` - Source retrieval errors (HTTP status codes)
- `DataLoader.NetworkError` - Network errors (with retry count)

**Important Methods**:
```python
load(source: str, use_optimized=True, progress_callback=None) -> bool
save_to_json(file_path: str) -> bool
load_from_json(file_path: str) -> bool
get_channel_by_name(name: str) -> Optional[Channel]  # O(1) lookup
get_group(name: str) -> Optional[Group]
search_channels(pattern, search_fields=None) -> List[Channel]
get_channels_by_type(stream_type: StreamType) -> List[Channel]
get_statistics() -> Dict[str, Any]
```

**Stream Types** (`StreamType` enum):
- `LIVE` - Live TV streams (.m3u8, .ts)
- `VOD` - Video on demand (.mp4, .mkv, etc.)
- `SERIES` - TV series (detected via S01E01 patterns)
- `UNKNOWN` - Unclassifiable

### 5. ProfileManager (`src/data/profile_manager.py`)

**Purpose**: Thread-safe profile management with atomic persistence.

**Thread Safety**: Uses `threading.RLock` for all operations. Dual data structures (dict for O(1) lookup, list for ordered iteration).

**Atomic Writes**: Writes to `.tmp` file first, then `os.replace()` for atomic swap. Rollback on save failure.

**Key Methods**:
```python
create_profile(name, url, favorites=None) -> Optional[Profile]
update_profile(updated_profile: Profile) -> bool
get_profile(name: str) -> Optional[Profile]
delete_profile(name: str) -> bool
list_profiles() -> List[str]
export_profiles(file_path: str) -> bool
import_profiles(file_path: str, overwrite=False) -> Tuple[int, int, int]
find_profiles(name=None, url=None) -> List[Profile]
```

### 6. ConfigManager (`src/data/config_manager.py`)

**Purpose**: Manage application-wide configuration with auto-save.

**Default Configuration**:
```python
DEFAULT_CONFIG = {
    "last_active_profile_id": None,
    "auto_login_enabled": False,
    "theme": "default",
    "app_version": "1.0.0",
    "first_run": True,
    "log_level": "INFO",
    "preferred_audio_language": "",
    "subtitles_enabled": False,
    "preferred_subtitle_language": "",
    "preferred_quality": "auto"
}
```

**Properties** (auto-save on set):
- `last_active_profile_id` / `auto_login_enabled` / `theme`
- `preferred_audio_language` / `subtitles_enabled` / `preferred_subtitle_language`
- `preferred_quality`

**Generic Access**:
```python
config.get_value("key", default=None)
config.set_value("key", value)
config.should_auto_login() -> Tuple[bool, Optional[str]]
config.reset_to_defaults()
```

### 7. DownloadRecordManager (`src/services/download_record_manager.py`)

**Purpose**: Manage concurrent downloads and recordings with progress tracking.

**Downloads**: Use `requests` streaming with 64KB chunks, cancellable via `cancelled_downloads` set.

**Recordings**: Use VLC's `sout` option to record live streams to file. Each recording gets its own `vlc.Instance`.

**Signals**:
```python
download_progress(str, int, int)    # id, bytes_downloaded, total_bytes
download_complete(str, str)         # id, file_path
download_error(str, str)            # id, error_message
recording_started(str)              # id
recording_stopped(str, str)         # id, file_path
```

**Key Methods**:
```python
start_download(id, channel_name, url) -> bool
start_recording(id, channel_name, url) -> bool
stop_recording(id, blocking=False) -> bool
cancel_download(id) -> bool
cleanup_all(blocking=True)
is_media_file(url) -> bool  # Check if URL is downloadable vs live stream
generate_filename(name, url, is_recording=False) -> str
```

### 8. StreamHealthTracker (`src/services/stream_health_tracker.py`)

**Purpose**: Track problematic channels and failure patterns across the application.

**Singleton** (thread-safe via `RLock`).

**A channel is "problematic" if**:
- 3+ consecutive failures, OR
- Failure rate > 50% with at least 5 attempts

**Key Methods**:
```python
record_failure(channel_name: str)
record_success(channel_name: str)
is_problematic(channel_name: str) -> bool
get_consecutive_failures(channel_name: str) -> int
get_health(channel_name: str) -> Optional[ChannelHealth]
get_problematic_channels() -> list
reset_channel(channel_name: str)
clear_all()
```

### 9. HLSParser (`src/services/hls_parser.py`)

**Purpose**: Parse HLS master playlists to extract quality variants.

**`QualityVariant` dataclass**:
```python
@dataclass
class QualityVariant:
    resolution: str      # e.g., "1920x1080"
    bandwidth: int       # bits per second
    url: str             # URL to variant playlist
    name: str            # e.g., "1080p HD"
    codecs: str = ""     # Optional codec info
```

**Quality names auto-generated**: 4K UHD, 1440p QHD, 1080p HD, 720p HD, 480p SD, 360p, or bandwidth-based fallback.

### 10. Recording Scheduler System

**Three components work together**:

1. **`ScheduledRecording`** (`src/model/scheduled_recording.py`) - Data model with UUID-based ID, start/end times, status tracking, duration helpers, and `should_start_now`/`should_stop_now` properties.

2. **`ScheduleManager`** (`src/services/schedule_manager.py`) - JSON persistence layer with conflict detection (overlapping time ranges). Thread-safe with `RLock`.

3. **`RecordingScheduler`** (`src/services/recording_scheduler.py`) - QTimer-based scheduler that checks every 30 seconds for schedules that need starting/stopping. Integrates with `DownloadRecordManager` for actual recording.

**Workflow**:
```
User creates schedule via ScheduleRecordingDialog
  -> ScheduleManager.add_schedule() (with conflict check)
  -> RecordingScheduler._check_schedules() (every 30s)
  -> RecordingScheduler._start_recording() triggers DownloadRecordManager
  -> QTimer set for auto-stop at end_time
  -> RecordingScheduler._stop_recording() on completion
```

---

## Coding Conventions

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Classes | PascalCase | `ProfileManager`, `SharedPlayerManager` |
| Functions/Methods | snake_case | `load_profiles()`, `add_to_favorites()` |
| Constants | UPPER_SNAKE_CASE | `MEDIA_EXTENSIONS`, `CONNECTION_TIMEOUT` |
| Private methods | Leading underscore | `_parse_extinf()`, `_attach_to_frame()` |
| PyQt5 Signals | Descriptive names | `profiles_updated`, `stream_error`, `retry_started` |
| Module files | snake_case | `shared_player_manager.py`, `stream_health_tracker.py` |
| Enums | PascalCase class, UPPER values | `RecordingStatus.PENDING`, `StreamType.LIVE` |

### Import Style

All source imports use absolute `src.` prefix:
```python
# Standard library
import os
import logging
from typing import List, Optional

# Third-party
from PyQt5.QtCore import QObject, pyqtSignal
import vlc

# Local (always use src. prefix)
from src.controller.controller import Controller
from src.model.channel_model import Channel
from src.services.shared_player_manager import get_shared_player
```

### Code Style

**Follow PEP 8** with these specifics:

1. **Indentation**: 4 spaces (no tabs)
2. **Line Length**: Aim for 79 characters, max ~100 for readability
3. **Docstrings**: Triple quotes, describe Args and Returns
4. **Type Hints**: Used for method signatures throughout
5. **Error Handling**: Always log errors and emit signals where applicable
6. **Logging**: `logging.basicConfig(level=logging.DEBUG)` at module level, `logger = logging.getLogger(__name__)`

### PyQt5 Patterns

**Signal/Slot Declaration**:
```python
class MyComponent(QObject):
    data_ready = pyqtSignal()
    error_occurred = pyqtSignal(str)

    @pyqtSlot(str)
    def on_action(self, data: str):
        self.data_ready.emit()
```

**Worker Thread Pattern** (used in `LoaderWorker`):
```python
class Worker(QObject):
    finished = pyqtSignal()
    data_loaded = pyqtSignal(object)
    error = pyqtSignal(str)

    def run(self):
        try:
            result = heavy_work()
            self.data_loaded.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        self.finished.emit()

# Usage in view:
worker = LoaderWorker(controller)
thread = QThread()
worker.moveToThread(thread)
thread.started.connect(worker.run)
worker.finished.connect(thread.quit)
thread.start()
```

### Dataclass Usage

Use `@dataclass` for simple data models:
```python
@dataclass
class Channel:
    name: str
    stream_url: str
    tvg_id: str = ""
    tvg_logo: str = ""
    channel_type: str = ""
```

**When NOT to use `@dataclass` with default `__init__`**: When complex initialization logic is needed (like `Profile`, which has a custom `__init__` despite `@dataclass` decorator).

---

## Data Management

### Data Storage Format

**All data stored as JSON** in `IPTV-Saba/` directory (relative to cwd).

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
        "channel_type": "live"
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
  "log_level": "INFO",
  "preferred_audio_language": "",
  "subtitles_enabled": false,
  "preferred_subtitle_language": "",
  "preferred_quality": "auto"
}
```

#### schedules.json Structure
```json
[
  {
    "id": "a1b2c3d4",
    "channel_name": "CNN",
    "stream_url": "http://stream.url",
    "start_time": "2026-02-22T20:00:00",
    "end_time": "2026-02-22T21:00:00",
    "status": "pending",
    "created_at": "2026-02-22T19:00:00",
    "output_path": null,
    "error_message": null
  }
]
```

#### Cached Channel Data ({profile}data.json)
```json
{
  "groups": [
    {
      "name": "News",
      "channels": [
        {
          "name": "CNN",
          "stream_url": "http://...",
          "tvg_id": "cnn.us",
          "tvg_logo": "http://...",
          "channel_type": "live"
        }
      ]
    }
  ],
  "default_group_name": "Ungrouped",
  "version": "2.0",
  "statistics": { ... }
}
```

### Data Persistence Strategy

| Data | Storage | Cache | Thread Safety |
|------|---------|-------|--------------|
| Profiles | JSON file (atomic writes) | In-memory dict + list | `RLock` |
| Channels | JSON cache (24h TTL) | In-memory dict | Worker thread |
| Config | JSON file (immediate save) | In-memory dict | Single-threaded |
| Schedules | JSON file | In-memory list | `RLock` |
| Downloads | Stream to disk | N/A | Per-thread |
| Health data | In-memory only | N/A | `RLock` |

### Atomic File Operations

**Pattern used throughout** (ProfileManager, ScheduleManager):
```python
def save(self, data, file_path):
    tmp_path = file_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=4)
    os.replace(tmp_path, file_path)  # Atomic on most filesystems
```

---

## UI Framework and Patterns

### Styling Guidelines

**Color Palette** (Netflix-inspired):
| Color | Hex | Usage |
|-------|-----|-------|
| Primary Red | `#E50914` | Buttons, accents, branding |
| Hover Red | `#FF0909` / `#F6121D` | Button hover state |
| Pressed Red | `#BF0811` / `#b00710` | Button pressed state |
| Dark Background | `#141414` / `#1a1a1a` | Main backgrounds |
| Secondary Dark | `#222222` / `#2c2c2c` | Input backgrounds |
| Facebook Blue | `#1877F2` | Secondary actions |
| Text White | `#FFFFFF` | Primary text |
| Text Gray | `#AAAAAA` / `#888` | Secondary text |

### Key UI Components

**LoadingOverlay** (in `choose_channel_screen.py`):
- Unicode spinner animation (`SPINNER_CHARS` cycling at 80ms)
- Semi-transparent dark background
- Progress message text

**RetryOverlay** (`retry_overlay.py`):
- Fade-in/fade-out animations (`QGraphicsOpacityEffect` + `QPropertyAnimation`)
- Indeterminate progress bar
- Attempt counter ("Attempt 2 of 3")
- Cancel button

**ScheduleRecordingDialog** (`schedule_dialog.py`):
- `QDateTimeEdit` with calendar popup for start/end time
- Duration validation (1 min to 24 hours)
- Live duration display

### Auto-hiding Controls (FullScreenView)

```python
# Controls appear on mouse movement, hide after delay
def mouseMoveEvent(self, event):
    self.show_controls()
    self.hide_timer.start(HIDE_CONTROLS_MOUSE_DELAY_MS)  # 5000ms

def show_controls(self):
    self.controls_widget.show()

def hide_controls(self):
    self.controls_widget.hide()
```

---

## Video Playback

### SharedPlayerManager Architecture

**All video playback in the main app flow** (ChooseChannelScreen + FullScreenView) goes through the `SharedPlayerManager` singleton. This ensures:
- No dual streams
- Seamless fullscreen transitions
- Centralized error handling and retry logic
- Consistent audio/subtitle/quality management

**Exception**: `EasyModeScreen` creates its own `vlc.Instance()` and `media_player_new()` independently.

### View Transition Flow

```
1. User clicks fullscreen button in ChooseChannelScreen
2. ChooseChannelScreen calls SharedPlayerManager.transition_to_fullscreen(frame)
3. SharedPlayerManager:
   a. Saves playback state (URL, position, playing status)
   b. Sets state to TRANSITIONING
   c. Stops VLC player
   d. QTimer.singleShot(100ms) -> complete transition
4. After 100ms delay:
   a. Attaches player to fullscreen frame (platform-specific window ID)
   b. Creates new media, starts playback
   c. Restores position
   d. Sets state to FULLSCREEN
```

### Platform-Specific Window Attachment

```python
def _attach_to_frame(self, frame: QWidget) -> bool:
    win_id = int(frame.winId())
    if sys.platform.startswith('linux'):
        self._player.set_xwindow(win_id)
    elif sys.platform == "win32":
        self._player.set_hwnd(win_id)
    elif sys.platform == "darwin":
        self._player.set_nsobject(win_id)
```

### VLC Event Handling

SharedPlayerManager registers callbacks for:
- `MediaPlayerPlaying` -> Cancel retry, record success in health tracker, emit audio/subtitle tracks
- `MediaPlayerEncounteredError` -> Record failure, trigger retry
- `MediaPlayerBuffering` -> Emit buffering percentage
- `MediaPlayerOpening` -> Start connection timeout timer (15s)
- `MediaPlayerEndReached` -> Stream ended
- `MediaPlayerStopped` / `MediaPlayerPaused` -> State tracking

### Critical Windows VLC Workarounds

1. **Never call `player.stop()` during cleanup** - Use `player.set_pause(1)` then `player.set_media(None)`
2. **Detach from window before release** - `player.set_hwnd(None)` before `player.release()`
3. **VLC plugins path must be specified** on Windows: `--plugin-path=C:\Program Files\VideoLAN\VLC\plugins`
4. **`safe_stop_for_cleanup()`** is specifically designed for logout/cleanup scenarios where we need to avoid crashes

---

## Scheduling System

### Creating a Scheduled Recording

```python
# Via the dialog (from ChooseChannelScreen)
schedule = ScheduleRecordingDialog.create_schedule(channel, parent=self)
if schedule:
    schedule_manager.add_schedule(schedule)  # Checks for conflicts
```

### Conflict Detection

The `ScheduleManager` checks for time overlaps between new and existing pending/active schedules:
```python
def _times_overlap(start1, end1, start2, end2) -> bool:
    return start1 < end2 and start2 < end1
```

### Recording Status Lifecycle

```
PENDING -> RECORDING -> COMPLETED
                    |-> FAILED
           |-> CANCELLED
PENDING -> CANCELLED
```

### Cleanup

`ScheduleManager.cleanup_old_schedules(days=7)` removes finished schedules older than the specified number of days.

---

## Stream Health and Reliability

### Health Tracking Flow

```
Channel played -> SharedPlayerManager._on_playing
  -> StreamHealthTracker.record_success(channel_name)
  -> Resets consecutive_failures to 0

Channel fails -> SharedPlayerManager._on_error / _on_connection_timeout
  -> StreamHealthTracker.record_failure(channel_name)
  -> Increments failure_count and consecutive_failures
  -> If retry_enabled and attempts < 3: schedule retry
  -> If exhausted: emit retry_exhausted signal
```

### Retry Configuration

| Setting | Value |
|---------|-------|
| Max attempts | 3 |
| Delay sequence | 2s, 4s, 8s (exponential backoff) |
| Connection timeout | 15 seconds |

### UI Integration

- `RetryOverlay` shows "Reconnecting..." with attempt counter
- Cancel button aborts retry sequence
- `retry_exhausted` signal triggers user-facing error message

---

## Testing Guidelines

### Current Testing Approach

**Manual Testing** is the primary approach. No formal test framework (pytest/unittest) is currently configured.

### Running Existing Tests

```bash
# Basic functionality test
python test_simple.py

# Performance benchmark
python test_optimized_loader.py
```

### Manual Testing Checklist

When making changes, manually test:

- [ ] Profile creation and deletion
- [ ] M3U playlist loading (small and large files)
- [ ] Channel playback (live streams and VOD)
- [ ] Favorites management (add/remove)
- [ ] History tracking
- [ ] Search functionality
- [ ] Fullscreen transitions (enter and exit)
- [ ] Easy Mode activation and channel navigation
- [ ] Download/record features
- [ ] Auto-login functionality
- [ ] Cross-profile switching (logout -> switch -> login)
- [ ] Stream retry on failure (disconnect internet, reconnect)
- [ ] Audio track switching (multi-language streams)
- [ ] Subtitle enabling/disabling
- [ ] Quality selection (HLS streams with variants)
- [ ] Schedule recording dialog (create, validate, conflict check)
- [ ] Application cleanup (close app while playing, no crashes)

---

## Common Development Tasks

### Adding a New View/Screen

1. **Create view file** in `src/view/`:
   ```python
   from PyQt5.QtWidgets import QWidget
   from PyQt5.QtCore import pyqtSignal
   from src.utils.resource_path import resource_path

   WINDOW_ICON_PATH = resource_path("Assets/iptv-logo2.ico")

   class MyNewScreen(QWidget):
       back_clicked = pyqtSignal()

       def __init__(self, controller):
           super().__init__()
           self.controller = controller
           self.init_ui()
   ```

2. **Register in IPTVApp** (`src/iptv_app.py`):
   ```python
   from src.view.my_new_screen import MyNewScreen
   ```

3. **Add transition logic** and cleanup handling.

### Adding a New Service

1. **Create service file** in `src/services/`
2. **Follow singleton pattern** if needed (see `SharedPlayerManager` or `StreamHealthTracker`)
3. **Use thread-safe data structures** (`RLock`) if accessed from multiple threads
4. **Emit signals** for UI communication
5. **Integrate cleanup** in `IPTVApp.cleanup()` if the service holds resources

### Adding a New Configuration Option

1. **Update `ConfigManager.DEFAULT_CONFIG`**
2. **Add property with getter/setter** (setter calls `self.save()`)
3. **Use in application** via `config_manager.my_new_option`
4. **Existing configs auto-migrate** (missing keys filled from defaults on load)

### Adding a New Model Field

1. **Update dataclass** in `src/model/`
2. **Update `to_dict()`** and `from_dict()`** methods
3. **Add default value** for backward compatibility with existing JSON
4. **Update ProfileManager** if profile data needs migration

---

## Build and Distribution

### PyInstaller Build

```bash
# Windows: Use the build script
build.bat
```

The build script:
1. Activates venv (if exists)
2. Installs PyInstaller (if not present)
3. Cleans previous `dist/` and `build/` directories
4. Runs `pyinstaller iptv_saba.spec --noconfirm`
5. Output: `dist/IPTV-Saba.exe`

### Resource Path Helper

When running as a bundled EXE, use `resource_path()` for all asset access:

```python
from src.utils.resource_path import resource_path

icon_path = resource_path("Assets/iptv-logo2.ico")
```

This handles both development mode (uses `src/` directory) and PyInstaller bundle mode (uses `sys._MEIPASS`).

### End-User Requirements

- **VLC Media Player** must be installed (for python-vlc bindings)
- Windows: VLC expected at `C:\Program Files\VideoLAN\VLC\`
- **ffmpeg** on PATH (only needed for `recorder.py` CLI feature)

---

## Git Workflow

### Branch Strategy

- **Main branch**: `master` - Stable releases
- **Feature branches**: `claude/feature-name-{session-id}`
- **Bug fix branches**: `claude/fix-description-{session-id}`

### Commit Message Format

Use conventional commit format:

```
<type>: <subject>

<body>
```

**Types**: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `perf`, `chore`

### Pre-commit Checklist

- [ ] Code follows PEP 8 style guide
- [ ] All imports use `src.` prefix
- [ ] No commented-out code (unless intentional)
- [ ] Logging statements added for debugging
- [ ] Manual testing completed
- [ ] No hardcoded paths or credentials
- [ ] Windows VLC crash scenarios considered (if touching player code)

---

## Important Files Reference

### Critical Files (DO NOT BREAK)

| File | Purpose | Caution Level |
|------|---------|---------------|
| `src/services/shared_player_manager.py` | Singleton VLC player + state machine | CRITICAL - breaks all playback |
| `src/data/data_loader.py` | M3U parsing | HIGH - affects all data loading |
| `src/controller/controller.py` | Central coordinator | HIGH - breaks entire app |
| `src/data/profile_manager.py` | Profile persistence | HIGH - data loss risk |
| `src/iptv_app.py` | Entry point + cleanup | HIGH - app lifecycle |
| `src/view/choose_channel_screen.py` | Main UI | MEDIUM - primary interface |
| `src/view/full_screen_view.py` | Video playback | MEDIUM - affects streaming |

### Configuration Files

| File | Purpose | Format |
|------|---------|--------|
| `requirements.txt` | Dependencies (PINNED) | Plain text |
| `build.bat` | Windows build script | Batch |
| `.gitignore` | Git exclusions | Plain text |

### Documentation Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | AI assistant guide (this file) |
| `docs/API_REFERENCE.md` | API documentation |
| `docs/ARCHITECTURE.md` | Architecture documentation |
| `docs/CODE_REVIEW_SUGGESTIONS.md` | Code review notes |
| `docs/CONTRIBUTING.md` | Contribution guidelines |
| `docs/DEVELOPMENT_SETUP.md` | Setup instructions |
| `docs/README.md` | User-facing documentation |
| `docs/USER_GUIDE.md` | User guide |

---

## Known Issues and Solutions

### Issue: VLC Crashes on Windows During Cleanup/Stop

**Status**: MITIGATED
**Root Cause**: VLC's internal threading conflicts with `player.stop()` on Windows.
**Solution**:
- Use `player.set_pause(1)` instead of `player.stop()`
- Use `player.set_media(None)` to effectively stop playback
- Detach from window (`set_hwnd(None)`) before releasing
- `safe_stop_for_cleanup()` method for logout scenarios
- `aboutToQuit` signal for final cleanup

### Issue: Black Screen in Fullscreen Mode

**Status**: FIXED
**Solution**: Use `showEvent()` for player attachment + platform-specific window ID handling + 100ms delay via `QTimer.singleShot`.

### Issue: Slow M3U Loading

**Status**: FIXED
**Solution**: Streaming parser with 64KB chunks + 4 parallel worker threads + string interning. 2-5x faster than traditional parsing.

### Issue: Duplicate Streams When Transitioning to Fullscreen

**Status**: FIXED
**Solution**: `SharedPlayerManager` singleton - player stopped + reattached to new frame during transitions. No new player instances created.

### Issue: Stream Fails Silently

**Status**: FIXED
**Solution**: VLC event callbacks detect errors and timeouts. Auto-retry with exponential backoff. `StreamHealthTracker` identifies problematic channels. `RetryOverlay` provides visual feedback.

### Common Pitfall: Thread Safety

**Problem**: Race conditions when accessing shared data.
**Solution**: Always use locks:
```python
with self.lock:
    # Access shared data here
```

### Common Pitfall: EasyMode Uses Separate VLC

**Problem**: `EasyModeScreen` does NOT use `SharedPlayerManager`.
**Implication**: It creates its own `vlc.Instance()` and player. Cleanup must be handled separately in `IPTVApp.cleanup()`.

### Common Pitfall: Import Paths

**Problem**: All imports use `from src.` prefix.
**Implication**: The project root must be on `sys.path`, not `src/`. Running `python src/iptv_app.py` from project root may fail; use `python -m src.iptv_app` instead, or run from within `src/` with the parent on path.

### Common Pitfall: .gitignore Has Merge Conflicts

**Status**: KNOWN
The `.gitignore` file currently contains unresolved merge conflict markers (`<<<<<<< Updated upstream` / `>>>>>>> Stashed changes`). This should be cleaned up.

---

## Quick Reference

### Import Paths

```python
# Controller
from src.controller.controller import Controller

# Models
from src.model.profile import Profile, create_mock_profile
from src.model.channel_model import Channel
from src.model.group_model import Group
from src.model.scheduled_recording import ScheduledRecording, RecordingStatus

# Data layer
from src.data.profile_manager import ProfileManager
from src.data.data_loader import DataLoader
from src.data.config_manager import ConfigManager
from src.data.recorder import Recording, record, record_now
from src.data.downloader import download_mp4

# Services
from src.services.shared_player_manager import SharedPlayerManager, get_shared_player
from src.services.download_record_manager import DownloadRecordManager
from src.services.stream_health_tracker import StreamHealthTracker, get_health_tracker
from src.services.hls_parser import HLSParser, QualityVariant, get_hls_parser
from src.services.schedule_manager import ScheduleManager
from src.services.recording_scheduler import RecordingScheduler

# Views
from src.view.login_view import LoginScreen, CreateProfileDialog
from src.view.choose_channel_screen import ChooseChannelScreen, LoaderWorker, LoadingOverlay
from src.view.full_screen_view import FullScreenView
from src.view.easy_mode_screen import EasyModeScreen
from src.view.retry_overlay import RetryOverlay
from src.view.schedule_dialog import ScheduleRecordingDialog

# Utils
from src.utils.resource_path import resource_path
```

### Useful Commands

```bash
# Run application
python -m src.iptv_app

# Run tests
python test_simple.py
python test_optimized_loader.py

# Build Windows EXE
build.bat

# Check dependencies
pip list
pip freeze > requirements.txt
```

---

**End of CLAUDE.md**

*This document is maintained for AI assistants working on IPTV-Saba. For user-facing documentation, see `docs/README.md`.*
