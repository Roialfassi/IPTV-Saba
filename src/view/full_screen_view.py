"""
FullScreenView - Fullscreen media player with floating overlay controls.

The controls and retry indicator are separate top-level windows
(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) that float
above VLC's native video surface.  This is necessary because VLC renders
via a native child window (set_hwnd / set_xwindow / set_nsobject) that
sits above all Qt child widgets in z-order.  Only independent top-level
windows can reliably appear above the native video.

Mouse detection uses QTimer-based cursor-position polling (100 ms) instead
of Qt event filters, because VLC's native window captures mouse events
before they reach Qt's event system.

This approach mirrors what VLC's own Qt interface does for its fullscreen
controller.
"""
import sys
import logging
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QSlider, QComboBox,
                             QFileDialog, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QIcon, QCursor
import vlc

from src.model.channel_model import Channel
from src.utils.resource_path import resource_path

# Import SharedPlayerManager for potential direct usage
try:
    from src.services.shared_player_manager import (
        get_shared_player, SharedPlayerManager)
except ImportError:
    get_shared_player = None
    SharedPlayerManager = None

logger = logging.getLogger(__name__)

# Constants
HIDE_CONTROLS_DELAY_MS = 4000
MOUSE_POLL_INTERVAL_MS = 100
CONTROLS_HEIGHT = 120
DEFAULT_VOLUME = 50
WINDOW_ICON_PATH = resource_path("Assets/iptv-logo2.ico")

# ---------------------------------------------------------------------------
#  Styles
# ---------------------------------------------------------------------------
COMBO_STYLE = """
    QComboBox {
        background-color: #2a2a2a; color: #ddd;
        border: 1px solid #555; border-radius: 4px;
        padding: 3px 6px; min-width: 100px;
        font-size: 11px; font-family: 'Segoe UI', Arial, sans-serif;
    }
    QComboBox:hover { border: 1px solid #E50914; }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView {
        background-color: #2a2a2a; color: #ddd;
        selection-background-color: #E50914;
    }
"""

ROW1_BUTTON_STYLE = """
    QPushButton {
        background-color: rgba(229,9,20,0.85); border: none; color: white;
        padding: 6px 14px; font-size: 13px; font-weight: bold;
        margin: 2px 1px; border-radius: 6px;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QPushButton:hover { background-color: rgba(229,9,20,1); }
    QPushButton:pressed { background-color: rgba(191,8,17,1); }
"""

ROW2_BUTTON_STYLE = """
    QPushButton {
        background-color: rgba(44,44,44,0.8);
        border: 1px solid #555; color: white;
        padding: 5px 10px; font-size: 12px;
        margin: 2px 1px; border-radius: 6px;
        font-family: 'Segoe UI', Arial, sans-serif;
    }
    QPushButton:hover {
        background-color: rgba(229,9,20,0.8);
        border: 1px solid #E50914;
    }
"""


# ===================================================================
#  _OverlayWindow -- base for top-level overlay windows above VLC
# ===================================================================

class _OverlayWindow(QWidget):
    """
    Base class for top-level overlay windows that float above VLC video.

    Uses Qt.Tool so the OS keeps it above its parent window, plus
    FramelessWindowHint and WindowStaysOnTopHint to guarantee it
    renders on top of VLC's native child window.
    """

    def __init__(self, parent_view: QWidget):
        super().__init__(parent_view)
        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self._parent_view = parent_view


# ===================================================================
#  Controls overlay (bottom bar)
# ===================================================================

