# IPTV-Saba Architecture Documentation

## Overview

IPTV-Saba is a desktop IPTV streaming application built with Python and PyQt5. The application follows a Model-View-Controller (MVC) architecture with an additional Service layer for complex operations.

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.8+ |
| UI Framework | PyQt5 | 5.15.11 |
| Video Playback | python-vlc | 3.0.21203 |
| Data Storage | JSON | - |
| HTTP Client | requests | 2.32.3 |
| Encoding Detection | chardet | 5.2.0 |
| String Matching | fuzzywuzzy, rapidfuzz | 0.18.0, 3.9.7 |

## High-Level Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           IPTVApp (iptv_app.py)         │
                    │   Application Entry & Lifecycle Mgmt    │
                    └─────────────────┬───────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────────┐
                    │        Controller (controller.py)        │
                    │   Central Coordinator & Business Logic   │
                    └──┬──────────────┬────────────────────┬──┘
                       │              │                    │
         ┌─────────────▼──┐    ┌──────▼──────┐    ┌───────▼────────┐
         │   Data Layer   │    │  View Layer │    │ Service Layer  │
         │                │    │             │    │                │
         │ - ProfileMgr   │    │ - Login     │    │ - SharedPlayer │
         │ - DataLoader   │    │ - ChanSel   │    │ - DownloadMgr  │
         │ - ConfigMgr    │    │ - FullScr   │    │                │
         │                │    │ - EasyMode  │    │                │
         └────────────────┘    └─────────────┘    └────────────────┘
                       │              │                    │
         ┌─────────────▼──────────────▼────────────────────▼──────┐
         │                      Model Layer                        │
         │     Profile  |  Channel  |  Group  |  StreamType       │
         └────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Application Layer (`src/iptv_app.py`)

**Responsibilities:**
- Application entry point and initialization
- QApplication lifecycle management
- Screen transition orchestration
- Resource cleanup on application exit

**Key Methods:**
- `__init__()`: Initialize QApplication and Controller
- `run()`: Start the application loop
- `cleanup()`: Clean up VLC resources
- `transition_to_*()`: Screen transition methods

**Signal Connections:**
- `app.aboutToQuit` → `cleanup()` for proper shutdown

### 2. Controller Layer (`src/controller/controller.py`)

**Responsibilities:**
- Central coordinator between data and view layers
- Profile management operations
- Channel search and filtering
- Favorites and history management
- Signal emission for UI updates

**Key Signals:**
| Signal | Parameter | Description |
|--------|-----------|-------------|
| `profiles_updated` | None | Profile list changed |
| `profile_selected` | str | Profile activated |
| `data_loaded` | dict | Channel data loaded |
| `error_occurred` | str | Error message |

**Dependencies:**
- ProfileManager (profile persistence)
- DataLoader (M3U parsing)
- ConfigManager (app settings)

### 3. Model Layer (`src/model/`)

#### Profile (`profile.py`)
```python
@dataclass
class Profile:
    name: str
    url: str
    favorites: List[Channel]
    history: List[Channel]
    last_loaded: Optional[int]
    max_history_items: int = 50
```

#### Channel (`channel_model.py`)
```python
@dataclass
class Channel:
    name: str
    stream_url: str
    tvg_id: str = ""
    tvg_logo: str = ""
    channel_type: str = ""
```

#### Group (`group_model.py`)
```python
@dataclass
class Group:
    name: str
    channels: List[Channel]
```

### 4. View Layer (`src/view/`)

#### Screen Hierarchy
```
QWidget
├── LoginScreen         # Profile selection
├── ChooseChannelScreen # Main channel browser
├── FullScreenView      # Fullscreen playback
└── EasyModeScreen      # Simplified interface
```

#### UI Patterns
- **Signal/Slot Communication**: Views emit signals, controller handles
- **Worker Threads**: Background data loading (LoaderWorker)
- **Loading Overlay**: Visual feedback during operations
- **Auto-hiding Controls**: Video player controls

### 5. Data Layer (`src/data/`)

#### DataLoader
**Features:**
- Streaming M3U parser (64KB chunks)
- Parallel processing (4 worker threads)
- Encoding detection (chardet)
- JSON caching with 24h TTL
- Fast channel lookup (O(1) via index)

**Optimization Techniques:**
- String interning for memory optimization
- Pre-compiled regex patterns
- Incremental parsing during download

