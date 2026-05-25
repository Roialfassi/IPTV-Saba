import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QLabel, QListWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QSlider, QMessageBox, QSplitter,
    QApplication, QSizePolicy, QMenu, QAction, QGraphicsOpacityEffect,
    QComboBox, QFileDialog, QFrame, QListWidgetItem, QStackedLayout,
    QTabBar
)
from PyQt5.QtCore import Qt, pyqtSlot, QObject, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QThread
from PyQt5.QtGui import QFont, QIcon, QColor
import vlc

from src.controller.controller import Controller
from src.data.data_loader import DataLoader
from src.model.group_model import Group
from src.model.channel_model import Channel
from src.model.profile import create_mock_profile, Profile
from src.view.full_screen_view import FullScreenView
from src.services.download_record_manager import DownloadRecordManager
from src.services.shared_player_manager import SharedPlayerManager, get_shared_player
from src.view.retry_overlay import RetryOverlay
from src.view.schedule_dialog import ScheduleRecordingDialog
from src.view.downloads_panel import DownloadsPanel
from src.services.schedule_manager import ScheduleManager
from src.services.recording_scheduler import RecordingScheduler
from src.utils.resource_path import resource_path

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

WINDOW_ICON_PATH = resource_path("Assets/iptv-logo2.ico")
MAX_DISPLAY_CHANNELS = 200  # Cap channel list display for performance

# ============================================================
#  Compact icon-style button factory
# ============================================================
_ICON_BTN = """
    QPushButton {{
        background: {bg};
        color: #fff;
        border: none;
        border-radius: {rad}px;
        font-size: {fs}px;
        font-weight: 700;
        padding: {pad};
        min-width: {mw}px;
        min-height: {mh}px;
    }}
    QPushButton:hover {{ background: {hover}; }}
    QPushButton:pressed {{ background: {pressed}; }}
    QPushButton:disabled {{ background: #333; color: #666; }}
"""

def _icon_btn(text, tooltip, bg="#E50914", hover="#F6121D", pressed="#b00710",
              rad=6, fs=14, pad="4px 10px", mw=32, mh=28):
    b = QPushButton(text)
    b.setToolTip(tooltip)
    b.setCursor(Qt.PointingHandCursor)
    b.setStyleSheet(_ICON_BTN.format(
        bg=bg, hover=hover, pressed=pressed,
        rad=rad, fs=fs, pad=pad, mw=mw, mh=mh))
    return b

def _combo(tooltip, min_w=90):
    c = QComboBox()
    c.setMinimumWidth(min_w)
    c.setToolTip(tooltip)
    c.setStyleSheet("""
        QComboBox {
            background: #2a2a2a; color: #ddd; border: 1px solid #444;
            border-radius: 4px; padding: 3px 6px; font-size: 11px;
        }
        QComboBox:hover { border-color: #E50914; }
        QComboBox::drop-down { border: none; }
        QComboBox QAbstractItemView {
            background: #2a2a2a; color: #ddd;
            selection-background-color: #E50914;
        }
    """)
    return c


# ============================================================
#  LoaderWorker  (unchanged logic, kept in same file)
# ============================================================

class LoaderWorker(QObject):
    finished = pyqtSignal()
    data_loaded = pyqtSignal(object)
    progress = pyqtSignal(int)
    progress_message = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller
        self.source = str(controller.active_profile.url)
        self.profile_name = str(controller.active_profile.name)
        self.config_dir = str(controller.config_dir)
        self.is_within_24_hours = controller.active_profile.is_within_24_hours()
        self.loader = controller.data_loader  # Use controller's loader directly

    def _progress_callback(self, current, total, message):
        if total > 0:
            self.progress.emit(int((current / total) * 100))
        self.progress_message.emit(message)

    def run(self):
        try:
            data_path = Path(os.path.join(self.config_dir, self.profile_name + "data.json"))
            if self.is_within_24_hours and data_path.is_file():
                self.progress_message.emit("Loading from cache...")
                self.loader.load_from_json(data_path)
            else:
                self.progress_message.emit("Downloading playlist...")
                success = self.loader.load(self.source, progress_callback=self._progress_callback)
                if not success:
                    self.error.emit("Failed to load IPTV data from URL")
                    self.progress_message.emit("Falling back to cached data...")
                    if data_path.is_file():
                        self.loader.load_from_json(data_path)
                    else:
                        self.error.emit("No cached data available")
                        self.finished.emit()
                        return
                else:
                    self.progress_message.emit("Saving to cache...")
                    self.loader.save_to_json(data_path)
                    self.controller.active_profile.update_last_loaded()
                    self.controller.profile_manager.update_profile(self.controller.active_profile)
                    self.controller.profile_manager.export_profiles(self.controller.profile_path)

            self.data_loaded.emit(None)  # Signal that loading is done
            self.progress_message.emit("Loading complete!")
            self.finished.emit()
        except Exception as e:
            exc_type, _, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f"{exc_type.__name__} in {fname} line {exc_tb.tb_lineno}: {e}")
            self.error.emit(f"Error loading IPTV data: {str(e)}")
            self.finished.emit()


# ============================================================
#  LoadingOverlay  (unchanged)
# ============================================================

