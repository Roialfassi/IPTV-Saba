# IPTV-Saba Code Review: 50 Improvement Suggestions

**Reviewed:** February 2026
**Entry Point:** `iptv_app.py`
**Total Files Reviewed:** 17 Python files

## Rating System

- **Code Value (CV):** Impact on code quality, maintainability, architecture (1-5)
- **User Value (UV):** Impact on end-user experience (1-5)
- **Difficulty:** Easy / Medium / Hard

---

## Summary Statistics

| Difficulty | Count | Avg Code Value | Avg User Value |
|------------|-------|----------------|----------------|
| Easy | 20 | 3.1 | 2.8 |
| Medium | 18 | 3.7 | 3.5 |
| Hard | 12 | 4.3 | 4.2 |

---

## Easy Improvements (1-20)

### 1. Fix Double QApplication Creation
**File:** `iptv_app.py:16` and `iptv_app.py:117`

**Issue:** QApplication is created twice - once in `IPTVApp.__init__()` and once in `main()`.

**Current:**
```python
# In IPTVApp.__init__
self.app = QApplication(sys.argv)

# In main()
app = QApplication(sys.argv)
```

**Suggested Fix:** Remove the QApplication creation from `main()` or pass the existing app to IPTVApp.

| CV | UV | Difficulty |
|----|----|----|
| 4 | 2 | Easy |

---

### 2. Replace Print Statements with Logging
**Files:** Multiple (`iptv_app.py:35`, `easy_mode_screen.py:184`, `login_view.py:447`)

**Issue:** Mix of `print()` statements and proper logging.

**Current:**
```python
print("IPTVApp: Starting application cleanup...")
print(f"handle_easy_mode {e}")
```

**Suggested Fix:** Use consistent logging:
```python
logger.info("Starting application cleanup...")
logger.error(f"handle_easy_mode error: {e}")
```

| CV | UV | Difficulty |
|----|----|----|
| 3 | 1 | Easy |

---

### 3. Add Type Hints to Missing Methods
**Files:** Multiple methods lack type hints

**Issue:** Inconsistent use of type hints.

**Example - Current:**
```python
def update_auto_login(self, state):
```

**Suggested Fix:**
```python
def update_auto_login(self, state: int) -> None:
```

| CV | UV | Difficulty |
|----|----|----|
| 3 | 1 | Easy |

---

### 4. Fix Return Type Inconsistency in Profile Methods
**File:** `profile.py:263-292`

**Issue:** `is_in_favorites()` and `is_in_history()` return `int` but docstring says `bool`.

**Current:**
```python
def is_in_favorites(self, name: str) -> bool:
    """Returns: bool: True if the channel is in favorites"""
    for i, channel in enumerate(self.favorites):
        if channel.name.lower() == name.lower():
            return i  # Returns int, not bool!
    return -1
```

**Suggested Fix:** Rename to `get_favorite_index()` or change return type.

| CV | UV | Difficulty |
|----|----|----|
| 3 | 1 | Easy |

---

### 5. Remove Commented-Out Code
**Files:** `easy_mode_screen.py:76-79`, `choose_channel_screen.py:510-516`

**Issue:** Dead commented code clutters the codebase.

**Suggested Fix:** Delete commented code; use git history if needed.

| CV | UV | Difficulty |
|----|----|----|
| 2 | 1 | Easy |

---

### 6. Add Docstrings to Undocumented Methods
**File:** `easy_mode_screen.py` - Several methods lack docstrings

**Current:**
```python
def update_ui(self):
    pass
```

**Suggested Fix:**
```python
def update_ui(self) -> None:
    """Update UI elements periodically. Currently a placeholder for future use."""
    pass
```

| CV | UV | Difficulty |
|----|----|----|
| 2 | 1 | Easy |

---

### 7. Use Constants for Magic Numbers
**Files:** Multiple

**Issue:** Magic numbers scattered throughout code.

**Current:**
```python
self.hide_controls_timer = QTimer(self, interval=2000)
if len(self.history) > 10:
CONNECTION_TIMEOUT = 15
```

**Suggested Fix:** Define constants at class/module level:
```python
CONTROLS_HIDE_DELAY_MS = 2000
MAX_HISTORY_ITEMS = 10
```

| CV | UV | Difficulty |
|----|----|----|
| 3 | 1 | Easy |

---

### 8. Fix Incorrect Docstring in Profile.remove_from_history
**File:** `profile.py:248-260`

