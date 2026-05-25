# CLAUDE.md - IPTV-Saba

## What This Is

Desktop IPTV streaming app: Python 3.8+ / PyQt5 / python-vlc. MVC + Service Layer architecture.
Features: profiles, M3U playlists, favorites, history, scheduled recordings, stream health/retry, HLS quality selection, Easy Mode (elderly users), PyInstaller build.

## Running

```bash
# From project root
python -m src.iptv_app

# Tests
python test_simple.py
python test_optimized_loader.py

# Build Windows EXE
build.bat
```

**Prerequisites**: VLC Media Player installed, ffmpeg on PATH (for scheduled recordings).

## Critical Conventions

- **All imports use `src.` prefix**: `from src.controller.controller import Controller`
- **Naming**: PascalCase classes, snake_case functions, UPPER_SNAKE_CASE constants, `_leading_underscore` private
- **PEP 8**, 4 spaces, type hints on signatures, `logger = logging.getLogger(__name__)`
- **Data models**: `@dataclass` for simple models. `Profile` has custom `__init__` despite `@dataclass` decorator.
- **Thread safety**: `threading.RLock` for shared state (ProfileManager, ScheduleManager, StreamHealthTracker)
- **Atomic writes**: Write to `.tmp` then `os.replace()` (ProfileManager, ScheduleManager)
- **PyQt signals/slots** for all cross-component communication

## Architecture Essentials

- **SharedPlayerManager** — singleton VLC player (`get_shared_player()`). ALL main-app playback goes through this. State machine: IDLE -> EMBEDDED -> TRANSITIONING -> FULLSCREEN.
- **EasyModeScreen** — exception: creates its OWN `vlc.Instance()`, does NOT use SharedPlayerManager.
- **DataLoader** — streaming M3U parser with 4 worker threads, O(1) channel lookup via `_channel_index`, 24h JSON cache.
- **StreamHealthTracker** — singleton, channel is "problematic" at 3+ consecutive failures OR >50% failure rate with 5+ attempts.
- **RecordingScheduler** — QTimer checks every 30s, delegates to DownloadRecordManager.

## Windows VLC Workarounds (CRITICAL)

These prevent crashes on Windows — do not change without testing:

1. **Never call `player.stop()` during cleanup** — use `player.set_pause(1)` then `player.set_media(None)`
2. **Detach before release** — `player.set_hwnd(None)` before `player.release()`
3. **VLC plugins path**: `--plugin-path=C:\Program Files\VideoLAN\VLC\plugins`
4. **`safe_stop_for_cleanup()`** only pauses, never stops — designed for logout/exit

## Runtime Data

All persisted to `{cwd}/IPTV-Saba/` as JSON: `profiles.json`, `config.json`, `schedules.json`, `{profile}data.json` (cached channels, 24h TTL), `downloads/`.

## UI Styling

Netflix-inspired dark theme. Key colors: `#E50914` (primary red), `#141414` (background), `#1877F2` (secondary blue), `#FFFFFF` / `#AAAAAA` (text).

## Build

`build.bat` runs PyInstaller via `iptv_saba.spec` -> `dist/IPTV-Saba.exe`. Use `resource_path()` from `src.utils.resource_path` for all asset paths (handles both dev and bundled modes).