class _ControlsOverlay(_OverlayWindow):
    """Floating controls bar at the bottom of the fullscreen view."""

    def __init__(self, parent_view, channel_name: str):
        super().__init__(parent_view)
        self.setStyleSheet("""
            QWidget#_ctrl_bg {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0,0,0,0),
                    stop:0.3 rgba(0,0,0,100),
                    stop:1 rgba(0,0,0,220));
            }
            QLabel { background: transparent; color: #fff;
                     font-family: 'Segoe UI', Arial, sans-serif; }
        """)

        bg = QWidget(self)
        bg.setObjectName("_ctrl_bg")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(bg)

        layout = QVBoxLayout(bg)
        layout.setContentsMargins(12, 20, 12, 10)
        layout.setSpacing(6)

        # -- Row 1: Back, Play/Pause, Volume, Channel name --
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.back_button = QPushButton("Back")
        self.back_button.setToolTip("Return to channel browser (Escape)")
        self.back_button.setCursor(Qt.PointingHandCursor)
        self.back_button.setStyleSheet(ROW1_BUTTON_STYLE)
        self.back_button.setFocusPolicy(Qt.NoFocus)
        row1.addWidget(self.back_button)

        self.play_pause_button = QPushButton("Pause")
        self.play_pause_button.setToolTip("Play / Pause (Space)")
        self.play_pause_button.setCursor(Qt.PointingHandCursor)
        self.play_pause_button.setStyleSheet(ROW1_BUTTON_STYLE)
        self.play_pause_button.setFocusPolicy(Qt.NoFocus)
        row1.addWidget(self.play_pause_button)

        vol_label = QLabel("Vol")
        vol_label.setStyleSheet("font-size: 12px;")
        row1.addWidget(vol_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(DEFAULT_VOLUME)
        self.volume_slider.setToolTip("Volume (0-100)")
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setFocusPolicy(Qt.NoFocus)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px; background: #444; border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #E50914; width: 12px; margin: -4px 0;
                border-radius: 6px;
            }
        """)
        row1.addWidget(self.volume_slider)

        self.volume_percent_label = QLabel(f"{DEFAULT_VOLUME}%")
        self.volume_percent_label.setFixedWidth(40)
        self.volume_percent_label.setStyleSheet("font-size: 12px;")
        row1.addWidget(self.volume_percent_label)

        row1.addStretch()

        self.channel_label = QLabel(channel_name)
        self.channel_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.channel_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        row1.addWidget(self.channel_label)

        layout.addLayout(row1)

        # -- Row 2: Audio, Subs, SRT, Quality --
        row2 = QHBoxLayout()
        row2.setSpacing(8)
        lbl_s = "font-size: 12px; color: #aaa;"

        a_lbl = QLabel("Audio:")
        a_lbl.setStyleSheet(lbl_s)
        row2.addWidget(a_lbl)
        self.audio_combo = QComboBox()
        self.audio_combo.setMinimumWidth(120)
        self.audio_combo.setToolTip("Select audio track")
        self.audio_combo.setStyleSheet(COMBO_STYLE)
        self.audio_combo.setFocusPolicy(Qt.NoFocus)
        row2.addWidget(self.audio_combo)

        s_lbl = QLabel("Subs:")
        s_lbl.setStyleSheet(lbl_s)
        row2.addWidget(s_lbl)
        self.subtitle_combo = QComboBox()
        self.subtitle_combo.setMinimumWidth(120)
        self.subtitle_combo.setToolTip("Select subtitle track")
        self.subtitle_combo.setStyleSheet(COMBO_STYLE)
        self.subtitle_combo.setFocusPolicy(Qt.NoFocus)
        row2.addWidget(self.subtitle_combo)

        self.load_subtitle_button = QPushButton("Load SRT")
        self.load_subtitle_button.setToolTip(
            "Load external subtitle file (.srt, .sub, .ass)")
        self.load_subtitle_button.setCursor(Qt.PointingHandCursor)
        self.load_subtitle_button.setStyleSheet(ROW2_BUTTON_STYLE)
        self.load_subtitle_button.setFocusPolicy(Qt.NoFocus)
        row2.addWidget(self.load_subtitle_button)

        q_lbl = QLabel("Quality:")
        q_lbl.setStyleSheet(lbl_s)
        row2.addWidget(q_lbl)
        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumWidth(100)
        self.quality_combo.setToolTip("Select stream quality")
        self.quality_combo.addItem("Auto", 0)
        self.quality_combo.setStyleSheet(COMBO_STYLE)
        self.quality_combo.setFocusPolicy(Qt.NoFocus)
        row2.addWidget(self.quality_combo)

        row2.addStretch()
        layout.addLayout(row2)

    # Convenience references used by FullScreenView
    # (avoids self._controls_overlay.back_button.clicked.connect etc.)


# ===================================================================
#  Retry overlay (centered)
# ===================================================================

class _RetryOverlay(_OverlayWindow):
    """Centered reconnection status overlay above VLC video."""

    def __init__(self, parent_view: QWidget):
        super().__init__(parent_view)
        self.setStyleSheet("background: transparent;")

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        container = QWidget()
        container.setFixedSize(300, 180)
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(20,20,20,0.92);
                border-radius: 10px;
                border: 2px solid #E50914;
            }
        """)
        cl = QVBoxLayout(container)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(15)

        self.title_label = QLabel("Reconnecting...")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #fff;"
            "background: transparent; border: none;")
        cl.addWidget(self.title_label)

        self.attempt_label = QLabel("Attempt 1 of 3")
        self.attempt_label.setAlignment(Qt.AlignCenter)
        self.attempt_label.setStyleSheet(
            "font-size: 14px; color: #aaa;"
            "background: transparent; border: none;")
        cl.addWidget(self.attempt_label)

        progress = QProgressBar()
        progress.setRange(0, 0)
        progress.setTextVisible(False)
        progress.setFixedHeight(6)
        progress.setStyleSheet("""
            QProgressBar {
                background-color: #333; border: none; border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #E50914; border-radius: 3px;
            }
        """)
        cl.addWidget(progress)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setFocusPolicy(Qt.NoFocus)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #444; color: white; border: none;
                padding: 8px 16px; border-radius: 4px; font-weight: 600;
            }
            QPushButton:hover { background-color: #E50914; }
            QPushButton:pressed { background-color: #BF0811; }
        """)
        cl.addWidget(self.cancel_button, alignment=Qt.AlignCenter)

        outer.addWidget(container)


# ===================================================================
#  FullScreenView
# ===================================================================

class FullScreenView(QWidget):
    """
    Full-screen media player.

    Overlay controls and retry indicator are separate top-level windows
    that float above VLC's native video surface.  Mouse movement is
    detected via cursor-position polling (not Qt event filters) to work
    reliably even when VLC's native window captures input.
    """

    go_back_signal = pyqtSignal()

    def __init__(self, channel: Channel,
                 existing_player=None, existing_instance=None):
        super().__init__()
        self.channel_name = channel.name
        self.stream_url = channel.stream_url

        # VLC player setup
        if existing_player and existing_instance:
            self.vlc_instance = existing_instance
            self.player = existing_player
            self.is_playing = True
            self.using_shared_player = True
            logger.info("Reusing existing VLC player instance")
        else:
            self.vlc_instance = vlc.Instance()
            self.player = self.vlc_instance.media_player_new()
            self.is_playing = False
            self.using_shared_player = False
            logger.info("Created new VLC player instance")

        self.is_muted = False
        self._cursor_hidden = False

        # Build main window (video frame only)
        self._init_ui()

        # Build overlay windows (separate top-level windows)
        self._controls_overlay = _ControlsOverlay(self, self.channel_name)
        self._retry_overlay = _RetryOverlay(self)

        # Wire overlay button/combo signals
        self._wire_controls()

        # Start playback or update UI
        if not (existing_player and existing_instance):
            self.play_channel()
        else:
            self.play_pause_button.setText("Pause")

        # Connect SharedPlayerManager signals
        self._connect_track_signals()
        self._connect_retry_signals()

        # --- Mouse polling timer (replaces event filter) ---
        self._last_cursor_pos = QPoint(-1, -1)
        self._mouse_poll_timer = QTimer(self)
        self._mouse_poll_timer.setInterval(MOUSE_POLL_INTERVAL_MS)
        self._mouse_poll_timer.timeout.connect(self._poll_mouse)

        # --- Auto-hide timer (single-shot) ---
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.setInterval(HIDE_CONTROLS_DELAY_MS)
        self._hide_timer.timeout.connect(self._on_hide_timer)

    # ================================================================
    #  Convenience accessors (keep FullScreenView API flat)
    # ================================================================

    @property
    def play_pause_button(self):
        return self._controls_overlay.play_pause_button

    @property
    def volume_slider(self):
        return self._controls_overlay.volume_slider

    @property
    def volume_percent_label(self):
        return self._controls_overlay.volume_percent_label

    @property
    def audio_combo(self):
        return self._controls_overlay.audio_combo

    @property
    def subtitle_combo(self):
        return self._controls_overlay.subtitle_combo

    @property
    def quality_combo(self):
        return self._controls_overlay.quality_combo

    # ================================================================
    #  UI Construction
    # ================================================================

    def _init_ui(self):
        self.setWindowTitle('Full Screen Channel View')
        self.setWindowIcon(QIcon(WINDOW_ICON_PATH))
        self.setStyleSheet("background-color: #000;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_frame, 1)

    def _wire_controls(self):
        """Connect overlay widget signals to FullScreenView methods."""
        c = self._controls_overlay
        c.back_button.clicked.connect(self.go_back)
        c.play_pause_button.clicked.connect(self.toggle_play_pause)
        c.volume_slider.valueChanged.connect(self.set_volume)
        c.audio_combo.currentIndexChanged.connect(
            self._on_audio_track_selected)
        c.subtitle_combo.currentIndexChanged.connect(
            self._on_subtitle_track_selected)
        c.load_subtitle_button.clicked.connect(self._load_external_subtitle)
        c.quality_combo.currentIndexChanged.connect(self._on_quality_selected)

        self._retry_overlay.cancel_button.clicked.connect(self._cancel_retry)

    # ================================================================
    #  Overlay geometry sync
    # ================================================================

    def _sync_overlays(self):
        """Position overlay windows relative to this fullscreen window."""
        geo = self.geometry()

        # Controls bar at bottom
        self._controls_overlay.setGeometry(
            geo.x(),
            geo.y() + geo.height() - CONTROLS_HEIGHT,
            geo.width(),
            CONTROLS_HEIGHT,
        )

        # Retry overlay fills entire area (content is centered by layout)
        self._retry_overlay.setGeometry(geo)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_overlays()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._sync_overlays()

    # ================================================================
    #  Mouse detection via cursor polling
    # ================================================================

    def _poll_mouse(self):
        """Check if the cursor moved since last poll."""
        pos = QCursor.pos()
        if pos != self._last_cursor_pos:
            self._last_cursor_pos = pos
            # Only react if cursor is within our fullscreen area
            if self.geometry().contains(pos):
                self._on_mouse_activity()

    def _on_mouse_activity(self):
        """Cursor moved over our window -- show controls, reset timer."""
        self.show_controls()
        self._hide_timer.start()

    def _on_hide_timer(self):
        """Auto-hide timer expired."""
        # Don't hide while retry overlay is showing
        if self._retry_overlay.isVisible():
            self._hide_timer.start()
            return

        # Don't hide if cursor is currently over the controls
        pos = QCursor.pos()
        ctrl_geo = self._controls_overlay.geometry()
        if self._controls_overlay.isVisible() and ctrl_geo.contains(pos):
            self._hide_timer.start()
            return

        self.hide_controls()

    # ================================================================
    #  Show / Hide controls + cursor
    # ================================================================

    def show_controls(self):
        if not self._controls_overlay.isVisible():
            self._sync_overlays()
            self._controls_overlay.show()
            self._controls_overlay.raise_()
        if self._cursor_hidden:
            QApplication.restoreOverrideCursor()
            self._cursor_hidden = False

    def hide_controls(self):
        self._controls_overlay.hide()
        if not self._cursor_hidden:
            QApplication.setOverrideCursor(QCursor(Qt.BlankCursor))
            self._cursor_hidden = True

    # ================================================================
    #  Retry overlay
    # ================================================================

    def _connect_retry_signals(self):
        if not (get_shared_player and self.using_shared_player):
            return
        sp = get_shared_player()
        sp.retry_started.connect(self._on_retry_started)
        sp.retry_exhausted.connect(self._on_retry_exhausted)
        sp.playback_started.connect(self._on_playback_started)
        logger.info("Connected to SharedPlayerManager retry signals")

    def _on_retry_started(self, channel_name, attempt, max_attempts):
        self._retry_overlay.attempt_label.setText(
            f"Attempt {attempt} of {max_attempts}")
        self._retry_overlay.title_label.setText("Reconnecting...")
        self._sync_overlays()
        self._retry_overlay.show()
        self._retry_overlay.raise_()
        self.show_controls()

    def _on_retry_exhausted(self, channel_name):
        self._retry_overlay.hide()

    def _on_playback_started(self):
        self._retry_overlay.hide()

    def _cancel_retry(self):
        if get_shared_player and self.using_shared_player:
            get_shared_player().cancel_retry()
        self._retry_overlay.hide()

    # ================================================================
    #  Player attachment
    # ================================================================

    def attach_player_to_window(self):
        """Attach VLC player to the video frame (platform-specific)."""
        if not self.player:
            logger.warning("No player to attach")
            return
        try:
            win_id = int(self.video_frame.winId())
            logger.info(f"FullScreenView: Attaching to window {win_id}")

            if sys.platform.startswith('linux'):
                self.player.set_xwindow(win_id)
            elif sys.platform == "win32":
                self.player.set_hwnd(win_id)
            elif sys.platform == "darwin":
                self.player.set_nsobject(win_id)
            else:
                logger.error(f"Unsupported platform: {sys.platform}")
                return

            QTimer.singleShot(150, self._refresh_video_after_attach)
        except Exception as e:
            logger.error(f"Error attaching player: {e}")
            import traceback
            traceback.print_exc()

    def _refresh_video_after_attach(self):
        """Force video to refresh after attaching to new window."""
        try:
            if not self.player:
                return
            if self.player.is_playing():
                current_pos = self.player.get_position()
                self.player.pause()

                def resume():
                    if self.player:
                        self.player.play()
                        if current_pos and current_pos > 0.0:
                            QTimer.singleShot(
                                50,
                                lambda: self.player.set_position(current_pos))

                QTimer.singleShot(100, resume)
            else:
                self.player.play()
        except Exception as e:
            logger.error(f"Error refreshing video: {e}")

    # ================================================================
    #  Widget events
    # ================================================================

    def showEvent(self, event):
        super().showEvent(event)

        # Start polling and auto-hide now that the window is visible
        self._sync_overlays()
        self._controls_overlay.show()
        self._controls_overlay.raise_()
        self._mouse_poll_timer.start()
        self._hide_timer.start()

        if self.using_shared_player:
            logger.info("FullScreenView shown - shared player handles attachment")
        else:
            logger.info("FullScreenView shown - scheduling own player attachment")
            QTimer.singleShot(200, self.attach_player_to_window)

    def keyPressEvent(self, event):
        self.show_controls()
        self._hide_timer.start()

        if event.key() == Qt.Key_Escape:
            self.go_back()
        elif event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        elif event.key() == Qt.Key_Up:
            vol = min(self.player.audio_get_volume() + 10, 100)
            self.volume_slider.setValue(vol)
            self.set_volume(vol)
        elif event.key() == Qt.Key_Down:
            vol = max(self.player.audio_get_volume() - 10, 0)
            self.volume_slider.setValue(vol)
            self.set_volume(vol)
        event.accept()

    def closeEvent(self, event):
        """Clean up timers, overlays, cursor, and optionally VLC player."""
        # Stop timers
        self._mouse_poll_timer.stop()
        self._hide_timer.stop()

        # Hide and close overlay windows
        self._controls_overlay.hide()
        self._controls_overlay.close()
        self._retry_overlay.hide()
        self._retry_overlay.close()

        # Restore cursor
        if self._cursor_hidden:
            QApplication.restoreOverrideCursor()
            self._cursor_hidden = False

        # Disconnect SharedPlayerManager signals
        self._disconnect_signals()

        # VLC cleanup (only if we own the player)
        if not self.using_shared_player and self.player:
            try:
                if self.player.is_playing():
                    self.player.set_pause(1)
                try:
                    self.player.set_media(None)
                except Exception:
                    pass
                if sys.platform != "win32":
                    try:
                        self.player.stop()
                    except Exception:
                        pass
                try:
                    self.player.release()
                except Exception as e:
                    logger.warning(f"Error releasing player: {e}")
                if self.vlc_instance:
                    try:
                        self.vlc_instance.release()
                    except Exception as e:
                        logger.warning(f"Error releasing VLC instance: {e}")
                logger.info("Cleaned up local VLC player instance")
            except Exception as e:
                logger.error(f"Error during FullScreenView cleanup: {e}")
        else:
            logger.info("Using shared player - skipping VLC cleanup")

        event.accept()

    def _disconnect_signals(self):
        """Safely disconnect all SharedPlayerManager signals."""
        if not (get_shared_player and self.using_shared_player):
            return
        sp = get_shared_player()
        pairs = [
            (sp.audio_tracks_available, self._on_audio_tracks_available),
            (sp.subtitles_available, self._on_subtitles_available),
            (sp.quality_variants_available, self._on_quality_variants_available),
            (sp.retry_started, self._on_retry_started),
            (sp.retry_exhausted, self._on_retry_exhausted),
            (sp.playback_started, self._on_playback_started),
        ]
        for sig, slot in pairs:
            try:
                sig.disconnect(slot)
            except (TypeError, RuntimeError):
                pass

    # ================================================================
    #  Playback controls
    # ================================================================

    def play_channel(self):
        media = self.vlc_instance.media_new(self.stream_url)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True
        self.play_pause_button.setText("Pause")

    def toggle_play_pause(self):
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
            self.play_pause_button.setText("Play")
        else:
            self.player.play()
            self.is_playing = True
            self.play_pause_button.setText("Pause")

    def set_volume(self, volume):
        self.player.audio_set_volume(volume)
        self.volume_percent_label.setText(f"{volume}%")

    def go_back(self):
        self.go_back_signal.emit()

    # ================================================================
    #  Audio / Subtitle / Quality
    # ================================================================

    def _connect_track_signals(self):
        if get_shared_player and self.using_shared_player:
            sp = get_shared_player()
            sp.audio_tracks_available.connect(self._on_audio_tracks_available)
            sp.subtitles_available.connect(self._on_subtitles_available)
            sp.quality_variants_available.connect(
                self._on_quality_variants_available)
            logger.info("Connected to SharedPlayerManager track signals")
            variants = sp.get_quality_variants()
            if variants:
                self._on_quality_variants_available(variants)

    def _on_audio_tracks_available(self, tracks):
        logger.info(f"Audio tracks available: {len(tracks)}")
        self.audio_combo.blockSignals(True)
        self.audio_combo.clear()
        for tid, tname in tracks:
            self.audio_combo.addItem(tname, tid)
        self.audio_combo.blockSignals(False)
        if get_shared_player:
            cur = get_shared_player().get_current_audio_track()
            for i in range(self.audio_combo.count()):
                if self.audio_combo.itemData(i) == cur:
                    self.audio_combo.setCurrentIndex(i)
                    break

    def _on_subtitles_available(self, tracks):
        logger.info(f"Subtitle tracks available: {len(tracks)}")
        self.subtitle_combo.blockSignals(True)
        self.subtitle_combo.clear()
        for tid, tname in tracks:
            self.subtitle_combo.addItem(tname, tid)
        self.subtitle_combo.blockSignals(False)
        if get_shared_player:
            cur = get_shared_player().get_current_subtitle_track()
            for i in range(self.subtitle_combo.count()):
                if self.subtitle_combo.itemData(i) == cur:
                    self.subtitle_combo.setCurrentIndex(i)
                    break

    def _on_audio_track_selected(self, index):
        if index < 0:
            return
        tid = self.audio_combo.itemData(index)
        if tid is not None:
            if get_shared_player and self.using_shared_player:
                get_shared_player().set_audio_track(tid)
            elif self.player:
                self.player.audio_set_track(tid)
            logger.info(f"Selected audio track: {tid}")

    def _on_subtitle_track_selected(self, index):
        if index < 0:
            return
        tid = self.subtitle_combo.itemData(index)
        if tid is not None:
            if get_shared_player and self.using_shared_player:
                get_shared_player().set_subtitle_track(tid)
            elif self.player:
                self.player.video_set_spu(tid)
            logger.info(f"Selected subtitle track: {tid}")

    def _load_external_subtitle(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Subtitle File", "",
            "Subtitle Files (*.srt *.sub *.ass *.ssa *.vtt);;All Files (*)")
        if file_path:
            if get_shared_player and self.using_shared_player:
                ok = get_shared_player().load_external_subtitle(file_path)
            elif self.player:
                ok = self.player.video_set_subtitle_file(file_path)
            else:
                ok = False
            if ok:
                logger.info(f"Loaded external subtitle: {file_path}")
            else:
                logger.error(f"Failed to load subtitle: {file_path}")

    def _on_quality_variants_available(self, variants):
        logger.info(f"Quality variants available: {len(variants)}")
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        self.quality_combo.addItem("Auto", 0)
        for i, v in enumerate(variants, start=1):
            self.quality_combo.addItem(v.display_name, i)
        self.quality_combo.blockSignals(False)

    def _on_quality_selected(self, index):
        if index < 0:
            return
        vi = self.quality_combo.itemData(index)
        if vi is not None and get_shared_player and self.using_shared_player:
            get_shared_player().set_quality(vi)
            logger.info(f"Selected quality: index {vi}")


# ===================================================================
#  Standalone test
# ===================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    channel_mock = Channel.from_dict({
        "name": "Sample Channel",
        "stream_url": "http://commondatastorage.googleapis.com/"
                      "gtv-videos-bucket/sample/BigBuckBunny.mp4",
    })
    view = FullScreenView(channel_mock)
    view.go_back_signal.connect(app.quit)
    view.showFullScreen()
    sys.exit(app.exec_())