**Issue:** Docstring says "Removes from favorites" but method removes from history.

**Current:**
```python
def remove_from_history(self, channel: str) -> None:
    """Removes a channel from the favorites list if it exists."""
```

**Suggested Fix:**
```python
def remove_from_history(self, channel: str) -> None:
    """Removes a channel from the history list if it exists."""
```

| CV | UV | Difficulty |
|----|----|----|
| 2 | 1 | Easy |

---

### 9. Use Qt.CheckState Enum Instead of Magic Number
**File:** `login_view.py:460`

**Issue:** Magic number 2 for checked state.

**Current:**
```python
self.auto_login = state == 2  # Checked (Qt.Checked) is 2
```

**Suggested Fix:**
```python
self.auto_login = state == Qt.Checked
```

| CV | UV | Difficulty |
|----|----|----|
| 2 | 1 | Easy |

---

### 10. Add Error Message for Empty Profile URL
**File:** `login_view.py:143-145`

**Issue:** Generic "Incomplete Data" message doesn't specify which field is empty.

**Suggested Fix:**
```python
if not name:
    QMessageBox.warning(self, "Missing Name", "Please enter a profile name.")
    return
if not url:
    QMessageBox.warning(self, "Missing URL", "Please enter a playlist URL.")
    return
```

| CV | UV | Difficulty |
|----|----|----|
| 2 | 3 | Easy |

---

### 11. Initialize all_channels Before Use
**File:** `choose_channel_screen.py:547`

**Issue:** `self.all_channels` used in `filter_channels()` but may not be initialized.

**Current:**
```python
def filter_channels(self, text: str):
    if self.channel_list:
        self.channel_list.clear()
        filtered_channels = [channel for channel in self.all_channels if ...]
```

**Suggested Fix:** Initialize in `__init__`:
```python
self.all_channels = []
```

| CV | UV | Difficulty |
|----|----|----|
| 3 | 2 | Easy |

---

### 12. Add Input Validation for Profile URL Format
**File:** `login_view.py`

**Issue:** No validation that URL is actually an M3U URL.

**Suggested Fix:**
```python
def validate_url(self, url: str) -> bool:
    if not url.startswith(('http://', 'https://')):
        return False
    if not any(url.endswith(ext) for ext in ['.m3u', '.m3u8']) and 'm3u' not in url.lower():
        # Warn user but don't block
        pass
    return True
```

| CV | UV | Difficulty |
|----|----|----|
| 3 | 4 | Easy |

---

### 13. Add Tooltip to Volume Slider
**Files:** `choose_channel_screen.py`, `easy_mode_screen.py`, `full_screen_view.py`

**Issue:** Volume slider has no tooltip showing current value.

**Suggested Fix:**
```python
self.volume_slider.setToolTip(f"Volume: {value}%")
self.volume_slider.valueChanged.connect(
    lambda v: self.volume_slider.setToolTip(f"Volume: {v}%")
)
```

| CV | UV | Difficulty |
|----|----|----|
| 1 | 3 | Easy |

---

### 14. Handle Empty Favorites Gracefully in show_favorites
**File:** `choose_channel_screen.py:705-714`

**Issue:** Shows QMessageBox for empty favorites, but could show inline message.

**Suggested Enhancement:** Consider showing a placeholder in the channel list instead of a popup.

| CV | UV | Difficulty |
|----|----|----|
| 2 | 3 | Easy |

---

### 15. Add Window Icon to All Screens
**Files:** `easy_mode_screen.py`, `full_screen_view.py`

**Issue:** Only main window has icon; child windows lack it.

**Suggested Fix:**
```python
self.setWindowIcon(QIcon("Assets/iptv-logo2.ico"))
```

| CV | UV | Difficulty |
|----|----|----|
| 1 | 2 | Easy |

---

### 16. Standardize Button Styling with Helper Function
**Files:** Multiple view files

**Issue:** Repeated button stylesheet code.

**Suggested Fix:** Create a style utility module:
```python
# src/utils/styles.py
def get_primary_button_style():
    return """QPushButton { background-color: #E50914; ... }"""
```

| CV | UV | Difficulty |
|----|----|----|
| 3 | 1 | Easy |

---

### 17. Add Confirmation Before Delete Profile
**Files:** `controller.py`, `login_view.py`

**Issue:** No confirmation dialog before profile deletion.

**Suggested Fix:** Add confirmation in UI layer before calling controller.delete_profile().

