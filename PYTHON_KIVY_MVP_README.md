# IPTV App MVP - Python & Kivy Edition

This document serves as a comprehensive guide and development plan to replicate the "IPTV-Saba" Netflix-style application using **Python** and **Kivy (KivyMD)**. It is designed to be a "master prompt" for an LLM to generate the entire codebase effectively.

## 1. Project Overview
**Goal**: Build a cross-platform (Windows/Linux/Android) IPTV player with a modern, Netflix-inspired dark UI.
**Core Features**:
-   **Profile Management**: Multiple user profiles with persistent settings.
-   **M3U Playlist Sync**: Download, parse, and categorize M3U playlists into Live TV, Movies, and Series.
-   **Media Player**: Integrated video player with custom controls and fullscreen support.
-   **Content Dashboard**: Categorized views with poster grids and metadata.

## 2. Technology Stack
-   **Language**: Python 3.10+
-   **UI Framework**: [KivyMD](https://kivymd.readthedocs.io/) (Material Design components for Kivy).
-   **Database**: `sqlite3` (Native Python) or `SQLAlchemy` (ORM). *Recommendation: SQLAlchemy for cleaner model definitions.*
-   **Video Player**: `kivy-media` or `ffpyplayer` (via `Video` widget).
-   **Network**: `requests` (for downloading M3U files).
-   **Async Processing**: `threading` or `asyncio` (Kivy is event loop based, so threading is often easier for heavy parsing tasks to avoid freezing UI).

## 3. Architecture & Folder Structure
Follow a modular MVC-like structure:

```text
iptv_kivy/
├── main.py                # Entry point, App class
├── config.py              # Constants, Theme colors
├── database/
│   ├── __init__.py
│   ├── db.py              # Database connection & session
│   └── models.py          # SQLAlchemy models (Profile, Source, Channel, etc.)
├── services/
│   ├── m3u_parser.py      # Regex logic for parsing M3U
│   └── sync_service.py    # Background thread for syncing
├── ui/
│   ├── screens/
│   │   ├── profile_select.py
│   │   ├── home.py
│   │   ├── player.py
│   │   └── settings.py
│   └── widgets/
│       ├── movie_card.py
│       └── channel_item.py
└── assets/                # Fonts, Icons, Images
```

## 4. Database Schema (SQLAlchemy)

### `Profile`
-   `id` (UUID/Integer, PK)
-   `name` (String)
-   `avatar_color` (String/Hex)
-   `is_active` (Boolean)

### `M3USource`
-   `id` (UUID/Integer, PK)
-   `profile_id` (FK -> Profile)
-   `url` (String)
-   `name` (String)
-   `last_synced` (DateTime)

### `Channel` (Polymorphic or Single Table with Type)
-   `id` (PK)
-   `source_id` (FK -> M3USource)
-   `tvg_id`, `tvg_name`, `tvg_logo`
-   `group_title` (Category)
-   `url` (Stream URL)
-   `content_type` (Enum: LIVE, MOVIE, SERIES_EPISODE)
-   `metadata` (JSON: Year, Season, Episode, etc.)

## 5. Development Plan (LLM Prompt Instructions)

**Instruction to LLM**: "Execute this plan step-by-step. Ensure all code is robust, error-handled, and follows PEP 8."

### Phase 1: Foundation & Database
1.  **Initialize Project**: Create `main.py` with a basic `MDApp` from KivyMD. Set theme to 'Dark', primary palette 'Red' (Netflix style).
2.  **Database Setup**: Implement `database/models.py`. Define `Profile`, `M3USource`, and `Channel` classes using SQLAlchemy declarative base.
3.  **DB Manager**: Create `database/db.py` to handle `engine` creation and `Session` management.

### Phase 2: Profile Management System
1.  **Profile Screen**: Create `ui/screens/profile_select.py`.
    -   Display a grid of circular avatars.
    -   "Add Profile" button that opens a dialog (MDDialog) to enter a name.
    -   Clicking a profile sets it as "Active" in a global `AppState` or `App.get_running_app().active_profile` and navigates to `Home`.
2.  **CRUD Logic**: Implement methods to `create_profile`, `get_all_profiles`, and `delete_profile` in a `ProfileService`.

### Phase 3: M3U Parsing & Sync Logic
1.  **Parser**: Port the regex logic from the TypeScript version to Python in `services/m3u_parser.py`.
    -   *Regex*: `#EXTINF:-1\s*(?:tvg-id="([^"]*)")?\s*(?:tvg-name="([^"]*)")?\s*(?:tvg-logo="([^"]*)")?\s*(?:group-title="([^"]*)")?,\s*(.*)`
2.  **Sync Service**: Create `services/sync_service.py`.
    -   Function `sync_source(source_id)`:
        -   Fetch URL using `requests`.
        -   Parse content.
        -   **Bulk Insert**: Use SQLAlchemy's `bulk_save_objects` or Core Insert for performance (critical for 20k+ channels).
        -   Run this in a `threading.Thread` to prevent UI freeze.

### Phase 4: Main UI (The "Netflix" Look)
1.  **Layout**: Use `MDBottomNavigation` for tabs: "Home", "Live TV", "Movies", "Series", "Settings".
2.  **Home Screen**:
    -   "Continue Watching" row (horizontal ScrollView).
    -   "Recently Added Movies" row.
3.  **Grid Views**: For Movies/Series, use `MDGridLayout` inside a `ScrollView`. Create a custom `MovieCard` widget (AsyncImage + Label).

### Phase 5: Video Player
1.  **Player Screen**: Create `ui/screens/player.py`.
2.  **Implementation**: Use Kivy's `Video` widget.
    -   Overlay custom controls (Play/Pause, Seek Bar `MDSlider`, Volume).
    -   **Fullscreen**: Toggle window fullscreen using `Window.fullscreen = 'auto'`.
    -   **Error Handling**: Handle stream failures gracefully (toast message).

### Phase 6: Wiring It All Together
1.  **Settings Screen**: Add UI to input M3U URL.
    -   "Add Source" button triggers `sync_service`.
    -   Show a `MDSpinner` while syncing.
2.  **Navigation**: Ensure back buttons work (Android hardware back button handling via `Window.bind(on_keyboard=...)`).

## 6. "One-Shot" Prompt for LLM
*Copy and paste this into an LLM to generate the core:*

> "Act as a Senior Python Developer. Build a KivyMD application for IPTV.
>
> **Requirements**:
> 1.  **Database**: Use SQLAlchemy with SQLite. Create models for `Profile`, `M3USource`, and `Channel`.
> 2.  **UI**: Dark theme, Netflix-red accent.
>     -   **Screen 1**: Profile Selection (Grid of avatars).
>     -   **Screen 2**: Main Dashboard with Bottom Navigation (Live, Movies, Series).
>     -   **Screen 3**: Video Player with custom controls.
> 3.  **Logic**:
>     -   On 'Settings' tab, allow adding an M3U URL.
>     -   Download and parse the M3U (use regex) in a background thread.
>     -   Save channels to DB.
>     -   Display channels in the respective tabs using a RecyleView for performance.
> 4.  **Code Structure**: Modular (main.py, models.py, screens/, services/).
>
> Provide the complete file structure and code for a functional MVP."
