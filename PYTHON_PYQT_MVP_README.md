# IPTV App MVP - Python & PyQt6 Edition

This document serves as a comprehensive guide and development plan to replicate the "IPTV-Saba" Netflix-style application using **Python** and **PyQt6 (or PySide6)**. It is designed to be a "master prompt" for an LLM to generate the entire codebase effectively.

## 1. Project Overview
**Goal**: Build a cross-platform (Windows/Linux/macOS) IPTV player with a modern, Netflix-inspired dark UI.
**Core Features**:
-   **Profile Management**: Multiple user profiles with persistent settings.
-   **M3U Playlist Sync**: Download, parse, and categorize M3U playlists into Live TV, Movies, and Series.
-   **Media Player**: Integrated video player with custom controls and fullscreen support.
-   **Content Dashboard**: Categorized views with poster grids and metadata.

## 2. Technology Stack
-   **Language**: Python 3.10+
-   **UI Framework**: [PyQt6](https://pypi.org/project/PyQt6/) (Industry standard for Python desktop apps).
-   **Database**: `SQLAlchemy` (ORM) with `sqlite3`.
-   **Video Player**: `python-mpv` (libmpv wrapper) or `vlc`. *Recommendation: `python-mpv` for best performance and codec support, or `QMediaPlayer` if strictly sticking to Qt (though codecs can be an issue).*
-   **Network**: `requests` (for downloading M3U files).
-   **Concurrency**: `QThread` (Qt's native threading) to keep the UI responsive during sync.
-   **Styling**: `QSS` (Qt Style Sheets) - CSS-like styling for widgets.

## 3. Architecture & Folder Structure
Follow a clean MVC pattern:

```text
iptv_pyqt/
├── main.py                # Entry point, QApplication setup
├── config.py              # Constants, Theme colors (Dark Palette)
├── database/
│   ├── __init__.py
│   ├── db.py              # SQLAlchemy engine & session setup
│   └── models.py          # Models: Profile, M3USource, Channel
├── workers/
│   └── sync_worker.py     # QThread for M3U downloading/parsing
├── ui/
│   ├── main_window.py     # QMainWindow container
│   ├── styles.qss         # Global stylesheet
│   ├── screens/
│   │   ├── profile_select.py
│   │   ├── home.py
│   │   ├── player.py
│   │   └── settings.py
│   └── widgets/
│       ├── movie_card.py
│       └── sidebar.py
└── assets/                # Icons, Images
```

## 4. Database Schema (SQLAlchemy)
Same robust schema as the web version:

### `Profile`
-   `id` (Integer, PK)
-   `name` (String)
-   `avatar_color` (String)
-   `is_active` (Boolean)

### `M3USource`
-   `id` (Integer, PK)
-   `profile_id` (FK -> Profile)
-   `url` (String)
-   `last_synced` (DateTime)

### `Channel`
-   `id` (PK)
-   `source_id` (FK)
-   `tvg_id`, `tvg_name`, `logo_url`
-   `group_title`
-   `stream_url`
-   `content_type` (LIVE, MOVIE, SERIES)
-   `metadata` (JSON)

## 5. Development Plan (LLM Prompt Instructions)

**Instruction to LLM**: "Execute this plan step-by-step. Use PyQt6. Ensure the UI is styled with a dark theme using QSS."

### Phase 1: Foundation & Database
1.  **Setup**: Initialize `main.py` with `QApplication`. Apply a global dark stylesheet (background `#141414`, text `#FFFFFF`, accent `#E50914`).
2.  **Database**: Create `database/models.py` using SQLAlchemy. Setup the SQLite connection in `database/db.py`.

### Phase 2: Profile Management
1.  **Profile Screen**: Create `ui/screens/profile_select.py`.
    -   Use `QGridLayout` to show circular profile avatars (styled `QPushButton` with `border-radius`).
    -   "Add Profile" button opens a `QInputDialog`.
    -   Clicking a profile updates the global state and switches the `QStackedWidget` to the Main Dashboard.

### Phase 3: M3U Sync Engine (QThread)
1.  **Worker**: Create `workers/sync_worker.py` inheriting from `QThread`.
    -   Signals: `progress(int)`, `finished()`, `error(str)`.
    -   **Logic**: Download M3U -> Parse Regex -> Bulk Insert into DB.
    -   *Regex*: Same robust regex as before.

### Phase 4: Main Dashboard (Netflix Style)
1.  **Layout**: Use a `QMainWindow` with a `QSplitter` or `QHBoxLayout`.
    -   **Left**: Collapsible Sidebar (`ui/widgets/sidebar.py`) with icons (Home, Live, Movies, Series, Settings).
    -   **Right**: `QStackedWidget` for content pages.
2.  **Content Pages**:
    -   Use `QScrollArea` containing a `QGridLayout` for posters.
    -   **Lazy Loading**: For performance with 20k+ items, implement a custom "Flow Layout" or use pagination logic (fetch 50 items at a time).

### Phase 5: Video Player
1.  **Integration**: Use `python-mpv` linked to a `QFrame` widget ID.
    -   *Alternative*: `QMediaPlayer` with `QVideoWidget` if MPV is too complex to setup cross-platform via script.
2.  **Controls**: Create a custom control bar overlay (Play, Pause, Slider, Volume, Fullscreen Toggle).
    -   **Fullscreen**: `window.showFullScreen()` / `window.showNormal()`.

### Phase 6: Settings & Wiring
1.  **Settings Page**: Input field for M3U URL. "Sync" button starts the `SyncWorker`.
2.  **Navigation**: Connect Sidebar buttons to `QStackedWidget` index changes.

## 6. "One-Shot" Prompt for LLM
*Copy and paste this into an LLM to generate the core:*

> "Act as a Senior Python Developer specialized in PyQt6. Build a modern desktop IPTV application.
>
> **Requirements**:
> 1.  **Tech Stack**: Python 3.10, PyQt6, SQLAlchemy (SQLite).
> 2.  **Design**: Netflix-inspired Dark Mode. Use QSS for styling (red accent, dark grey backgrounds).
> 3.  **Features**:
>     -   **Profile Selection**: Start screen to choose/create user profiles.
>     -   **M3U Sync**: 'Settings' tab to input M3U URL. Parse and save to DB in a background `QThread` to keep UI responsive.
>     -   **Dashboard**: Tabs for Live TV, Movies, Series. Display content in a responsive Grid Layout inside a Scroll Area.
>     -   **Player**: Click a poster to play video using `QMediaPlayer` or `mpv`. Custom overlay controls.
> 4.  **Structure**: Modular (MVC pattern).
>
> Provide the complete file structure and code for a functional MVP."