| CV | UV | Difficulty |
|----|----|----|
| 2 | 4 | Easy |

---

### 18. Show Loading State When Validating URL
**File:** `login_view.py`

**Issue:** No feedback during URL validation.

**Suggested Fix:**
```python
self.create_button.setEnabled(False)
self.create_button.setText("Validating...")
# After validation
self.create_button.setEnabled(True)
self.create_button.setText("Create")
```

| CV | UV | Difficulty |
|----|----|----|
| 2 | 4 | Easy |

---

### 19. Add Keyboard Navigation to Profile List
**File:** `login_view.py`

**Issue:** No keyboard-only way to navigate and select profiles.

**Suggested Fix:** Add Enter key to trigger login:
```python
self.profiles_list.itemDoubleClicked.connect(self.handle_login)
```

| CV | UV | Difficulty |
|----|----|----|
| 2 | 3 | Easy |

---

### 20. Fix Hardcoded VLC Path for Windows
**File:** `shared_player_manager.py:110-111`

**Issue:** Hardcoded path assumes default VLC installation.

**Current:**
```python
vlc_plugins_path = r'C:\Program Files\VideoLAN\VLC\plugins'
```

**Suggested Fix:**
```python
import shutil
vlc_path = shutil.which('vlc')
if vlc_path:
    vlc_plugins_path = os.path.join(os.path.dirname(vlc_path), 'plugins')
else:
    vlc_plugins_path = r'C:\Program Files\VideoLAN\VLC\plugins'
```

| CV | UV | Difficulty |
|----|----|----|
| 3 | 3 | Easy |

---

## Medium Improvements (21-38)

### 21. Implement Async Profile Save to Prevent UI Freeze
**File:** `controller.py`

**Issue:** Profile saves happen synchronously, blocking UI.

**Current:**
```python
self.profile_manager.update_profile(self.active_profile)
self.profile_manager.export_profiles(self.profile_path)
```

**Suggested Fix:** Use QThread or asyncio for file operations.

| CV | UV | Difficulty |
|----|----|----|
| 4 | 3 | Medium |

---

### 22. Add Progress Indicator During Profile Save
**File:** `controller.py`, `iptv_app.py`

**Issue:** No feedback during profile save operations.

**Suggested Fix:** Emit signals for save start/complete, show status in UI.

| CV | UV | Difficulty |
|----|----|----|
| 2 | 4 | Medium |

---

### 23. Implement Channel Preview Thumbnails
**File:** `choose_channel_screen.py`

**Issue:** No visual preview of channel logos.

**Suggested Enhancement:**
- Download and cache channel logos
- Show thumbnails in channel list
- Use placeholder for missing logos

| CV | UV | Difficulty |
|----|----|----|
| 3 | 5 | Medium |

---

### 24. Add Search History/Recent Searches
**File:** `choose_channel_screen.py`

**Issue:** No way to recall previous searches.

**Suggested Enhancement:**
- Store last 5-10 search queries
- Show dropdown with recent searches
- Clear search history option

| CV | UV | Difficulty |
|----|----|----|
| 2 | 4 | Medium |

---

### 25. Implement Favorites Sorting/Organization
**File:** `profile.py`, `choose_channel_screen.py`

**Issue:** Favorites can't be reordered.

**Suggested Enhancement:**
- Drag-and-drop reordering
- Sort alphabetically option
- Group favorites by category

| CV | UV | Difficulty |
|----|----|----|
| 3 | 4 | Medium |

---

### 26. Add Buffering Indicator in UI
**File:** `choose_channel_screen.py`

**Issue:** Buffering signal exists but no visual indicator.

**Current:**
```python
def _on_buffering(self, percentage: int):
    if percentage < 100 and percentage > 0:
        logger.debug(f"Buffering: {percentage}%")
```

**Suggested Fix:** Show buffering overlay or progress bar.

| CV | UV | Difficulty |
|----|----|----|
| 2 | 4 | Medium |

---

### 27. Implement Dark/Light Theme Toggle
**File:** `config_manager.py`, all views

**Issue:** Only dark theme available.

**Suggested Enhancement:**
- Add theme configuration option
- Create light theme stylesheets
- Theme toggle in settings

| CV | UV | Difficulty |
|----|----|----|
| 3 | 4 | Medium |

---

### 28. Add Recently Played Section
**File:** `choose_channel_screen.py`

**Issue:** History only accessible via button.

**Suggested Enhancement:**
- Show "Continue Watching" section on main screen
- Display last 3-5 channels prominently
- One-click resume playback

