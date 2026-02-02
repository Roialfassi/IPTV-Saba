# IPTV-Saba API Reference

## Table of Contents

1. [Controller](#controller)
2. [ProfileManager](#profilemanager)
3. [DataLoader](#dataloader)
4. [ConfigManager](#configmanager)
5. [SharedPlayerManager](#sharedplayermanager)
6. [DownloadRecordManager](#downloadrecordmanager)
7. [Models](#models)

---

## Controller

**Module:** `src.controller.controller`

Central coordinator for application logic and state management.

### Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `profiles_updated` | None | Emitted when profile list changes |
| `error_occurred` | `str` | Emitted on errors with message |
| `profile_selected` | `str` | Emitted when profile is activated |
| `data_loaded` | `dict` | Emitted when channel data is loaded |

### Constructor

```python
Controller(profiles_file: str = "profiles.json", folder_name: str = 'IPTV-Saba')
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `profiles_file` | str | "profiles.json" | Filename for profiles storage |
| `folder_name` | str | "IPTV-Saba" | Application data directory name |

### Methods

#### `login_logic() -> bool`
Check if auto-login should be performed.

**Returns:** `True` if auto-login succeeded, `False` otherwise

---

#### `list_profiles() -> List[str]`
Get all available profile names.

**Returns:** List of profile names

---

#### `select_profile(name: str) -> None`
Select and activate a profile.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Profile name to select |

**Emits:** `profile_selected` signal on success, `error_occurred` on failure

---

#### `create_profile(name: str, url: str) -> None`
Create a new profile.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Profile name |
| `url` | str | M3U playlist URL |

**Emits:** `profiles_updated` on success, `error_occurred` on failure

---

#### `delete_profile(name: str) -> None`
Delete an existing profile.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Profile name to delete |

**Emits:** `profiles_updated` on success, `error_occurred` on failure

---

#### `list_groups() -> List[str]`
Get all channel group names.

**Returns:** List of group names

---

#### `list_channels_in_group(group_name: Optional[str] = None) -> List[str]`
Get channel names in a group.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `group_name` | Optional[str] | None | Group name (uses selected group if None) |

**Returns:** List of channel names

---

#### `search_channels(query: str) -> List[Channel]`
Search channels by name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | str | Search string |

**Returns:** List of matching Channel objects

---

#### `find_channel_by_name(channel_name: str) -> Optional[Channel]`
Find a specific channel by exact name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `channel_name` | str | Channel name to find |

**Returns:** Channel object or None

---

#### `add_to_favorites(channel_name: str) -> None`
Add a channel to favorites.

| Parameter | Type | Description |
|-----------|------|-------------|
| `channel_name` | str | Channel name to add |

---

#### `remove_from_favorites(channel_name: str) -> None`
Remove a channel from favorites.

| Parameter | Type | Description |
|-----------|------|-------------|
| `channel_name` | str | Channel name to remove |

---

#### `add_to_history(channel: Channel) -> None`
Add a channel to watch history.

| Parameter | Type | Description |
|-----------|------|-------------|
| `channel` | Channel | Channel to add |

---

## ProfileManager

**Module:** `src.data.profile_manager`

Thread-safe profile management with atomic file operations.

### Constructor

```python
ProfileManager(profiles_folder: str, profiles_file_name: str = "profiles.json")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `profiles_folder` | str | - | Directory for profile storage |
| `profiles_file_name` | str | "profiles.json" | Filename for profiles |

### Methods

#### `load_profiles() -> bool`
Load profiles from JSON file.

**Returns:** `True` if successful

---

#### `save_profiles() -> bool`
Save profiles to JSON file atomically.

**Returns:** `True` if successful

---

#### `create_profile(name: str, url: str, favorites: Optional[List[str]] = None) -> Optional[Profile]`
Create a new profile with rollback support.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | - | Profile name |
| `url` | str | - | M3U playlist URL |
| `favorites` | Optional[List[str]] | None | Initial favorites |

**Returns:** Created Profile or None on failure

---

#### `get_profile(name: str) -> Optional[Profile]`
Retrieve a profile by name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Profile name |

**Returns:** Profile or None

---

#### `update_profile(updated_profile: Profile) -> bool`
Update an existing profile.

| Parameter | Type | Description |
|-----------|------|-------------|
| `updated_profile` | Profile | Profile with updated data |

**Returns:** `True` if successful

---

#### `delete_profile(name: str) -> bool`
Delete a profile with rollback support.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Profile name |

**Returns:** `True` if successful

---

#### `list_profiles() -> List[str]`
Get all profile names.

**Returns:** List of profile names

---

#### `find_profiles(name: Optional[str] = None, url: Optional[str] = None) -> List[Profile]`
Search profiles by name and/or URL.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | Optional[str] | Name filter |
| `url` | Optional[str] | URL filter |

**Returns:** List of matching profiles

---

#### `export_profiles(export_file_path: str) -> bool`
Export profiles to a file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `export_file_path` | str | Destination path |

**Returns:** `True` if successful

---

#### `import_profiles(import_file_path: str, overwrite_existing: bool = False) -> Tuple[int, int, int]`
Import profiles from a file.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `import_file_path` | str | - | Source file path |
| `overwrite_existing` | bool | False | Overwrite existing profiles |

**Returns:** Tuple of (added, updated, errors)

---

## DataLoader

**Module:** `src.data.data_loader`

Optimized M3U playlist parser with streaming and parallel processing.

### Class Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MAX_RETRIES` | 3 | Maximum retry attempts |
| `INITIAL_RETRY_DELAY` | 1.0 | Initial retry delay in seconds |
| `MAX_RETRY_DELAY` | 30.0 | Maximum retry delay in seconds |
| `BACKOFF_MULTIPLIER` | 2.0 | Exponential backoff multiplier |

### Exceptions

| Exception | Description |
|-----------|-------------|
| `ParseError` | M3U parsing errors |
| `SourceError` | Source retrieval errors |
| `NetworkError` | Network-related errors |

### Constructor

```python
DataLoader(default_group_name: str = "Ungrouped")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `default_group_name` | str | "Ungrouped" | Name for channels without group |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `groups` | Dict[str, Group] | All channel groups |
| `channels` | List[Channel] | All channels |

### Methods

#### `load(source: str, use_optimized: bool = True, progress_callback: Callable = None) -> bool`
Load M3U data from URL, file, or string.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | str | - | URL, file path, or M3U content |
| `use_optimized` | bool | True | Use streaming parser |
| `progress_callback` | Callable | None | Progress callback(current, total, message) |

**Returns:** `True` if successful

---

#### `get_group(name: str) -> Optional[Group]`
Find a group by exact name.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Group name |

**Returns:** Group or None

---

#### `get_channel_by_name(channel_name: str) -> Optional[Channel]`
Fast channel lookup by name (O(1)).

| Parameter | Type | Description |
|-----------|------|-------------|
| `channel_name` | str | Channel name |

**Returns:** Channel or None

---

#### `search_channels(pattern: Union[str, Pattern], search_fields: List[str] = None) -> List[Channel]`
Search channels with regex pattern.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pattern` | Union[str, Pattern] | - | Search pattern |
| `search_fields` | List[str] | ['name', 'tvg_id'] | Fields to search |

**Returns:** List of matching channels

---

#### `find_groups(pattern: Union[str, Pattern]) -> List[Group]`
Find groups matching a pattern.

| Parameter | Type | Description |
|-----------|------|-------------|
| `pattern` | Union[str, Pattern] | Search pattern |

**Returns:** List of matching groups

---

#### `get_channels_by_type(stream_type: StreamType) -> List[Channel]`
Get channels of a specific type.

| Parameter | Type | Description |
|-----------|------|-------------|
| `stream_type` | StreamType | LIVE, VOD, or SERIES |

**Returns:** List of channels

---

#### `save_to_json(file_path: str) -> bool`
Save parsed data to JSON cache.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | str | Destination path |

**Returns:** `True` if successful

---

#### `load_from_json(file_path: str) -> bool`
Load data from JSON cache.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | str | Source path |

**Returns:** `True` if successful

---

#### `get_statistics() -> Dict[str, Any]`
Get statistics about loaded data.

**Returns:** Dictionary with statistics

---

#### `detect_stream_type(url: str, name: str = "", metadata: Dict = None) -> StreamType`
Detect stream type from URL and metadata.

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | str | Stream URL |
| `name` | str | Channel name |
| `metadata` | Dict | M3U metadata |

**Returns:** StreamType enum value

---

## ConfigManager

**Module:** `src.data.config_manager`

Application configuration management.

### Default Configuration

```python
DEFAULT_CONFIG = {
    "last_active_profile_id": None,
    "auto_login_enabled": False,
    "theme": "default",
    "app_version": "1.0.0",
    "first_run": True,
    "log_level": "INFO"
}
```

### Constructor

```python
ConfigManager(config_dir: str = None, config_filename: str = "config.json")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config_dir` | str | None | Config directory (defaults to ~/.myapp) |
| `config_filename` | str | "config.json" | Config filename |

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `last_active_profile_id` | str | Last active profile ID |
| `auto_login_enabled` | bool | Auto-login flag |
| `theme` | str | Current theme |

### Methods

#### `should_auto_login() -> Tuple[bool, str]`
Check if auto-login should be performed.

**Returns:** Tuple of (should_login, profile_id)

---

#### `get_value(key: str, default = None) -> Any`
Get a configuration value.

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | str | Configuration key |
| `default` | Any | Default value |

**Returns:** Configuration value

---

#### `set_value(key: str, value: Any) -> None`
Set a configuration value.

| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | str | Configuration key |
| `value` | Any | Value to set |

---

#### `reset_to_defaults() -> None`
Reset configuration to defaults.

---

#### `save() -> None`
Save configuration to file.

---

## SharedPlayerManager

**Module:** `src.services.shared_player_manager`

Singleton VLC player manager with state machine.

### Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `state_changed` | PlayerViewState | View state changed |
| `channel_changed` | Channel | Current channel changed |
| `playback_started` | None | Playback started |
| `playback_stopped` | None | Playback stopped |
| `error_occurred` | str | Error message |
| `stream_error` | str | Stream error |
| `connection_timeout` | str | Connection timeout |
| `buffering` | int | Buffering percentage |

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `CONNECTION_TIMEOUT` | 15 | Timeout in seconds |

### States (PlayerViewState)

| State | Description |
|-------|-------------|
| `IDLE` | No view attached, player stopped |
| `EMBEDDED` | Playing in embedded view |
| `TRANSITIONING` | Moving between views |
| `FULLSCREEN` | Playing in fullscreen |

### Class Methods

#### `get_instance() -> SharedPlayerManager`
Get the singleton instance.

---

#### `reset_instance() -> None`
Reset the singleton (for cleanup).

---

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `player` | vlc.MediaPlayer | VLC player instance |
| `vlc_instance` | vlc.Instance | VLC instance |
| `state` | PlayerViewState | Current state |
| `current_channel` | Channel | Current channel |
| `is_playing` | bool | Playback status |
| `volume` | int | Volume (0-100) |

### Methods

#### `play_channel(channel, frame: QWidget = None) -> bool`
Start playing a channel.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `channel` | Channel | - | Channel to play |
| `frame` | QWidget | None | Video frame (uses embedded if None) |

**Returns:** `True` if successful

---

#### `play() -> None`
Resume playback.

---

#### `pause() -> None`
Pause playback.

---

#### `stop() -> None`
Stop playback safely.

---

#### `set_volume(value: int) -> None`
Set volume level.

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | int | Volume (0-100) |

---

#### `transition_to_fullscreen(fullscreen_frame: QWidget) -> bool`
Transition to fullscreen view.

| Parameter | Type | Description |
|-----------|------|-------------|
| `fullscreen_frame` | QWidget | Fullscreen video frame |

**Returns:** `True` if successful

---

#### `transition_to_embedded() -> bool`
Transition back to embedded view.

**Returns:** `True` if successful

---

#### `register_embedded_frame(frame: QWidget) -> None`
Register embedded video frame.

---

#### `register_fullscreen_frame(frame: QWidget) -> None`
Register fullscreen video frame.

---

#### `cleanup() -> None`
Clean up all resources.

---

### Convenience Function

```python
get_shared_player() -> SharedPlayerManager
```

Get the shared player manager instance.

---

## DownloadRecordManager

**Module:** `src.services.download_record_manager`

Download and recording manager.

### Signals

| Signal | Parameters | Description |
|--------|------------|-------------|
| `download_progress` | str, int, int | id, bytes_downloaded, total_bytes |
| `download_complete` | str, str | id, file_path |
| `download_error` | str, str | id, error_message |
| `recording_started` | str | id |
| `recording_stopped` | str, str | id, file_path |

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MEDIA_EXTENSIONS` | set | Downloadable extensions |

### Constructor

```python
DownloadRecordManager(downloads_dir: str = "downloads")
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `downloads_dir` | str | "downloads" | Download directory |

### Methods

#### `is_media_file(url: str) -> bool`
Check if URL is a downloadable media file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | str | URL to check |

**Returns:** `True` if downloadable media

---

#### `generate_filename(channel_name: str, url: str, is_recording: bool = False) -> str`
Generate a safe filename.

| Parameter | Type | Description |
|-----------|------|-------------|
| `channel_name` | str | Channel name |
| `url` | str | Stream URL |
| `is_recording` | bool | Recording flag |

**Returns:** Generated filename

---

#### `start_download(download_id: str, channel_name: str, url: str) -> bool`
Start downloading a media file.

| Parameter | Type | Description |
|-----------|------|-------------|
| `download_id` | str | Unique identifier |
| `channel_name` | str | Channel name |
| `url` | str | URL to download |

**Returns:** `True` if started

---

#### `start_recording(recording_id: str, channel_name: str, url: str) -> bool`
Start recording a livestream.

| Parameter | Type | Description |
|-----------|------|-------------|
| `recording_id` | str | Unique identifier |
| `channel_name` | str | Channel name |
| `url` | str | Stream URL |

**Returns:** `True` if started

---

#### `stop_recording(recording_id: str, blocking: bool = False) -> bool`
Stop an active recording.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `recording_id` | str | - | Recording ID |
| `blocking` | bool | False | Wait for finalization |

**Returns:** `True` if stopped

---

#### `cancel_download(download_id: str) -> bool`
Cancel an active download.

| Parameter | Type | Description |
|-----------|------|-------------|
| `download_id` | str | Download ID |

**Returns:** `True` if cancelled

---

#### `cleanup_all(blocking: bool = True) -> None`
Stop all downloads and recordings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `blocking` | bool | True | Wait for finalization |

---

## Models

### Channel

**Module:** `src.model.channel_model`

```python
@dataclass
class Channel:
    name: str
    stream_url: str
    tvg_id: str = ""
    tvg_logo: str = ""
    channel_type: str = ""
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | dict | Serialize to dictionary |
| `from_dict(data)` | Channel | Create from dictionary |
| `validate_stream_url()` | bool | Check if URL is reachable |
| `download_logo(path)` | bool | Download logo image |

---

### Group

**Module:** `src.model.group_model`

```python
@dataclass
class Group:
    name: str
    channels: List[Channel] = field(default_factory=list)
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `add_channel(channel)` | None | Add channel to group |
| `remove_channel(channel)` | None | Remove channel |
| `find_channel_by_name(name)` | Optional[Channel] | Find channel |
| `to_dict()` | dict | Serialize to dictionary |
| `from_dict(data)` | Group | Create from dictionary |

---

### Profile

**Module:** `src.model.profile`

```python
@dataclass
class Profile:
    name: str
    url: str
    favorites: List[Channel] = field(default_factory=list)
    history: List[Channel] = field(default_factory=list)
    last_loaded: Optional[int] = None
    max_history_items: int = 50
```

#### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `add_to_favorites(channel)` | None | Add to favorites |
| `remove_from_favorites(channel)` | None | Remove from favorites |
| `add_to_history(channel)` | None | Add to history |
| `is_in_favorites(name)` | int | Index or -1 |
| `is_in_history(name)` | int | Index or -1 |
| `clear_favorites()` | None | Clear favorites |
| `clear_history()` | None | Clear history |
| `needs_refresh()` | bool | Check if data needs refresh |
| `is_within_24_hours()` | bool | Check if recently loaded |
| `validate_url()` | bool | Validate M3U URL |
| `update_favorites(loader)` | None | Sync favorites with data |
| `update_history(loader)` | None | Sync history with data |
| `to_dict()` | dict | Serialize to dictionary |
| `from_dict(data)` | Profile | Create from dictionary |
| `to_json()` | str | Serialize to JSON string |
| `from_json(json_str)` | Profile | Create from JSON string |

---

### StreamType

**Module:** `src.data.data_loader`

```python
class StreamType(Enum):
    LIVE = "live"
    VOD = "vod"
    SERIES = "series"
    UNKNOWN = "unknown"
```