#### ProfileManager
**Features:**
- Thread-safe operations (RLock)
- Atomic file writes (temp file + replace)
- Rollback capability on save failure
- Dual data structures (dict + list)

#### ConfigManager
**Configuration Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `last_active_profile_id` | str | Last selected profile |
| `auto_login_enabled` | bool | Auto-login on startup |
| `theme` | str | UI theme |
| `app_version` | str | Application version |
| `first_run` | bool | First-time setup flag |
| `log_level` | str | Logging verbosity |

### 6. Service Layer (`src/services/`)

#### SharedPlayerManager
**Features:**
- Singleton VLC player instance
- State machine for view transitions
- Platform-specific window attachment
- Connection timeout detection
- Buffering progress tracking

**States:**
```
IDLE → EMBEDDED → TRANSITIONING → FULLSCREEN
  ↑                                    │
  └────────────────────────────────────┘
```

#### DownloadRecordManager
**Features:**
- Concurrent download management
- Live stream recording
- Progress signals for UI updates
- Sanitized filename generation

## Data Flow

### Profile Login Flow
```
1. User selects profile in LoginScreen
2. LoginScreen emits login_success signal
3. IPTVApp receives signal
4. Controller.select_profile() called
5. IPTVApp.transition_to_channel_selection_screen()
6. ChooseChannelScreen creates LoaderWorker
7. LoaderWorker loads M3U in background
8. Worker emits data_loaded signal
9. ChooseChannelScreen populates UI
```

### Channel Playback Flow
```
1. User clicks channel in list
2. on_channel_selected() called
3. SharedPlayerManager.play_channel() invoked
4. VLC media created and set
5. Player attached to video frame
6. Playback starts
7. Channel added to history
```

### Fullscreen Transition Flow
```
1. User clicks fullscreen button
2. ChooseChannelScreen creates FullScreenView
3. SharedPlayerManager.transition_to_fullscreen() called
4. State changes to TRANSITIONING
5. Current playback state saved
6. Player stops and reattaches to new frame
7. Playback resumes
8. State changes to FULLSCREEN
```

## File Storage

### Directory Structure
```
IPTV-Saba/                    # Application data directory
├── config.json               # App configuration
├── profiles.json             # User profiles
├── {profile_name}data.json   # Cached channel data (24h TTL)
└── downloads/                # Downloaded/recorded media
```

### File Formats

#### profiles.json
```json
[
  {
    "name": "ProfileName",
    "url": "https://example.com/playlist.m3u",
    "favorites": [/* Channel objects */],
    "history": [/* Channel objects */],
    "last_loaded": 1700000000
  }
]
```

#### config.json
```json
{
  "last_active_profile_id": "ProfileName",
  "auto_login_enabled": true,
  "theme": "default",
  "app_version": "1.0.0",
  "first_run": false,
  "log_level": "INFO"
}
```

## Threading Model

### Main Thread
- All PyQt5 UI operations
- Signal/slot processing
- User input handling

### Worker Threads
- M3U playlist loading (LoaderWorker)
- Media downloads (DownloadRecordManager)
- Stream recording

### Thread Safety
- ProfileManager uses RLock for all operations
- DataLoader streaming parser uses thread-safe queues
- Signals used for cross-thread communication

## Error Handling

### Exception Hierarchy
```
Exception
├── DataLoader.ParseError      # M3U parsing errors
├── DataLoader.SourceError     # Source retrieval errors
└── DataLoader.NetworkError    # Network-related errors
```

### Recovery Strategies
1. **Network Errors**: Exponential backoff retry (3 attempts)
2. **Cache Fallback**: Load cached data if network fails
3. **Rollback**: ProfileManager rolls back on save failure
4. **Graceful Degradation**: Continue with available data

## Platform Support

### Windows
- VLC plugin path: `C:\Program Files\VideoLAN\VLC\plugins`
- Window attachment: `set_hwnd()`
- AppUserModelID for taskbar

### Linux
- Window attachment: `set_xwindow()`
- Standard VLC installation

### macOS
- Window attachment: `set_nsobject()`
- Standard VLC installation

## Performance Considerations

1. **M3U Loading**: Streaming parser with parallel processing
2. **Channel Lookup**: O(1) via name index
3. **UI Responsiveness**: Worker threads for heavy operations
4. **Memory**: String interning for repeated values
5. **Caching**: 24-hour TTL on channel data