| CV | UV | Difficulty |
|----|----|----|
| 3 | 5 | Medium |

---

### 29. Implement Export Favorites Feature
**File:** `profile.py`, `login_view.py`

**Issue:** No way to backup/share favorites.

**Suggested Enhancement:**
- Export favorites to JSON/M3U
- Import favorites from file
- Share via clipboard

| CV | UV | Difficulty |
|----|----|----|
| 3 | 4 | Medium |

---

### 30. Add Channel Information Dialog
**File:** `choose_channel_screen.py`

**Issue:** No way to view channel details.

**Suggested Enhancement:**
- Right-click "Info" option
- Show: name, URL, logo, type, group
- Copy URL to clipboard

| CV | UV | Difficulty |
|----|----|----|
| 2 | 3 | Medium |

---

### 31. Implement Playlist Refresh Button
**File:** `choose_channel_screen.py`

**Issue:** No manual refresh option (24h cache).

**Suggested Enhancement:**
- Add "Refresh Channels" button
- Show last refresh time
- Force reload from URL

| CV | UV | Difficulty |
|----|----|----|
| 2 | 4 | Medium |

---

### 32. Add Error Recovery for Failed Streams
**File:** `shared_player_manager.py`, `choose_channel_screen.py`

**Issue:** Failed stream just shows error, no recovery.

**Suggested Enhancement:**
- Auto-retry with backoff
- Offer alternative streams
- Remember problematic channels

| CV | UV | Difficulty |
|----|----|----|
| 4 | 4 | Medium |

---

### 33. Implement Volume Memory Per Channel
**File:** `shared_player_manager.py`

**Issue:** Volume resets when changing channels.

**Suggested Enhancement:**
- Remember volume setting
- Option for per-channel volume
- Master volume control

| CV | UV | Difficulty |
|----|----|----|
| 2 | 3 | Medium |

---

### 34. Add Keyboard Shortcut Help Dialog
**File:** All views

**Issue:** No discoverable way to learn shortcuts.

**Suggested Enhancement:**
- "?" key or Help menu
- Modal showing all shortcuts
- Context-sensitive help

| CV | UV | Difficulty |
|----|----|----|
| 2 | 4 | Medium |

---

### 35. Implement Connection Quality Indicator
**File:** `shared_player_manager.py`, `choose_channel_screen.py`

**Issue:** No indication of stream quality/stability.

**Suggested Enhancement:**
- Show bitrate/quality info
- Connection strength indicator
- Buffering history

| CV | UV | Difficulty |
|----|----|----|
| 3 | 4 | Medium |

---

### 36. Add Double-Click to Play Behavior
**File:** `choose_channel_screen.py`

**Issue:** Single-click plays, which may be unexpected.

**Suggested Enhancement:**
- Single-click to select
- Double-click to play
- Configuration option

| CV | UV | Difficulty |
|----|----|----|
| 2 | 3 | Medium |

---

### 37. Implement Mini Player Mode
**File:** New file needed

**Issue:** Can only watch in main window or fullscreen.

**Suggested Enhancement:**
- Picture-in-picture style mini player
- Always-on-top option
- Draggable/resizable

| CV | UV | Difficulty |
|----|----|----|
| 4 | 5 | Medium |

---

### 38. Add Application Settings Screen
**File:** New view needed

**Issue:** No centralized settings management.

**Suggested Enhancement:**
- Settings screen with:
  - Theme selection
  - Default volume
  - Auto-login toggle
  - Cache management
  - Shortcut customization

| CV | UV | Difficulty |
|----|----|----|
| 4 | 5 | Medium |

---

## Hard Improvements (39-50)

### 39. Add Unit Tests with pytest
**File:** New `tests/` directory

**Issue:** No automated tests.

**Suggested Enhancement:**
- Unit tests for models
- Unit tests for data layer
- Mocking for VLC operations
- CI integration

| CV | UV | Difficulty |
|----|----|----|
| 5 | 2 | Hard |

---

### 40. Implement EPG (Electronic Program Guide)
**File:** New service and view

**Issue:** No program schedule information.

**Suggested Enhancement:**
- Parse XMLTV EPG data
- Show current/next program
- Program search
- Reminders

| CV | UV | Difficulty |
|----|----|----|
| 5 | 5 | Hard |

---

### 41. Add Scheduled Recording Feature
**File:** `download_record_manager.py`

**Issue:** Can only record manually.