class LoadingOverlay(QWidget):
    SPINNER_CHARS = ['\u280B', '\u2819', '\u2839', '\u2838', '\u283C', '\u2834', '\u2826', '\u2827', '\u2807', '\u280F']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180);")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.spinner_index = 0
        self.spinner_label = QLabel(self.SPINNER_CHARS[0])
        self.spinner_label.setAlignment(Qt.AlignCenter)
        self.spinner_label.setStyleSheet("font-size: 70px; color: #E50914;")
        layout.addWidget(self.spinner_label)

        self.text_label = QLabel("Loading channels...")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("font-size: 20px; color: white; margin-top: 10px;")
        layout.addWidget(self.text_label)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_spinner)
        self.timer.start(80)
        self.hide()

    def rotate_spinner(self):
        self.spinner_index = (self.spinner_index + 1) % len(self.SPINNER_CHARS)
        self.spinner_label.setText(self.SPINNER_CHARS[self.spinner_index])

    def showEvent(self, event):
        super().showEvent(event)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(500)
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.opacity_anim.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        self.timer.stop()

    def update_text(self, text):
        self.text_label.setText(text)


# ============================================================
#  ChooseChannelScreen  – full rewrite of layout
# ============================================================

class ChooseChannelScreen(QWidget):
    logout_signal = pyqtSignal(str)

    # ── init ────────────────────────────────────────────────
    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.all_groups = []
        self._all_groups_lower = []  # Pre-lowered for fast search
        self.all_channels = []
        self._all_channels_lower = []  # Pre-lowered for fast search
        self._cached_fav_names = None  # Cached favorite names set
        self.controller = controller
        self.active_channel = None
        self.fullscreen_view = None
        self.thread = None
        self.worker = None
        self._badge_map = {}

        self._build_ui()
        self._connect_signals()

        # Download/record manager
        downloads_dir = os.path.join(controller.config_dir, "downloads")
        self.download_manager = DownloadRecordManager(downloads_dir)
        self.active_recordings = {}
        self._active_download_id = None
        self._setup_download_signals()

        # Scheduled recording system
        self.schedule_manager = ScheduleManager(controller.config_dir)
        self.recording_scheduler = RecordingScheduler(self.schedule_manager, self.download_manager)
        self._setup_scheduler_signals()
        self.recording_scheduler.start()

        # Search debounce timers
        self._channel_search_timer = QTimer()
        self._channel_search_timer.setSingleShot(True)
        self._channel_search_timer.setInterval(250)
        self._channel_search_timer.timeout.connect(self._do_filter_channels)

        self._group_search_timer = QTimer()
        self._group_search_timer.setSingleShot(True)
        self._group_search_timer.setInterval(200)
        self._group_search_timer.timeout.connect(self._do_filter_groups)

        # Overlays
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()
        self.retry_overlay = RetryOverlay(self)
        self.retry_overlay.cancel_button.clicked.connect(self._cancel_retry)
        self.retry_overlay.hide()

        QTimer.singleShot(100, self.load_playlist_with_progress)

    # ── master stylesheet ───────────────────────────────────
    _STYLESHEET = """
        QWidget {
            background: #0e0e0e;
            color: #FFFFFF;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QWidget#header {
            background: #141414;
            border-bottom: 1px solid #222;
        }
        QWidget#sidebar {
            background: #141414;
        }
        QListWidget {
            background: #1a1a1a;
            border: 1px solid #2a2a2a;
            border-radius: 6px;
            padding: 2px;
            font-size: 13px;
            outline: none;
        }
        QListWidget::item {
            padding: 5px 8px;
            border-radius: 4px;
        }
        QListWidget::item:selected {
            background: #E50914;
        }
        QListWidget::item:hover:!selected {
            background: #252525;
        }
        QLineEdit {
            background: #1e1e1e;
            border: 1px solid #333;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 13px;
            color: #ddd;
        }
        QLineEdit:focus { border-color: #E50914; }
        QSlider::groove:horizontal {
            height: 4px; background: #444; border-radius: 2px;
        }
        QSlider::handle:horizontal {
            background: #E50914; width: 12px; margin: -4px 0; border-radius: 6px;
        }
        QTabBar::tab {
            background: #1a1a1a;
            color: #888;
            border: none;
            padding: 5px 8px;
            min-width: 50px;
            font-size: 12px;
            font-weight: 600;
        }
        QTabBar::tab:selected {
            color: #E50914;
            border-bottom: 2px solid #E50914;
        }
        QTabBar::tab:hover:!selected { color: #ccc; }
    """

    # ── build UI ────────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle("IPTV Saba")
        self.setWindowIcon(QIcon(WINDOW_ICON_PATH))
        self.setMinimumSize(900, 600)
        self.resize(1280, 750)
        self.setStyleSheet(self._STYLESHEET)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ──── Header ────────────────────────────────────────
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(44)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 14, 0)
        hl.setSpacing(12)

        title = QLabel("IPTV Saba")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #E50914; background: transparent;")
        hl.addWidget(title)

        self.now_playing_label = QLabel("")
        self.now_playing_label.setStyleSheet("font-size: 13px; color: #999; background: transparent;")
        hl.addWidget(self.now_playing_label, 1)

        self.logout_button = _icon_btn("Logout", "Return to profile selection",
                                        bg="#333", hover="#444", pressed="#222",
                                        fs=12, pad="5px 14px", mw=60, mh=26)
        hl.addWidget(self.logout_button)
        root.addWidget(header)

        # ──── Body splitter ─────────────────────────────────
        body = QSplitter(Qt.Horizontal)
        body.setHandleWidth(1)
        body.setStyleSheet("QSplitter::handle { background: #222; }")
        root.addWidget(body, 1)

        # ──── LEFT SIDEBAR ──────────────────────────────────
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(10, 10, 6, 10)
        sl.setSpacing(6)

        # Groups section
        gl = QLabel("GROUPS")
        gl.setStyleSheet("font-size: 10px; font-weight: 700; color: #555; letter-spacing: 1px; background: transparent;")
        sl.addWidget(gl)

        self.group_search_bar = QLineEdit()
        self.group_search_bar.setPlaceholderText("Search groups...")
        sl.addWidget(self.group_search_bar)

        self.group_list = QListWidget()
        sl.addWidget(self.group_list, 1)

        # Channels section
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #222;")
        sl.addWidget(sep)

        # Tab bar: All | Favorites | History
        self.channel_tabs = QTabBar()
        self.channel_tabs.addTab("All")
        self.channel_tabs.addTab("Favorites")
        self.channel_tabs.addTab("History")
        self.channel_tabs.setExpanding(True)
        self.channel_tabs.setDrawBase(False)
        self.channel_tabs.setDocumentMode(True)
        sl.addWidget(self.channel_tabs)

        self.channel_search_bar = QLineEdit()
        self.channel_search_bar.setPlaceholderText("Search channels...")
        sl.addWidget(self.channel_search_bar)

        self.channel_list = QListWidget()
        sl.addWidget(self.channel_list, 2)

        body.addWidget(sidebar)

        # ──── RIGHT CONTENT ─────────────────────────────────
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 8, 10, 8)
        rl.setSpacing(6)

        # Video frame
        self.video_frame = QWidget()
        self.video_frame.setMinimumHeight(240)
        self.video_frame.setStyleSheet("background: #000; border-radius: 8px;")
        rl.addWidget(self.video_frame, 1)

        # ── Transport controls bar ──────────────────────────
        transport = QWidget()
        transport.setFixedHeight(36)
        transport.setStyleSheet("background: transparent;")
        tl = QHBoxLayout(transport)
        tl.setContentsMargins(0, 2, 0, 2)
        tl.setSpacing(6)

        self.play_button = _icon_btn("Play", "Play", fs=11, pad="4px 10px", mw=40, mh=26)
        self.pause_button = _icon_btn("Pause", "Pause", fs=11, pad="4px 10px", mw=44, mh=26)
        self.stop_button = _icon_btn("Stop", "Stop", fs=11, pad="4px 10px", mw=40, mh=26)
        self.fullscreen_button = _icon_btn("Full", "Fullscreen",
                                            bg="#333", hover="#444", pressed="#222",
                                            fs=11, pad="4px 10px", mw=40, mh=26)

        tl.addWidget(self.play_button)
        tl.addWidget(self.pause_button)
        tl.addWidget(self.stop_button)
        tl.addWidget(self.fullscreen_button)

        tl.addSpacing(8)
        vol_icon = QLabel("Vol")
        vol_icon.setStyleSheet("font-size: 11px; color: #888; background: transparent;")
        vol_icon.setFixedWidth(24)
        tl.addWidget(vol_icon)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setToolTip("Volume")
        tl.addWidget(self.volume_slider)

        tl.addStretch()

        self.record_download_button = _icon_btn("Rec", "Record / Download",
                                                 bg="#1877F2", hover="#145dbf", pressed="#0d4ea2",
                                                 fs=11, pad="4px 12px", mw=44, mh=26)
        self.record_download_button.setEnabled(False)
        tl.addWidget(self.record_download_button)

        rl.addWidget(transport)

        # ── Track bar (audio / subs / quality) ──────────────
        trackbar = QWidget()
        trackbar.setFixedHeight(30)
        trackbar.setStyleSheet("background: transparent;")
        tbl = QHBoxLayout(trackbar)
        tbl.setContentsMargins(0, 0, 0, 0)
        tbl.setSpacing(8)

        lbl_style = "font-size: 11px; color: #777; background: transparent;"
        a_lbl = QLabel("Audio:")
        a_lbl.setStyleSheet(lbl_style)
        tbl.addWidget(a_lbl)
        self.audio_combo = _combo("Select audio track")
        tbl.addWidget(self.audio_combo)

        s_lbl = QLabel("Subs:")
        s_lbl.setStyleSheet(lbl_style)
        tbl.addWidget(s_lbl)
        self.subtitle_combo = _combo("Select subtitle track")
        tbl.addWidget(self.subtitle_combo)

        q_lbl = QLabel("Quality:")
        q_lbl.setStyleSheet(lbl_style)
        tbl.addWidget(q_lbl)
        self.quality_combo = _combo("Select stream quality", min_w=80)
        self.quality_combo.addItem("Auto", 0)
        tbl.addWidget(self.quality_combo)

        self.load_subtitle_button = _icon_btn("SRT", "Load external subtitle file",
                                               bg="#333", hover="#444", pressed="#222",
                                               fs=10, pad="3px 8px", mw=36, mh=22)
        tbl.addWidget(self.load_subtitle_button)
        tbl.addStretch()
        rl.addWidget(trackbar)

        # ── Downloads & Recordings Panel ────────────────────
        self.downloads_panel = DownloadsPanel()
        rl.addWidget(self.downloads_panel)

        body.addWidget(right)
        body.setSizes([280, 1000])
        body.setStretchFactor(0, 0)
        body.setStretchFactor(1, 1)

        # Shared player setup
        self.shared_player = get_shared_player()
        self.shared_player.register_embedded_frame(self.video_frame)
        self.player = self.shared_player.player
        self.instance = self.shared_player.vlc_instance
        self.volume_slider.setValue(self.shared_player.volume)

    # ── connect signals ─────────────────────────────────────
    def _connect_signals(self):
        # Sidebar (debounced search)
        self.group_search_bar.textChanged.connect(lambda: self._group_search_timer.start())
        self.group_list.itemClicked.connect(self.on_group_selected)
        self.channel_search_bar.textChanged.connect(lambda: self._channel_search_timer.start())
        self.channel_list.itemClicked.connect(self.on_channel_selected)
        self.channel_tabs.currentChanged.connect(self._on_channel_tab_changed)

        # Transport
        self.play_button.clicked.connect(self.play_channel)
        self.pause_button.clicked.connect(self.pause_channel)
        self.stop_button.clicked.connect(self.stop_channel)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.record_download_button.clicked.connect(self._on_record_download_clicked)
        self.logout_button.clicked.connect(self.logout)

        # Track combos
        self.audio_combo.currentIndexChanged.connect(self._on_audio_track_selected)
        self.subtitle_combo.currentIndexChanged.connect(self._on_subtitle_track_selected)
        self.quality_combo.currentIndexChanged.connect(self._on_quality_selected)
        self.load_subtitle_button.clicked.connect(self._load_external_subtitle)

        # Context menu
        self.channel_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.channel_list.customContextMenuRequested.connect(self.open_context_menu)

        # Controller
        self.controller.data_loaded.connect(self.on_data_loaded)
        self.controller.error_occurred.connect(self.show_error)

        # Shared player
        self.shared_player.stream_error.connect(self._on_stream_error)
        self.shared_player.connection_timeout.connect(self._on_connection_timeout)
        self.shared_player.buffering.connect(self._on_buffering)
        self.shared_player.audio_tracks_available.connect(self._on_audio_tracks_available)
        self.shared_player.subtitles_available.connect(self._on_subtitles_available)
        self.shared_player.retry_started.connect(self._on_retry_started)
        self.shared_player.retry_exhausted.connect(self._on_retry_exhausted)
        self.shared_player.playback_started.connect(self._on_playback_started)
        self.shared_player.quality_variants_available.connect(self._on_quality_variants_available)

    # ── download / recording signal wiring ──────────────────
    def _setup_download_signals(self):
        dm = self.download_manager
        dp = self.downloads_panel

        dm.download_progress.connect(self.on_download_progress)
        dm.download_complete.connect(self.on_download_complete)
        dm.download_error.connect(self.on_download_error)
        dm.recording_started.connect(self.on_recording_started)
        dm.recording_stopped.connect(self.on_recording_stopped)

        dm.download_speed.connect(dp.update_download_speed)
        dm.recording_elapsed.connect(dp.update_recording_elapsed)
        dm.recording_error.connect(self._on_recording_error)
        dm.download_paused.connect(dp.mark_download_paused)
        dm.download_resumed.connect(dp.mark_download_resumed)
        dm.download_queued.connect(self._on_download_queued)

        dp.pause_download_requested.connect(dm.pause_download)
        dp.resume_download_requested.connect(dm.resume_download)
        dp.cancel_download_requested.connect(dm.cancel_download)
        dp.stop_recording_requested.connect(lambda rid: dm.stop_recording(rid))
        dp.open_folder_requested.connect(self._open_folder)
        dp.retry_download_requested.connect(
            lambda did, name, url: dm.start_download(did + "_retry", name, url))

    def _setup_scheduler_signals(self):
        self.recording_scheduler.schedule_started.connect(self.on_scheduled_recording_started)
        self.recording_scheduler.schedule_completed.connect(self.on_scheduled_recording_completed)
        self.recording_scheduler.schedule_failed.connect(self.on_scheduled_recording_failed)

    # ============================================================
    #  Channel list helpers
    # ============================================================

    def _set_all_channels(self, channels):
        """Set channel list and pre-compute lowercase names for search."""
        self.all_channels = channels
        self._all_channels_lower = [ch.lower() for ch in channels]

    def _get_favorite_names(self):
        if self._cached_fav_names is not None:
            return self._cached_fav_names
        try:
            self._cached_fav_names = {ch.name for ch in self.controller.active_profile.favorites}
        except Exception:
            self._cached_fav_names = set()
        return self._cached_fav_names

    def _get_channel_badge(self, channel_name):
        try:
            ch = self.controller.data_loader.get_channel_by_name(channel_name)
            if ch and ch.channel_type:
                ct = ch.channel_type.upper()
                if ct in ("LIVE", "VOD", "SERIES"):
                    return f"  [{ct}]"
        except Exception:
            pass
        return ""

    def _add_channel_items(self, channel_names):
        self.channel_list.setUpdatesEnabled(False)
        self.channel_list.clear()
        fav_names = self._get_favorite_names()

        # Cap displayed items for performance
        display_names = channel_names[:MAX_DISPLAY_CHANNELS]
        truncated = len(channel_names) > MAX_DISPLAY_CHANNELS

        for name in display_names:
            prefix = "[F] " if name in fav_names else ""
            badge = self._badge_map.get(name, "")
            item = QListWidgetItem(f"{prefix}{name}{badge}")
            item.setData(Qt.UserRole, name)
            self.channel_list.addItem(item)

        if truncated:
            overflow = QListWidgetItem(
                f"... and {len(channel_names) - MAX_DISPLAY_CHANNELS} more \u2014 use search to filter"
            )
            overflow.setFlags(overflow.flags() & ~Qt.ItemIsSelectable)
            overflow.setForeground(QColor("#888"))
            self.channel_list.addItem(overflow)

        self.channel_list.setUpdatesEnabled(True)

    def _get_selected_channel_name(self):
        selected_item = self.channel_list.currentItem()
        if selected_item:
            return selected_item.data(Qt.UserRole) or selected_item.text()
        return None

    # ============================================================
    #  Channel tabs: All / Favorites / History
    # ============================================================

    def _on_channel_tab_changed(self, index):
        if index == 0:
            # Reload current group channels
            selected = self.group_list.currentItem()
            if selected:
                self.on_group_selected()
            else:
                self.channel_list.clear()
                self._set_all_channels([])
        elif index == 1:
            self.show_favorites()
        elif index == 2:
            self.show_history()

    # ============================================================
    #  Record / Download button
    # ============================================================

    def _update_record_download_button(self):
        if not self.active_channel or not self.active_channel.stream_url:
            self.record_download_button.setEnabled(False)
            self.record_download_button.setText("Rec")
            return
        self.record_download_button.setEnabled(True)
        if self.download_manager.is_media_file(self.active_channel.stream_url):
            self.record_download_button.setText("DL")
            self.record_download_button.setToolTip("Download this media file")
        else:
            if self.active_channel.name in self.active_recordings:
                self.record_download_button.setText("Stop")
                self.record_download_button.setToolTip("Stop recording")
            else:
                self.record_download_button.setText("Rec")
                self.record_download_button.setToolTip("Start recording")

    def _on_record_download_clicked(self):
        if not self.active_channel:
            return
        if self.download_manager.is_media_file(self.active_channel.stream_url):
            self.download_channel(self.active_channel)
        elif self.active_channel.name in self.active_recordings:
            self.stop_recording_channel(self.active_channel)
        else:
            self.start_recording_channel(self.active_channel)

    # ============================================================
    #  Playlist loading
    # ============================================================

    def load_playlist_with_progress(self):
        try:
            self.loading_overlay.resize(self.size())
            self.loading_overlay.show()
            self.thread = QThread()
            self.worker = LoaderWorker(self.controller)
            self.worker.moveToThread(self.thread)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(self.on_loading_finished)
            self.worker.error.connect(self.show_error)
            self.worker.data_loaded.connect(self._on_data_loaded_from_worker)
            self.worker.progress_message.connect(self.loading_overlay.update_text)
            self.thread.start()
        except Exception as e:
            logger.error(f"Failed to start loading: {e}")
            self.show_error(f"Failed to start loading: {str(e)}")

    def _on_data_loaded_from_worker(self, _unused):
        try:
            loader = self.controller.data_loader
            logger.info(f"Data loaded: {len(loader._groups)} groups, {len(loader._channels)} channels")

            # Invalidate controller caches after data reload
            self.controller._channel_names_cache.clear()

            # Pre-compute badge map once for all channels
            self._badge_map = {}
            for ch in loader.channels:
                if ch.channel_type:
                    self._badge_map[ch.name] = f"  [{ch.channel_type.upper()}]"
        except Exception as e:
            logger.error(f"Error processing loaded data: {e}")

    def on_loading_finished(self):
        self.loading_overlay.hide()
        self.load_groups()

    def _add_group_items(self, group_names):
        """Add group names to the list with channel counts."""
        self.group_list.clear()
        groups_dict = self.controller.data_loader.groups
        for name in group_names:
            group = groups_dict.get(name)
            count = len(group.channels) if group else 0
            item = QListWidgetItem(f"{name}  ({count:,})")
            item.setData(Qt.UserRole, name)
            self.group_list.addItem(item)

    def load_groups(self):
        groups = self.controller.list_groups()
        self.all_groups = groups
        self._all_groups_lower = [g.lower() for g in groups]
        self._add_group_items(groups)

    def populate_group_list(self):
        self._add_group_items(sorted(self.groups_dict.keys()))

    def filter_groups(self, text):
        text_lower = text.lower()
        filtered = [g for g, g_low in zip(self.all_groups, self._all_groups_lower)
                    if text_lower in g_low]
        self._add_group_items(filtered)

    def _do_filter_groups(self):
        self.filter_groups(self.group_search_bar.text())

    def filter_channels(self, text):
        if self.all_channels:
            text_lower = text.lower()
            filtered = [ch for ch, ch_low in zip(self.all_channels, self._all_channels_lower)
                        if text_lower in ch_low]
            self._add_channel_items(filtered)

    def _do_filter_channels(self):
        self.filter_channels(self.channel_search_bar.text())

    # ============================================================
    #  Channel / playback actions
    # ============================================================

    def on_channel_selected(self):
        channel_name = self._get_selected_channel_name()
        if channel_name:
            channel = self.controller.find_channel_by_name(channel_name)
            if channel and channel.stream_url:
                self.play_channel_stream(channel)
                self.add_to_history(channel)
                self.active_channel = channel
                self._update_record_download_button()
                self.now_playing_label.setText(f"Now Playing: {channel.name}")
            else:
                QMessageBox.critical(self, "Stream Error", "Selected channel does not have a valid stream URL.")

    def play_channel_stream(self, channel):
        try:
            success = self.shared_player.play_channel(channel, self.video_frame)
            if not success:
                QMessageBox.critical(self, "Playback Error", "Failed to start playback")
        except Exception as e:
            QMessageBox.critical(self, "Playback Error", f"An error occurred:\n{e}")

    def play_stream(self, stream_url):
        class SimpleChannel:
            def __init__(self, url):
                self.stream_url = url
                self.name = "Stream"
        self.play_channel_stream(SimpleChannel(stream_url))

    def play_channel(self):
        if self.player:
            self.player.play()

    def pause_channel(self):
        if self.player:
            self.player.pause()

    def stop_channel(self):
        if self.player:
            self.player.stop()

    def toggle_fullscreen(self):
        if self.active_channel:
            self.open_fullscreen_view(self.active_channel)
        elif self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def set_volume(self, value):
        if self.player:
            self.player.audio_set_volume(value)

    def set_position(self, position):
        if self.player:
            self.player.set_position(position / 1000.0)

    # ============================================================
    #  Stream error / timeout / buffering handlers
    # ============================================================

    def _on_stream_error(self, error_msg):
        logger.error(f"Stream error: {error_msg}")
        self.retry_overlay.hide_overlay()
        QMessageBox.warning(self, "Stream Error", error_msg, QMessageBox.Ok)

    def _on_connection_timeout(self, timeout_msg):
        logger.warning(f"Connection timeout: {timeout_msg}")
        self.retry_overlay.hide_overlay()
        QMessageBox.warning(self, "Connection Timeout",
                            timeout_msg + "\n\nPlease try another channel or check your network.",
                            QMessageBox.Ok)

    def _on_buffering(self, percentage):
        if 0 < percentage < 100:
            logger.debug(f"Buffering: {percentage}%")

    # ============================================================
    #  Audio / Subtitle / Quality track handlers
    # ============================================================

    def _on_audio_tracks_available(self, tracks):
        self.audio_combo.blockSignals(True)
        self.audio_combo.clear()
        for tid, tname in tracks:
            self.audio_combo.addItem(tname, tid)
        self.audio_combo.blockSignals(False)
        current = self.shared_player.get_current_audio_track()
        for i in range(self.audio_combo.count()):
            if self.audio_combo.itemData(i) == current:
                self.audio_combo.setCurrentIndex(i)
                break

    def _on_subtitles_available(self, tracks):
        self.subtitle_combo.blockSignals(True)
        self.subtitle_combo.clear()
        for tid, tname in tracks:
            self.subtitle_combo.addItem(tname, tid)
        self.subtitle_combo.blockSignals(False)
        current = self.shared_player.get_current_subtitle_track()
        for i in range(self.subtitle_combo.count()):
            if self.subtitle_combo.itemData(i) == current:
                self.subtitle_combo.setCurrentIndex(i)
                break

    def _on_audio_track_selected(self, index):
        if index < 0:
            return
        tid = self.audio_combo.itemData(index)
        if tid is not None:
            self.shared_player.set_audio_track(tid)

    def _on_subtitle_track_selected(self, index):
        if index < 0:
            return
        tid = self.subtitle_combo.itemData(index)
        if tid is not None:
            self.shared_player.set_subtitle_track(tid)

    def _load_external_subtitle(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Subtitle File", "",
            "Subtitle Files (*.srt *.sub *.ass *.ssa *.vtt);;All Files (*)")
        if path:
            if not self.shared_player.load_external_subtitle(path):
                QMessageBox.warning(self, "Subtitle Error", f"Failed to load:\n{path}")

    def _on_quality_variants_available(self, variants):
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        self.quality_combo.addItem("Auto", 0)
        for i, v in enumerate(variants, 1):
            self.quality_combo.addItem(v.display_name, i)
        self.quality_combo.blockSignals(False)

    def _on_quality_selected(self, index):
        if index < 0:
            return
        vi = self.quality_combo.itemData(index)
        if vi is not None:
            self.shared_player.set_quality(vi)

    # ============================================================
    #  Retry handlers
    # ============================================================

    def _on_retry_started(self, channel_name, attempt, max_attempts):
        self.retry_overlay.resize(self.video_frame.size())
        self.retry_overlay.move(self.video_frame.pos())
        self.retry_overlay.show_retry(attempt, max_attempts)

    def _on_retry_exhausted(self, channel_name):
        self.retry_overlay.hide_overlay()
        QMessageBox.warning(self, "Stream Unavailable",
                            f"Could not connect to '{channel_name}' after multiple attempts.\n\n"
                            "The stream may be offline or temporarily unavailable.",
                            QMessageBox.Ok)

    def _cancel_retry(self):
        self.shared_player.cancel_retry()
        self.retry_overlay.hide_overlay()

    def _on_playback_started(self):
        self.retry_overlay.hide_overlay()
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        self.quality_combo.addItem("Auto", 0)
        self.quality_combo.blockSignals(False)

    # ============================================================
    #  Favorites / History / Context menu
    # ============================================================

    def add_to_history(self, channel):
        self.controller.add_to_history(channel)

    def show_favorites(self):
        if not self.controller.active_profile.favorites:
            self.channel_list.clear()
            self._set_all_channels([])
            return
        fav_names = self.controller.active_profile.list_channels_in_favorites()
        self._set_all_channels(fav_names)
        self._add_channel_items(fav_names)

    def show_history(self):
        if not self.controller.active_profile.history:
            self.channel_list.clear()
            self._set_all_channels([])
            return
        hist_names = self.controller.active_profile.list_channels_in_history()
        self._set_all_channels(hist_names)
        self._add_channel_items(hist_names)

    def open_context_menu(self, position):
        channel_name = self._get_selected_channel_name()
        if not channel_name:
            return
        channel = self.controller.find_channel_by_name(channel_name)
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu { background: #222; color: #ddd; border: 1px solid #333; padding: 4px; }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background: #E50914; }
        """)

        menu.addAction("Add to Favorites", self.add_selected_to_favorites)
        menu.addAction("Remove from Favorites", self.remove_selected_from_favorites)
        menu.addSeparator()

        if channel and channel.stream_url:
            if self.download_manager.is_media_file(channel.stream_url):
                menu.addAction("Download", lambda: self.download_channel(channel))
            else:
                if channel_name in self.active_recordings:
                    menu.addAction("Stop Recording", lambda: self.stop_recording_channel(channel))
                else:
                    menu.addAction("Start Recording", lambda: self.start_recording_channel(channel))
            menu.addSeparator()
            menu.addAction("Schedule Recording", lambda: self.schedule_recording(channel))

        menu.exec_(self.channel_list.viewport().mapToGlobal(position))

    def add_selected_to_favorites(self):
        name = self._get_selected_channel_name()
        if name:
            self.controller.add_to_favorites(name)
            self._cached_fav_names = None

    def remove_selected_from_favorites(self):
        name = self._get_selected_channel_name()
        if name:
            self.controller.remove_from_favorites(name)
            self._cached_fav_names = None

    def add_to_favorites(self, channel_name):
        self.controller.add_to_favorites(channel_name)
        self._cached_fav_names = None

    def remove_from_favorites(self, channel_name):
        self.controller.remove_from_favorites(channel_name)
        self._cached_fav_names = None

    @pyqtSlot(dict)
    def on_data_loaded(self, groups):
        self.groups_dict = groups
        self.populate_group_list()

    @pyqtSlot()
    def on_group_selected(self):
        selected_item = self.group_list.currentItem()
        if selected_item:
            group_name = selected_item.data(Qt.UserRole) or selected_item.text()
            channels = self.controller.list_channels_in_group(group_name)
            self._set_all_channels(sorted(channels))  # Sort once here
            self._add_channel_items(self.all_channels)
            # Reset to "All" tab silently
            self.channel_tabs.blockSignals(True)
            self.channel_tabs.setCurrentIndex(0)
            self.channel_tabs.blockSignals(False)

    def populate_channel_list(self, channel_names):
        self._add_channel_items(channel_names)

    @pyqtSlot(str)
    def on_error_occurred(self, error_message):
        QMessageBox.critical(self, "Error", error_message)

    @pyqtSlot(str)
    def show_error(self, message):
        QMessageBox.critical(self, "Error", message)

    # ============================================================
    #  Download / Record actions
    # ============================================================

    def download_channel(self, channel):
        download_id = f"download_{channel.name}_{id(channel)}"
        reply = QMessageBox.question(
            self, 'Download',
            f"Download '{channel.name}'?\n\nSaved to: {self.download_manager.downloads_dir}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success = self.download_manager.start_download(download_id, channel.name, channel.stream_url)
            if success:
                self._active_download_id = download_id
                if self.download_manager.get_queue_position(download_id) == 0:
                    self.downloads_panel.add_active_download(download_id, channel.name)
            else:
                QMessageBox.warning(self, 'Download Failed', f"Could not start download for '{channel.name}'")

    def start_recording_channel(self, channel):
        recording_id = f"record_{channel.name}_{id(channel)}"
        reply = QMessageBox.question(
            self, 'Record',
            f"Start recording '{channel.name}'?\n\nSaved to: {self.download_manager.downloads_dir}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            success = self.download_manager.start_recording(recording_id, channel.name, channel.stream_url)
            if success:
                self.active_recordings[channel.name] = recording_id
                self._update_record_download_button()
            else:
                QMessageBox.warning(self, 'Recording Failed', f"Could not start recording for '{channel.name}'")

    def stop_recording_channel(self, channel):
        if channel.name not in self.active_recordings:
            return
        recording_id = self.active_recordings[channel.name]
        reply = QMessageBox.question(
            self, 'Stop Recording', f"Stop recording '{channel.name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.download_manager.stop_recording(recording_id):
                del self.active_recordings[channel.name]
                self._update_record_download_button()

    # ============================================================
    #  Download / Record signal handlers
    # ============================================================

    def on_download_progress(self, download_id, bytes_downloaded, total_bytes):
        self.downloads_panel.update_download_progress(download_id, bytes_downloaded, total_bytes)

    def on_download_complete(self, download_id, filepath):
        logger.info(f"Download complete: {filepath}")
        self._active_download_id = None
        self.downloads_panel.remove_download(download_id)
        self.downloads_panel.add_completed_item({
            'item_id': download_id, 'channel_name': download_id,
            'filepath': filepath, 'item_type': 'download',
            'state': 'completed', 'completed_at': datetime.now(),
        })

    def on_download_error(self, download_id, error_message):
        logger.error(f"Download error: {error_message}")
        self._active_download_id = None
        self.downloads_panel.remove_download(download_id)
        self.downloads_panel.remove_queued_download(download_id)
        self.downloads_panel.add_completed_item({
            'item_id': download_id, 'channel_name': download_id,
            'filepath': '', 'item_type': 'download',
            'state': 'failed', 'error_message': error_message,
            'completed_at': datetime.now(),
        })

    def on_recording_started(self, recording_id):
        logger.info(f"Recording started: {recording_id}")
        channel_name = recording_id
        for name, rid in self.active_recordings.items():
            if rid == recording_id:
                channel_name = name
                break
        self.downloads_panel.add_active_recording(recording_id, channel_name)

    def on_recording_stopped(self, recording_id, filepath):
        logger.info(f"Recording stopped: {filepath}")
        self.downloads_panel.remove_recording(recording_id)
        channel_name = recording_id
        for name, rid in list(self.active_recordings.items()):
            if rid == recording_id:
                channel_name = name
                break
        self.downloads_panel.add_completed_item({
            'item_id': recording_id, 'channel_name': channel_name,
            'filepath': filepath, 'item_type': 'recording',
            'state': 'completed', 'completed_at': datetime.now(),
        })
        for name, rid in list(self.active_recordings.items()):
            if rid == recording_id:
                del self.active_recordings[name]
                break
        self._update_record_download_button()

    def _on_recording_error(self, recording_id, error_message):
        logger.error(f"Recording error: {recording_id} - {error_message}")

    def _on_download_queued(self, download_id, channel_name, position):
        self.downloads_panel.add_queued_download(download_id, channel_name, position)

    def _open_folder(self, filepath):
        folder = os.path.dirname(filepath)
        if not os.path.isdir(folder):
            return
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", folder])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", folder])
        except Exception as e:
            logger.error(f"Failed to open folder: {e}")

    # ============================================================
    #  Scheduled recording
    # ============================================================

    def schedule_recording(self, channel):
        schedule = ScheduleRecordingDialog.create_schedule(channel, self)
        if not schedule:
            return
        conflicts = self.schedule_manager.get_conflicts(schedule)
        if conflicts:
            names = ", ".join(c.channel_name for c in conflicts)
            QMessageBox.warning(self, "Schedule Conflict",
                                f"Conflicts with: {names}\n\nPlease choose a different time.")
            return
        if self.schedule_manager.add_schedule(schedule):
            QMessageBox.information(self, "Scheduled",
                f"Recording scheduled for '{channel.name}':\n"
                f"Start: {schedule.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"End: {schedule.end_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"Duration: {schedule.duration_minutes} min")
        else:
            QMessageBox.critical(self, "Failed", "Could not add schedule.")

    def on_scheduled_recording_started(self, schedule_id, channel_name):
        logger.info(f"Scheduled recording started: {channel_name}")

    def on_scheduled_recording_completed(self, schedule_id, channel_name, output_path):
        logger.info(f"Scheduled recording completed: {channel_name} -> {output_path}")

    def on_scheduled_recording_failed(self, schedule_id, channel_name, error_message):
        logger.error(f"Scheduled recording failed: {channel_name} - {error_message}")

    # ============================================================
    #  Fullscreen transitions
    # ============================================================

    def open_fullscreen_view(self, channel):
        self.fullscreen_view = FullScreenView(
            channel,
            existing_player=self.shared_player.player,
            existing_instance=self.shared_player.vlc_instance)
        self.fullscreen_view.go_back_signal.connect(self.on_fullscreen_view_closed)
        self.fullscreen_view.showFullScreen()
        QTimer.singleShot(150, self._complete_fullscreen_entry)
        self.hide()

    def _complete_fullscreen_entry(self):
        if self.fullscreen_view and hasattr(self.fullscreen_view, 'video_frame'):
            self.shared_player.transition_to_fullscreen(self.fullscreen_view.video_frame)

    def on_fullscreen_view_closed(self):
        self.show()
        if self.fullscreen_view:
            self.fullscreen_view.close()
            self.fullscreen_view = None
        QTimer.singleShot(150, lambda: self.shared_player.transition_to_embedded())

    # ============================================================
    #  Player attachment / events / cleanup
    # ============================================================

    def attach_player_to_window(self):
        if hasattr(self, 'shared_player') and self.shared_player and hasattr(self, 'video_frame'):
            try:
                self.shared_player.attach_to_frame(self.video_frame)
            except Exception as e:
                logger.error(f"Error attaching player: {e}")

    def showEvent(self, event):
        super().showEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.loading_overlay.resize(self.size())
        if self.retry_overlay.isVisible():
            self.retry_overlay.resize(self.video_frame.size())
            self.retry_overlay.move(self.video_frame.pos())

    def closeEvent(self, event):
        self._perform_full_cleanup()
        event.accept()

    def _perform_full_cleanup(self, for_logout=False):
        logger.info(f"Performing cleanup (for_logout={for_logout})")
        if hasattr(self, 'recording_scheduler'):
            try:
                self.recording_scheduler.stop()
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")

        if hasattr(self, 'download_manager'):
            try:
                self.download_manager.cleanup_all()
            except Exception as e:
                logger.error(f"Error cleaning up downloads: {e}")

        if hasattr(self, 'fullscreen_view') and self.fullscreen_view:
            try:
                self.fullscreen_view.close()
                self.fullscreen_view = None
            except Exception as e:
                logger.error(f"Error closing fullscreen: {e}")

        if hasattr(self, 'shared_player') and self.shared_player:
            try:
                if for_logout:
                    self.shared_player.safe_stop_for_cleanup()
                    self.shared_player._embedded_frame = None
                else:
                    self.shared_player.stop()
            except Exception as e:
                logger.error(f"Error stopping player: {e}")

    @pyqtSlot()
    def logout(self):
        reply = QMessageBox.question(
            self, 'Logout', "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self._perform_full_cleanup(for_logout=True)
            QTimer.singleShot(100, lambda: self.logout_signal.emit("logging Out"))


def main():
    app = QApplication(sys.argv)
    controller = Controller()
    controller.active_profile = create_mock_profile()
    screen = ChooseChannelScreen(controller)
    screen.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
