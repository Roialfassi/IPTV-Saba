# IPTV-Saba Developer Guide

**For LLMs and Developers Making Safe Improvements**

This guide helps you understand the codebase, avoid regressions, and make meaningful improvements to IPTV-Saba.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding the Current State](#understanding-the-current-state)
3. [Critical Paths - DO NOT BREAK](#critical-paths---do-not-break)
4. [Testing Strategy](#testing-strategy)
5. [High-Impact Improvements](#high-impact-improvements)
6. [Common Gotchas](#common-gotchas)
7. [Verification Procedures](#verification-procedures)
8. [Safe Development Workflow](#safe-development-workflow)

---

## Quick Start

### What is IPTV-Saba?

A desktop IPTV streaming application built with Python/PyQt5 that:
- Manages multiple user profiles with separate M3U playlists
- Provides channel browsing, favorites, and watch history
- Offers VLC-based video playback with fullscreen mode
- Includes "Easy Mode" for elderly users (simplified UI)
- Supports downloading and recording streams

### Technology Stack

```yaml
Language: Python 3.8+
UI: PyQt5 (5.15.11)
Video: python-vlc (3.0.21203)
Data: JSON files (profiles.json, config.json)
Architecture: MVC with service layer
Platforms: Windows (primary), Linux, macOS
```

### Get Running in 5 Minutes

```bash
# 1. Clone and navigate
git clone https://github.com/Roialfassi/IPTV-Saba.git
cd IPTV-Saba

# 2. Set up environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
cd src
python iptv_app.py
```

**First Run:** The app creates a mock profile automatically. You can create real profiles with M3U playlist URLs.

### Verify It Works

- [ ] Application window opens without errors
- [ ] Can create a new profile
- [ ] Can select a profile (mock or created)
- [ ] Channel list loads (for mock profile)
- [ ] Can click a channel and see video player area
- [ ] Can add channel to favorites (star icon)

---

## Understanding the Current State

### Architecture Overview

```
┌─────────────────────────────────────────────┐
│         iptv_app.py (Entry Point)           │
│  • Manages screen transitions               │
│  • Handles auto-login                       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│       controller.py (Orchestrator)          │
│  • Central coordinator (257 lines)          │
│  • Manages active profile and channels      │
│  • Emits PyQt5 signals for UI updates       │
└────┬────────┬────────┬────────┬─────────────┘
     │        │        │        │
     ▼        ▼        ▼        ▼
┌─────────┐ ┌──────┐ ┌──────┐ ┌─────────┐
│Profile  │ │Data  │ │Config│ │Download │
│Manager  │ │Loader│ │Mgr   │ │Record   │
│(338 ln) │ │(630) │ │(181) │ │Manager  │
└─────────┘ └──────┘ └──────┘ └─────────┘
```

### Key Files by Risk Level

| Risk | File | Lines | Purpose | Why Critical |
|------|------|-------|---------|--------------|
| 🔴 **CRITICAL** | `src/data/data_loader.py` | 630 | M3U parser | Breaks all data loading |
| 🔴 **CRITICAL** | `src/controller/controller.py` | 257 | Central coordinator | Breaks entire app |
| 🔴 **CRITICAL** | `src/data/profile_manager.py` | 338 | Profile persistence | Data loss risk |
| 🟡 **HIGH** | `src/view/choose_channel_screen.py` | 800+ | Main UI | Primary interface |
| 🟡 **HIGH** | `src/view/full_screen_view.py` | 200+ | Video playback | Streaming experience |
| 🟢 **MEDIUM** | `src/view/login_view.py` | 472 | Profile selection | Entry point |
| 🟢 **MEDIUM** | `src/data/config_manager.py` | 181 | App config | Settings management |

### Recent Major Fixes

**Understand these before modifying related code:**

1. **Fullscreen Black Screen Fix** (`FULLSCREEN_FIX_DETAILS.md`)
   - Problem: Video disappeared in fullscreen
   - Solution: Platform-specific VLC attachment in `showEvent()`
   - Key Pattern: Reuse player instance, don't create new ones

2. **M3U Loading Optimization** (`OPTIMIZATION_DETAILS.md`)
   - Problem: Slow loading of large playlists
   - Solution: Streaming parser with 64KB chunks + 4 worker threads
   - Performance: 2-5x faster than traditional parsing

3. **Download/Record Feature** (`DOWNLOAD_RECORD_FEATURE.md`)
   - Implements concurrent download/record with progress tracking
   - Thread-safe operations with worker threads

### Data Flow

```
User Action → View (emit signal) → Controller (business logic)
  → Manager (data access) → JSON File / Network

Updates: JSON → Manager → Controller (emit signal) → View (update UI)
```

**Example: Adding to Favorites**

```
1. User clicks star icon → ChooseChannelScreen.on_favorite_clicked()
2. View emits signal → Controller.add_to_favorites(channel_name)
3. Controller finds channel → active_profile.add_favorite(channel)
4. Controller saves → profile_manager.update_profile()
5. ProfileManager writes → atomic file write to profiles.json
6. Controller emits → profiles_updated signal
7. View receives signal → updates UI with star filled
```

---

## Critical Paths - DO NOT BREAK

### 1. Profile Loading and Saving

**Why Critical:** Data loss if broken

**Files Involved:**
- `src/data/profile_manager.py` (lines 54-71: save_profiles)
- `src/model/profile.py` (to_dict/from_dict serialization)

**What NOT to Break:**
```python
# ✅ MUST maintain this pattern:
with self.lock:  # Thread safety
    # Atomic write pattern
    with tempfile.NamedTemporaryFile('w', delete=False) as tmp:
        json.dump(data, tmp, indent=2)
    os.replace(tmp_path, self.profiles_file)  # Atomic!
```

**How to Verify:**
```python
# Test script
manager = ProfileManager()
profile = manager.create_profile("Test", "http://example.com/test.m3u")
manager.save_profiles()

# Kill app, restart
manager2 = ProfileManager()
assert "Test" in manager2.list_profiles()
```

### 2. M3U Playlist Parsing

**Why Critical:** Affects all channel data

**Files Involved:**
- `src/data/data_loader.py` (entire file, especially load_from_url_streaming)

**What NOT to Break:**
```python
# ✅ MUST preserve:
# 1. Encoding detection (chardet)
# 2. Line-by-line parsing (handles large files)
# 3. #EXTINF and #EXTM3U tag parsing
# 4. Thread-safe group assignment
```

**Regression Risks:**
- Changing regex patterns for EXTINF parsing
- Modifying chunk size without testing large files
- Breaking encoding detection
- Thread-unsafe list operations

**How to Verify:**
```bash
python test_optimized_loader.py  # Benchmark test
python test_simple.py            # Functional test
# Should load without errors, channels > 0
```

### 3. VLC Player Lifecycle

**Why Critical:** Video playback breaks if wrong

**Files Involved:**
- `src/view/choose_channel_screen.py` (player creation/attachment)
- `src/view/full_screen_view.py` (player reuse, showEvent attachment)

**What NOT to Break:**
```python
# ✅ MUST maintain this pattern:

# 1. Create ONCE per screen
self.vlc_instance = vlc.Instance()
self.player = self.vlc_instance.media_player_new()

# 2. Attach in showEvent() - NOT in __init__!
def showEvent(self, event):
    super().showEvent(event)
    if not self.player_attached:
        QTimer.singleShot(100, self.attach_player)  # Delay critical!

# 3. Platform-specific attachment
if sys.platform == "win32":
    self.player.set_hwnd(window_id)
elif sys.platform.startswith('linux'):
    self.player.set_xwindow(window_id)
elif sys.platform == "darwin":
    self.player.set_nsobject(window_id)

# 4. REUSE player when transitioning screens
fullscreen = FullScreenView(self.player, self.vlc_instance)  # Pass existing!
```

**Regression Risks:**
- Creating new player instance for fullscreen (causes dual streams)
- Attaching player in `__init__` (window ID not valid yet)
- Missing platform check
- Not using QTimer delay

**How to Verify:**
```
1. Play a channel in main screen
2. Enter fullscreen
3. Video should continue playing (same stream)
4. Exit fullscreen
5. Video should still play
6. No "black screen" at any point
```

### 4. Signal/Slot Communication

**Why Critical:** UI updates break if signals don't emit

**Files Involved:**
- `src/controller/controller.py` (all signals)
- All view files (signal connections)

**What NOT to Break:**
```python
# ✅ MUST emit signals after operations:

class Controller(QObject):
    profiles_updated = pyqtSignal()
    error_occurred = pyqtSignal(str)
    data_loaded = pyqtSignal()

    def create_profile(self, name, url):
        # Do work...
        self.profiles_updated.emit()  # REQUIRED!

    # ✅ Views MUST connect to signals:
    controller.profiles_updated.connect(self.refresh_profile_list)
```

**Regression Risks:**
- Forgetting to emit signal after data changes
- Disconnecting signals without reconnecting
- Emitting wrong signal type

**How to Verify:**
```
Test each user action:
1. Create profile → Profile appears in list
2. Delete profile → Profile disappears
3. Add favorite → Star icon fills
4. Remove favorite → Star icon empties
5. All should happen immediately (signals working)
```

### 5. Thread Safety in ProfileManager

**Why Critical:** Concurrent access can corrupt data

**Files Involved:**
- `src/data/profile_manager.py` (all methods with self.lock)

**What NOT to Break:**
```python
# ✅ MUST wrap shared data access:
from threading import RLock

class ProfileManager:
    def __init__(self):
        self.lock = RLock()  # Reentrant lock!

    def update_profile(self, name, profile):
        with self.lock:  # REQUIRED for thread safety
            self.profiles_dict[name] = profile
            self.save_profiles()
```

**Regression Risks:**
- Removing `with self.lock:` blocks
- Changing RLock to Lock (breaks reentrant calls)
- Accessing self.profiles_dict outside lock

**How to Verify:**
```python
# Stress test (run in test script)
import threading

def rapid_updates():
    for i in range(100):
        manager.update_profile("Test", profile)

threads = [threading.Thread(target=rapid_updates) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()

# Should not crash, profiles.json should be valid JSON
```

---

## Testing Strategy

### Current State: No Automated Tests

**What Exists:**
- `test_simple.py` - Basic M3U loading test
- `test_optimized_loader.py` - Performance benchmark
- Manual testing only

**Testing Gap:** 🔴 **CRITICAL RISK**

### Before Making ANY Changes

**Run these manual tests:**

```bash
# 1. Basic functionality
cd src
python iptv_app.py
# [ ] App launches
# [ ] Can create profile
# [ ] Can load channels
# [ ] Can play channel
# [ ] Can add to favorites
# [ ] Favorites persist after restart

# 2. Performance test
python test_optimized_loader.py
# [ ] Completes without errors
# [ ] Performance within expected range

# 3. Parser test
python test_simple.py
# [ ] Loads test_sample.m3u successfully
```

### After Making Changes

**Regression Test Checklist:**

```
Core Functionality:
[ ] Application starts without errors
[ ] No new errors in console/logs
[ ] Profile creation works
[ ] Profile deletion works
[ ] Profile switching works
[ ] Channel list loads
[ ] Search works
[ ] Favorites add/remove works
[ ] History tracks watched channels

Video Playback:
[ ] Channel plays in main screen
[ ] Fullscreen mode works
[ ] Exit fullscreen works
[ ] No black screen
[ ] No duplicate audio (dual streams)
[ ] Volume control works

Data Persistence:
[ ] Favorites survive app restart
[ ] History survives app restart
[ ] Config (auto-login) survives restart
[ ] Can export/import profiles

Performance:
[ ] No noticeable slowdown
[ ] test_optimized_loader.py still fast
[ ] UI doesn't freeze during operations
```

### Setting Up Automated Tests (RECOMMENDED)

**Step 1: Install pytest**

```bash
pip install pytest pytest-qt pytest-cov
```

**Step 2: Create test structure**

```bash
mkdir -p tests/{unit,integration}
touch tests/__init__.py
touch tests/conftest.py
```

**Step 3: Write first test**

```python
# tests/unit/test_profile.py
import pytest
from model.profile import Profile
from model.channel_model import Channel

def test_profile_serialization():
    """Verify profile can be saved and restored"""
    profile = Profile("TestUser", "http://example.com/playlist.m3u")
    channel = Channel("CNN", "http://stream.url", "cnn.us", "http://logo.url")
    profile.add_favorite(channel)

    # Serialize
    data = profile.to_dict()

    # Restore
    restored = Profile.from_dict(data)

    assert restored.name == "TestUser"
    assert len(restored.favorites) == 1
    assert restored.favorites[0].name == "CNN"

def test_profile_favorite_limit():
    """Verify favorites respect max limit"""
    profile = Profile("Test", "http://example.com")

    # Add many channels
    for i in range(200):
        channel = Channel(f"Channel{i}", f"http://stream{i}.url")
        profile.add_favorite(channel)

    # Should cap at max (currently no limit, but should add one)
    assert len(profile.favorites) <= 500  # Reasonable limit
```

**Step 4: Run tests**

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

### Test Coverage Goals

**Priority 1 - Critical Paths:**
- [ ] Profile serialization/deserialization
- [ ] ProfileManager CRUD operations
- [ ] DataLoader M3U parsing (various formats)
- [ ] Controller signal emissions
- [ ] Config save/load

**Priority 2 - Business Logic:**
- [ ] Favorites add/remove/update
- [ ] History tracking
- [ ] Search functionality
- [ ] Download filename generation

**Priority 3 - Error Handling:**
- [ ] Invalid M3U content
- [ ] Network failures
- [ ] Corrupt JSON files
- [ ] Invalid URLs

---

## High-Impact Improvements

### 🔴 CRITICAL - Fix Immediately

#### 1. Security: Hardcoded Credentials

**File:** `src/data/downloader.py:59-63`

**Issue:**
```python
# 🚨 SECURITY RISK - Credentials exposed in version control
download_mp4("http://worldiptv.me:8080/movie/fwNqqZfSrZWf/jAQCcnHh5rWr/121103.mkv", ...)
# Username: fwNqqZfSrZWf
# Password: jAQCcnHh5rWr
```

**Fix:**
```python
# Remove the hardcoded test code entirely
if __name__ == "__main__":
    # Example usage (no real credentials)
    # download_mp4("http://example.com/movie.mkv", "movie.mkv")
    print("Use this module by importing and calling download_mp4()")
```

**Verification:**
```bash
git diff src/data/downloader.py  # Ensure credentials removed
grep -r "worldiptv" src/  # Should return nothing
grep -r "jAQCcnHh5rWr" src/  # Should return nothing
```

#### 2. Crash: Windows-Only Code

**File:** `src/iptv_app.py:70-73`

**Issue:**
```python
# Crashes on Linux/macOS
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
```

**Fix:**
```python
# Platform-specific code with error handling
if sys.platform == "win32":
    try:
        import ctypes
        myappid = 'RoiAlfassi.IPTV-Saba.PC-Version.1.0.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as e:
        logger.warning(f"Failed to set Windows app user model ID: {e}")
```

**Verification:**
```bash
# On Linux or macOS:
python src/iptv_app.py  # Should not crash

# On Windows:
python src/iptv_app.py  # Should still work
```

#### 3. Bug: Merge Conflict in .gitignore

**File:** `.gitignore:5-13`

**Issue:**
```
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
```

**Fix:**
```bash
# Edit .gitignore and remove conflict markers
# Keep the desired ignore patterns from both sides
```

**Verification:**
```bash
cat .gitignore | grep "<<<<<<" | wc -l  # Should output: 0
```

### 🟡 HIGH IMPACT - Implement Soon

#### 4. Performance: UI Freezing on File I/O

**File:** `src/data/profile_manager.py:54-71`

**Issue:** Synchronous file writes block UI thread

**Current:**
```python
def save_profiles(self):
    # Blocks UI during disk write
    with open(self.profiles_file, 'w') as f:
        json.dump(data, f)
```

**Fix:**
```python
from PyQt5.QtCore import QTimer

class ProfileManager:
    def __init__(self):
        self.save_timer = None
        self.pending_save = False

    def queue_save(self, delay_ms=1000):
        """Debounced save - batches rapid updates"""
        self.pending_save = True
        if self.save_timer:
            self.save_timer.stop()
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self._do_save)
        self.save_timer.setSingleShot(True)
        self.save_timer.start(delay_ms)

    def _do_save(self):
        if self.pending_save:
            self.save_profiles()  # Actual save
            self.pending_save = False
```

**Verification:**
```python
# Rapid-fire favorites test
for i in range(50):
    controller.add_to_favorites(f"Channel{i}")
    # UI should remain responsive
    # Only 1 save should occur at the end (check file timestamp)
```

#### 5. Performance: Slow Channel Lookup

**File:** `src/controller/controller.py:196-212`

**Issue:** O(n*m) linear search through all groups/channels

**Current:**
```python
def find_channel_by_name(self, channel_name):
    for group in self.data_loader.groups.values():  # O(n)
        for channel in group.channels:  # O(m)
            if channel.name.lower() == channel_name.lower():
                return channel
```

**Fix:**
```python
# In DataLoader class
class DataLoader:
    def __init__(self):
        self._channel_index = {}  # name -> channel mapping

    def _build_index(self):
        """Build fast lookup index after loading"""
        self._channel_index = {}
        for group in self.groups.values():
            for channel in group.channels:
                key = channel.name.lower()
                self._channel_index[key] = channel

    def find_channel(self, name: str) -> Optional[Channel]:
        """O(1) lookup instead of O(n*m)"""
        return self._channel_index.get(name.lower())

# In Controller
def find_channel_by_name(self, channel_name):
    return self.data_loader.find_channel(channel_name)
```

**Verification:**
```python
import time

# Load large playlist (1000+ channels)
start = time.time()
for i in range(100):
    channel = controller.find_channel_by_name("CNN")
elapsed = time.time() - start

# Should be < 0.1 seconds for 100 lookups
assert elapsed < 0.1, f"Too slow: {elapsed}s"
```

#### 6. UX: No Progress Indicator for M3U Loading

**File:** `src/view/choose_channel_screen.py` (LoaderWorker)

**Issue:** Spinner shows but no percentage/channel count

**Fix:**
```python
# In DataLoader
class DataLoader:
    def load_from_url_streaming(self, url, progress_callback=None):
        # ... existing code ...

        # Add progress reporting
        if progress_callback and total_lines:
            progress_callback(lines_processed, total_lines)

# In LoaderWorker
class LoaderWorker(QObject):
    progress = pyqtSignal(int, int)  # current, total

    def run(self):
        def on_progress(current, total):
            self.progress.emit(current, total)

        self.controller.data_loader.load_from_url(
            url, progress_callback=on_progress
        )

# In View
def on_loading_progress(self, current, total):
    percentage = int((current / total) * 100)
    self.status_label.setText(f"Loading... {percentage}% ({current}/{total} channels)")
```

**Verification:**
```
1. Create profile with large M3U URL
2. Watch loading screen
3. Should see: "Loading... 45% (450/1000 channels)"
4. Updates should be smooth, not jumpy
```

### 🟢 MEDIUM IMPACT - Nice to Have

#### 7. Feature: Keyboard Shortcuts

**Files:** All view files

**Current:** Mouse-only interaction

**Fix:**
```python
# In each view class
def keyPressEvent(self, event):
    key = event.key()

    if key == Qt.Key_F:  # Fullscreen
        self.toggle_fullscreen()
    elif key == Qt.Key_Space:  # Play/Pause
        self.toggle_playback()
    elif key == Qt.Key_Escape:  # Exit fullscreen
        self.exit_fullscreen()
    elif key == Qt.Key_F1:  # Help
        self.show_help_dialog()
    elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
        self.increase_volume()
    elif event.key() == Qt.Key_Minus:
        self.decrease_volume()
    else:
        super().keyPressEvent(event)
```

**Verification:**
```
Manual test:
[ ] F key toggles fullscreen
[ ] Space pauses/plays
[ ] Esc exits fullscreen
[ ] +/- changes volume
[ ] F1 shows help (if implemented)
```

#### 8. Code Quality: Inconsistent Error Handling

**Files:** Multiple

**Issue:** Mix of `return None`, `return False`, exceptions, and signal emissions

**Fix - Standardize Pattern:**
```python
# Pattern: Operations raise exceptions, Controller catches and emits signals

# In Manager classes (data layer)
def create_profile(self, name: str, url: str) -> Profile:
    if name in self.profiles_dict:
        raise ValueError(f"Profile '{name}' already exists")
    if not self._validate_url(url):
        raise ValueError(f"Invalid URL: {url}")
    # ... create profile ...
    return profile

# In Controller
def create_profile(self, name: str, url: str):
    try:
        profile = self.profile_manager.create_profile(name, url)
        self.profiles_updated.emit()
        return True
    except ValueError as e:
        self.error_occurred.emit(str(e))
        return False
    except Exception as e:
        logger.exception("Unexpected error creating profile")
        self.error_occurred.emit(f"Failed to create profile: {e}")
        return False
```

**Verification:**
```python
# Test error cases
controller.error_occurred.connect(lambda msg: print(f"Error: {msg}"))

controller.create_profile("Test", "invalid-url")
# Should emit error signal: "Invalid URL: invalid-url"

controller.create_profile("Test", "http://valid.com/test.m3u")
# Should succeed

controller.create_profile("Test", "http://other.com/test.m3u")
# Should emit error signal: "Profile 'Test' already exists"
```

#### 9. Documentation: Add Docstrings

**Files:** Most Python files

**Issue:** Many methods lack docstrings

**Fix:**
```python
def add_to_favorites(self, channel_name: str) -> bool:
    """Add a channel to the active profile's favorites.

    Args:
        channel_name: Name of the channel to add (case-insensitive)

    Returns:
        True if added successfully, False if already in favorites or error

    Raises:
        ValueError: If no active profile is set

    Emits:
        profiles_updated: When favorite successfully added
        error_occurred: If operation fails

    Side Effects:
        - Updates active_profile.favorites
        - Saves profile to disk (profiles.json)
        - Emits profiles_updated signal

    Example:
        >>> controller.select_profile("User1")
        >>> controller.add_to_favorites("CNN")
        True
    """
    if not self.active_profile:
        raise ValueError("No active profile")
    # ... implementation ...
```

**Verification:**
```bash
# Generate documentation
pip install pydoc-markdown
pydoc-markdown > API_DOCS.md

# Or use built-in
python -m pydoc src.controller.controller
```

---

## Common Gotchas

### 1. VLC Player Black Screen

**Symptom:** Video plays in one screen, black screen in another

**Cause:** Created new player instance instead of reusing

**Fix:** Always pass existing player instance:
```python
# ✅ CORRECT
fullscreen = FullScreenView(self.player, self.vlc_instance)

# ❌ WRONG
fullscreen = FullScreenView()  # Creates new player → dual streams
```

### 2. Widget Window ID Not Valid

**Symptom:** VLC player attachment fails, no video

**Cause:** Tried to get `winId()` before widget shown

**Fix:** Attach in `showEvent()`:
```python
def showEvent(self, event):
    super().showEvent(event)
    if not self.player_attached:
        QTimer.singleShot(100, self.attach_player)  # Delay important!
```

### 3. Profile Changes Not Persisting

**Symptom:** Favorites/history lost on restart

**Cause:** Forgot to call `profile_manager.update_profile()` after changes

**Fix:**
```python
# After modifying profile
self.active_profile.add_favorite(channel)
self.profile_manager.update_profile(self.active_profile.name, self.active_profile)
```

### 4. UI Freezing

**Symptom:** Application becomes unresponsive during operations

**Cause:** Heavy operation on main thread (file I/O, network request)

**Fix:** Use QThread or Worker pattern:
```python
worker = LoaderWorker(controller)
thread = QThread()
worker.moveToThread(thread)
thread.started.connect(worker.run)
thread.start()
```

### 5. Signals Not Firing

**Symptom:** UI doesn't update after data changes

**Cause:** Forgot to emit signal or connection not made

**Fix:**
```python
# In Controller - ALWAYS emit after changes
def create_profile(self, name, url):
    # ... do work ...
    self.profiles_updated.emit()  # ← REQUIRED!

# In View - ALWAYS connect signals
controller.profiles_updated.connect(self.refresh_profile_list)
```

### 6. Module Import Errors

**Symptom:** `ImportError: cannot import name 'X' from 'Y'`

**Cause:** Incorrect import paths (mixing absolute/relative)

**Fix:** Use consistent import style:
```python
# ✅ CORRECT (from src/)
from controller.controller import Controller
from model.profile import Profile

# ❌ WRONG
from src.controller.controller import Controller  # Don't use 'src.'
```

### 7. Logging Not Working

**Symptom:** No log output or inconsistent logging

**Cause:** Multiple `logging.basicConfig()` calls (last one wins)

**Fix:** Configure logging ONCE in `iptv_app.py` main block:
```python
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    # Rest of app...
```

### 8. Platform-Specific Crashes

**Symptom:** Works on Windows, crashes on Linux/macOS

**Cause:** Platform-specific code without guards

**Fix:** Always check platform:
```python
import sys

if sys.platform == "win32":
    # Windows-only code
    pass
elif sys.platform.startswith("linux"):
    # Linux-only code
    pass
elif sys.platform == "darwin":
    # macOS-only code
    pass
```

### 9. File Path Issues

**Symptom:** Files not found on different platforms

**Cause:** Hardcoded path separators or relative paths

**Fix:** Use `pathlib.Path`:
```python
from pathlib import Path

# ✅ CORRECT
icon_path = Path(__file__).parent / "Assets" / "iptv-logo2.ico"

# ❌ WRONG
icon_path = "Assets/iptv-logo2.ico"  # Relative to CWD, not file
```

### 10. JSON Corruption

**Symptom:** `profiles.json` becomes invalid, data lost

**Cause:** Direct write without atomic operation

**Fix:** Use atomic write pattern:
```python
import tempfile
import os

# Write to temp file first
with tempfile.NamedTemporaryFile('w', delete=False, dir=os.path.dirname(target)) as tmp:
    json.dump(data, tmp, indent=2)
    tmp_path = tmp.name

# Atomic replace
os.replace(tmp_path, target)  # Atomic on POSIX, near-atomic on Windows
```

---

## Verification Procedures

### Pre-Commit Verification

**Run before every commit:**

```bash
# 1. Check for secrets
grep -r "password\|token\|secret\|api_key" src/ | grep -v "# Example"
# Should return nothing or only example comments

# 2. Check for merge conflicts
find . -name "*.py" -o -name "*.json" | xargs grep "<<<<<<< \|======= \|>>>>>>> "
# Should return nothing

# 3. Check for syntax errors
python -m py_compile src/**/*.py
# Should complete without errors

# 4. Run manual tests
python test_simple.py
python test_optimized_loader.py
# Both should pass

# 5. Test application launch
cd src && python iptv_app.py &
sleep 5
pkill -f iptv_app.py
# Should launch and close without errors
```

### Post-Change Verification Matrix

**Use this checklist after ANY code change:**

| Category | Test | Pass/Fail |
|----------|------|-----------|
| **Startup** | App launches without errors | ⬜ |
| | No new console errors/warnings | ⬜ |
| | Icon displays correctly | ⬜ |
| **Profiles** | Can create profile | ⬜ |
| | Can delete profile | ⬜ |
| | Can switch profiles | ⬜ |
| | Auto-login works (if enabled) | ⬜ |
| **Channels** | Channels load from M3U | ⬜ |
| | Search finds channels | ⬜ |
| | Category filter works | ⬜ |
| **Playback** | Channel plays video | ⬜ |
| | Fullscreen works | ⬜ |
| | Exit fullscreen works | ⬜ |
| | No black screen issues | ⬜ |
| | No dual audio (duplicate streams) | ⬜ |
| **Favorites** | Can add to favorites | ⬜ |
| | Can remove from favorites | ⬜ |
| | Favorites persist after restart | ⬜ |
| | Easy Mode shows only favorites | ⬜ |
| **History** | Watched channels tracked | ⬜ |
| | History persists after restart | ⬜ |
| **Performance** | UI remains responsive | ⬜ |
| | Large playlists load reasonably fast | ⬜ |
| | No memory leaks (run for 5+ minutes) | ⬜ |

### Performance Benchmarks

**Baseline performance targets:**

```bash
# 1. Startup time
time python src/iptv_app.py --version
# Target: < 2 seconds

# 2. Profile loading
# Time from selecting profile to channels displayed
# Target: < 5 seconds for cached data
# Target: < 30 seconds for 1000-channel M3U from network

# 3. Search responsiveness
# Time from typing to results appearing
# Target: < 500ms

# 4. Favorite add/remove
# Time from click to UI update
# Target: < 100ms (instant feel)

# 5. Memory usage
# Check with: ps aux | grep iptv_app
# Target: < 200MB for normal operation
```

### Integration Test Scenarios

**Complete user flows to test:**

#### Scenario 1: New User First Run
```
1. Launch app (first time, no profiles)
2. Create profile "TestUser" with M3U URL
3. Select profile
4. Wait for channels to load
5. Search for "news"
6. Click a news channel
7. Verify video plays
8. Add to favorites
9. Close app
10. Relaunch app
11. Verify auto-login to TestUser
12. Verify favorite still there
```

#### Scenario 2: Existing User Workflow
```
1. Launch app with existing profiles
2. Switch between profiles
3. Play channel from each profile
4. Add favorites to each profile
5. Use Easy Mode
6. Verify only favorites shown
7. Use search in multiple profiles
8. Exit and verify all data persists
```

#### Scenario 3: Error Recovery
```
1. Create profile with invalid URL
2. Verify error message shown
3. Create profile with valid URL
4. Disconnect internet
5. Try to reload channels
6. Verify cached data still works
7. Reconnect internet
8. Verify can refresh data
```

### Security Verification

**Check these after any security-related changes:**

```bash
# 1. No hardcoded credentials
git log -p | grep -i "password\|secret\|token\|api_key" | grep -v "example"

# 2. No SQL injection points (if adding database)
grep -r "execute.*%\|execute.*+\|execute.*format" src/

# 3. No command injection
grep -r "os\.system\|subprocess\.call.*shell=True" src/

# 4. No eval/exec
grep -r "eval\|exec" src/

# 5. HTTPS verification enabled
grep -r "verify=False" src/
# Should return nothing

# 6. Path traversal prevention
grep -r "open.*input\|Path.*input" src/
# Verify all user inputs are sanitized
```

---

## Safe Development Workflow

### Step-by-Step Process

#### 1. Before Starting

```bash
# 1. Update to latest
git fetch origin
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Run baseline tests
python test_simple.py
python test_optimized_loader.py
cd src && python iptv_app.py  # Manual smoke test
```

#### 2. During Development

```bash
# 1. Make small, atomic changes
# Don't mix refactoring with feature additions
# One logical change per commit

# 2. Test frequently
# After each change, run affected component manually

# 3. Commit often
git add src/specific/file.py
git commit -m "feat: add specific feature"

# 4. Keep commits focused
# Good: "fix: handle null channel in favorites"
# Bad: "fixed stuff and added features and refactored"
```

#### 3. Before Committing

```bash
# 1. Run verification checklist (see above)

# 2. Check diff
git diff --staged
# Review every line you're committing

# 3. Check for debug code
grep -r "print(.*DEBUG\|TODO\|FIXME\|console\.log" src/
# Remove or address before committing

# 4. Format commit message
git commit -m "type: concise description

Optional longer description explaining why this change
was necessary and what it accomplishes.

Fixes #123"
```

#### 4. Before Pushing

```bash
# 1. Squash WIP commits if needed
git rebase -i HEAD~5  # Interactive rebase last 5 commits

# 2. Run full test suite
python test_simple.py
python test_optimized_loader.py

# 3. Manual smoke test
cd src && python iptv_app.py
# Go through verification checklist

# 4. Push
git push origin feature/your-feature-name
```

### Code Review Checklist

**Use this when reviewing code (your own or others):**

- [ ] **Correctness**: Does it do what it's supposed to?
- [ ] **No Regressions**: All existing tests still pass
- [ ] **Thread Safety**: Shared data protected with locks
- [ ] **Error Handling**: All exceptions caught and handled
- [ ] **Signal Emissions**: UI will update correctly
- [ ] **Type Hints**: Function signatures have types
- [ ] **Docstrings**: Public methods documented
- [ ] **No Secrets**: No hardcoded credentials or keys
- [ ] **Platform Safety**: Platform-specific code guarded
- [ ] **Performance**: No obvious performance issues
- [ ] **Logging**: Appropriate log statements added
- [ ] **Comments**: Complex logic explained
- [ ] **No Dead Code**: Unused imports/variables removed
- [ ] **Backwards Compatible**: Old profiles.json still loads

### Rollback Procedure

**If something breaks in production:**

```bash
# 1. Identify last known good commit
git log --oneline

# 2. Create hotfix branch from last good commit
git checkout -b hotfix/rollback-bad-change <last-good-commit>

# 3. Verify it works
python test_simple.py
cd src && python iptv_app.py

# 4. Push hotfix
git push origin hotfix/rollback-bad-change

# 5. Investigate root cause
git diff <last-good-commit> <bad-commit>
```

---

## Additional Resources

### Essential Reading

| Document | Purpose |
|----------|---------|
| `CLAUDE.md` | Complete codebase reference for AI assistants |
| `README.md` | User-facing documentation |
| `OPTIMIZATION_DETAILS.md` | DataLoader performance optimization details |
| `FULLSCREEN_FIX_DETAILS.md` | VLC player attachment fix explanation |
| `DOWNLOAD_RECORD_FEATURE.md` | Download/record implementation details |

### Key External Documentation

- **PyQt5**: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- **python-vlc**: https://www.olivieraubert.net/vlc/python-ctypes/doc/
- **M3U Format**: https://en.wikipedia.org/wiki/M3U

### Getting Help

1. **Check existing docs** - Most patterns documented in CLAUDE.md
2. **Search code** - Similar patterns likely exist already
3. **Check git history** - See how similar issues were resolved
4. **Test incrementally** - Small changes easier to debug

---

## Summary: Golden Rules

1. **Test Before Changing** - Know what works before breaking it
2. **Change One Thing** - Atomic commits, focused changes
3. **Test After Changing** - Verify nothing broke
4. **Never Skip Verification** - Every change runs checklist
5. **Preserve Critical Paths** - Profile loading, M3U parsing, VLC player
6. **Emit Signals** - UI updates depend on them
7. **Lock Shared Data** - Thread safety is non-negotiable
8. **Handle Errors** - Never silent failures
9. **Document Decisions** - Future you will thank present you
10. **When in Doubt, Ask** - Better to clarify than break

---

**Last Updated:** 2025-11-21
**Target Audience:** LLMs and developers making improvements
**Maintainer:** See CLAUDE.md for codebase maintainer information

---

*Good luck, and happy coding! Remember: working software > perfect software.*