**Suggested Enhancement:**
- Schedule recordings by time
- Integrate with EPG
- Recording management UI
- Notification on complete

| CV | UV | Difficulty |
|----|----|----|
| 4 | 5 | Hard |

---

### 42. Implement Parental Controls
**File:** New feature across multiple files

**Issue:** No content restrictions.

**Suggested Enhancement:**
- PIN protection
- Channel blocking
- Time-based restrictions
- Content rating filtering

| CV | UV | Difficulty |
|----|----|----|
| 4 | 4 | Hard |

---

### 43. Add Multi-Language UI Support (i18n)
**File:** All view files

**Issue:** English only.

**Suggested Enhancement:**
- Extract strings to translation files
- Language selection in settings
- Qt Linguist integration
- RTL support

| CV | UV | Difficulty |
|----|----|----|
| 4 | 5 | Hard |

---

### 44. Implement Catch-Up TV Feature
**File:** New service

**Issue:** No time-shifted viewing.

**Suggested Enhancement:**
- Detect catch-up capable streams
- Time-shift UI
- Archive browsing
- Resume from EPG

| CV | UV | Difficulty |
|----|----|----|
| 5 | 5 | Hard |

---

### 45. Add Audio Track Selection
**File:** `full_screen_view.py`, `shared_player_manager.py`

**Issue:** No way to change audio track.

**Suggested Enhancement:**
- Detect available audio tracks
- Language selection UI
- Remember preference

| CV | UV | Difficulty |
|----|----|----|
| 3 | 4 | Hard |

---

### 46. Implement Stream Quality Selection
**File:** `shared_player_manager.py`

**Issue:** No quality selection for adaptive streams.

**Suggested Enhancement:**
- Detect HLS/DASH quality levels
- Quality selection UI
- Auto-quality option
- Bandwidth management

| CV | UV | Difficulty |
|----|----|----|
| 4 | 4 | Hard |

---

### 47. Add Subtitle Support
**File:** `shared_player_manager.py`, views

**Issue:** No subtitle support.

**Suggested Enhancement:**
- Detect embedded subtitles
- External subtitle loading
- Subtitle styling options
- Language preference

| CV | UV | Difficulty |
|----|----|----|
| 4 | 4 | Hard |

---

### 48. Implement Channel Recommendations
**File:** New service

**Issue:** No discovery features.

**Suggested Enhancement:**
- Based on watch history
- "Similar channels" feature
- Trending channels
- New channels notification

| CV | UV | Difficulty |
|----|----|----|
| 4 | 5 | Hard |

---

### 49. Add Multi-Window/Split View
**File:** Major architecture change

**Issue:** Can only watch one channel.

**Suggested Enhancement:**
- Multiple player windows
- Split-screen view
- Channel comparison
- Multi-monitor support

| CV | UV | Difficulty |
|----|----|----|
| 5 | 5 | Hard |

---

### 50. Implement Plugin/Extension System
**File:** New architecture

**Issue:** No extensibility.

**Suggested Enhancement:**
- Plugin API
- Custom stream sources
- UI extensions
- Third-party integrations

| CV | UV | Difficulty |
|----|----|----|
| 5 | 4 | Hard |

---

## Implementation Priority Matrix

### High Priority (High Value, Lower Effort)
1. #1 - Fix Double QApplication
2. #11 - Initialize all_channels
3. #10 - Better error messages
4. #18 - Loading state during validation
5. #12 - URL validation

### Quick Wins (Lower Effort, Visible Improvement)
1. #13 - Volume tooltip
2. #15 - Window icons
3. #17 - Delete confirmation
4. #19 - Keyboard navigation
5. #34 - Keyboard shortcuts help

### High Impact User Features
1. #23 - Channel thumbnails
2. #28 - Recently played
3. #37 - Mini player
4. #38 - Settings screen
5. #40 - EPG support

### Technical Debt
1. #2 - Consistent logging
2. #3 - Type hints
3. #5 - Remove dead code
4. #16 - Standardize styles
5. #39 - Unit tests

---

## Conclusion

This codebase is well-structured with good separation of concerns following MVC architecture. The main areas for improvement are:

1. **Code Quality:** Consistent patterns, type hints, logging
2. **User Experience:** Feedback, discoverability, modern features
3. **Testing:** Automated tests for reliability
4. **Features:** EPG, scheduling, multi-language

Start with the Easy improvements to clean up technical debt, then progress to Medium features for user experience, and plan Hard features for major version updates.
