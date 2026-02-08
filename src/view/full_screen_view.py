import sys
import logging
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QSlider, QComboBox,
                             QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
import vlc

from src.model.channel_model import Channel
from src.utils.resource_path import resource_path

# Import SharedPlayerManager for potential direct usage
try:
    from src.services.shared_player_manager import get_shared_player, SharedPlayerManager
except ImportError:
    get_shared_player = None
    SharedPlayerManager = None

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Constants
HIDE_CONTROLS_DELAY_MS = 2000  # Milliseconds to wait before hiding controls
HIDE_CONTROLS_MOUSE_DELAY_MS = 5000  # Delay when mouse moves
DEFAULT_VOLUME = 50  # Default volume level (0-100)
WINDOW_ICON_PATH = resource_path("Assets/iptv-logo2.ico")


class FullScreenView(QWidget):
    """
    A full-screen media player that takes a URL, plays the channel, and provides limited controls.
    Keys include: back to `ChooseChannelScreen`, volume control, and play/pause.

    NOTE: This view reuses the existing VLC player instance to avoid dual streams.
    """

    go_back_signal = pyqtSignal()  # Signal to emit when going back to ChooseChannelScreen

    def __init__(self, channel: Channel, existing_player=None, existing_instance=None):
        super().__init__()
        self.channel_name = channel.name
        self.stream_url = channel.stream_url

        # Reuse existing player if provided to avoid dual streams
        if existing_player and existing_instance:
            self.vlc_instance = existing_instance
            self.player = existing_player
            self.is_playing = True  # Already playing
            self.using_shared_player = True  # Track that we're using shared player
            logger.info("Reusing existing VLC player instance (seamless transition)")
        else:
            self.vlc_instance = vlc.Instance()
            self.player = self.vlc_instance.media_player_new()
            self.is_playing = False
            self.using_shared_player = False
            logger.info("Created new VLC player instance")

        self.is_muted = False
        self.init_ui()
        self.setMouseTracking(True)

        # Only start playing if we created a new player
        if not (existing_player and existing_instance):
            self.play_channel()
        else:
            # Just update the UI to reflect current state
            self.play_pause_button.setText("Pause")

        # Connect to SharedPlayerManager signals for audio/subtitle tracks
        self._connect_track_signals()

        self.hide_controls_timer = QTimer(self, interval=HIDE_CONTROLS_DELAY_MS)
        self.hide_controls_timer.timeout.connect(self.hide_controls)
        self.hide_controls_timer.start(HIDE_CONTROLS_DELAY_MS)

    def init_ui(self):
        self.setWindowTitle('Full Screen Channel View')
        self.setWindowIcon(QIcon(WINDOW_ICON_PATH))
        self.setStyleSheet("""
            QWidget {
                background-color: #141414;
                color: #FFFFFF;
                font-family: Arial, sans-serif;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Video frame
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_frame, 1)

        # Controls layout
        self.controls_widget = QWidget(self)
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.controls_widget)

        # Back Button
        self.back_button = QPushButton("Back to Channels")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(229, 9, 20, 0.8);
                border: none;
                color: white;
                padding: 5px 10px;
                text-align: center;
                font-size: 12px;
                margin: 2px 1px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: rgba(229, 9, 20, 1);
            }
        """)
        controls_layout.addWidget(self.back_button)

        # Play/Pause Button
        self.play_pause_button = QPushButton("Pause")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(229, 9, 20, 0.8);
                border: none;
                color: white;
                padding: 5px 10px;
                text-align: center;
                font-size: 12px;
                margin: 2px 1px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: rgba(229, 9, 20, 1);
            }
        """)
        controls_layout.addWidget(self.play_pause_button)

        # Volume Slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(DEFAULT_VOLUME)
        self.volume_slider.setToolTip("Adjust playback volume (0-100)")
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_layout.addWidget(QLabel("Volume"))
        controls_layout.addWidget(self.volume_slider)

        # Audio Track Combo Box
        controls_layout.addWidget(QLabel("Audio:"))
        self.audio_combo = QComboBox()
        self.audio_combo.setMinimumWidth(120)
        self.audio_combo.setToolTip("Select audio track")
        self.audio_combo.setStyleSheet("""
            QComboBox {
                background-color: #2c2c2c;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #E50914;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2c2c2c;
                color: white;
                selection-background-color: #E50914;
            }
        """)
        self.audio_combo.currentIndexChanged.connect(self._on_audio_track_selected)
        controls_layout.addWidget(self.audio_combo)

        # Subtitle Track Combo Box
        controls_layout.addWidget(QLabel("Subtitles:"))
        self.subtitle_combo = QComboBox()
        self.subtitle_combo.setMinimumWidth(120)
        self.subtitle_combo.setToolTip("Select subtitle track")
        self.subtitle_combo.setStyleSheet("""
            QComboBox {
                background-color: #2c2c2c;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #E50914;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2c2c2c;
                color: white;
                selection-background-color: #E50914;
            }
        """)
        self.subtitle_combo.currentIndexChanged.connect(self._on_subtitle_track_selected)
        controls_layout.addWidget(self.subtitle_combo)

        # Load External Subtitle Button
        self.load_subtitle_button = QPushButton("Load SRT")
        self.load_subtitle_button.setToolTip("Load external subtitle file")
        self.load_subtitle_button.clicked.connect(self._load_external_subtitle)
        self.load_subtitle_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(44, 44, 44, 0.8);
                border: 1px solid #444;
                color: white;
                padding: 5px 10px;
                text-align: center;
                font-size: 12px;
                margin: 2px 1px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: rgba(229, 9, 20, 0.8);
                border: 1px solid #E50914;
            }
        """)
        controls_layout.addWidget(self.load_subtitle_button)

        # Quality Selection Combo Box
        controls_layout.addWidget(QLabel("Quality:"))
        self.quality_combo = QComboBox()
        self.quality_combo.setMinimumWidth(100)
        self.quality_combo.setToolTip("Select stream quality")
        self.quality_combo.addItem("Auto", 0)
        self.quality_combo.setStyleSheet("""
            QComboBox {
                background-color: #2c2c2c;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px 8px;
                min-width: 80px;
            }
            QComboBox:hover {
                border: 1px solid #E50914;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #2c2c2c;
                color: white;
                selection-background-color: #E50914;
            }
        """)
        self.quality_combo.currentIndexChanged.connect(self._on_quality_selected)
        controls_layout.addWidget(self.quality_combo)

        # Channel name label
        self.channel_label = QLabel(self.channel_name)
        self.channel_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.channel_label)

        # Timer to update the UI
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)

    def attach_player_to_window(self):
        """
        Attach the VLC player to the video frame window using platform-specific methods.
        This must be called AFTER the widget is shown to ensure valid window ID.
        """
        if not self.player:
            logger.warning("No player to attach")
            return

        if not hasattr(self, 'video_frame'):
            logger.warning("No video frame to attach to")
            return

        try:
            win_id = int(self.video_frame.winId())
            logger.info(f"FullScreenView: Attempting to attach player to window ID: {win_id}")
            
            # Check if player was playing before attachment
            was_playing = self.player.is_playing()
            logger.info(f"FullScreenView: Player was_playing={was_playing}")

            if sys.platform.startswith('linux'):
                self.player.set_xwindow(win_id)
                logger.info(f"✓ Attached player to Linux X11 window: {win_id}")
            elif sys.platform == "win32":
                self.player.set_hwnd(win_id)
                logger.info(f"✓ Attached player to Windows HWND: {win_id}")
            elif sys.platform == "darwin":
                self.player.set_nsobject(win_id)
                logger.info(f"✓ Attached player to macOS NSObject: {win_id}")
            else:
                logger.error(f"Unsupported platform: {sys.platform}")
                return

            # CRITICAL: Force video to refresh after window change
            # Need to give the player time to recognize the new window
            QTimer.singleShot(150, self._refresh_video_after_attach)

        except Exception as e:
            logger.error(f"Error attaching player to window: {e}")
            import traceback
            traceback.print_exc()
    
    def _refresh_video_after_attach(self):
        """Force the video to refresh after attaching to new window."""
        try:
            if not self.player:
                return
                
            logger.info(f"FullScreenView: Refreshing video. is_playing={self.player.is_playing()}")
            
            if self.player.is_playing():
                # Save position
                current_pos = self.player.get_position()
                logger.info(f"FullScreenView: Current position before refresh: {current_pos}")
                
                # The trick: pause briefly, then resume to force re-render to new window
                self.player.pause()
                
                def resume_playback():
                    if self.player:
                        self.player.play()
                        logger.info("FullScreenView: Resumed playback after refresh")
                        # Restore position if needed
                        if current_pos and current_pos > 0.0:
                            QTimer.singleShot(50, lambda: self.player.set_position(current_pos))
                
                QTimer.singleShot(100, resume_playback)
            else:
                # Player wasn't playing, start it
                logger.info("FullScreenView: Player not playing - starting playback")
                self.player.play()
                
        except Exception as e:
            logger.error(f"Error refreshing video: {e}")

    def showEvent(self, event):
        """
        Called when the widget is shown.
        
        If using shared player (state machine), don't attach here - the 
        SharedPlayerManager handles the transition. Only attach if we 
        created our own player.
        """
        super().showEvent(event)
        
        if self.using_shared_player:
            # SharedPlayerManager's state machine handles attachment
            logger.info("FullScreenView showEvent - using shared player (state machine handles attachment)")
        else:
            # We created our own player, need to attach it
            logger.info("FullScreenView showEvent - own player, scheduling attachment")
            QTimer.singleShot(200, self.attach_player_to_window)

    def play_channel(self):
        """
        Play the channel stream provided in the URL.
        """
        media = self.vlc_instance.media_new(self.stream_url)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True
        self.play_pause_button.setText("Pause")

    def toggle_play_pause(self):
        """
        Toggle between play and pause.
        """
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
            self.play_pause_button.setText("Play")
        else:
            self.player.play()
            self.is_playing = True
            self.play_pause_button.setText("Pause")

    def set_volume(self, volume):
        """
        Set the volume of the player.
        """
        self.player.audio_set_volume(volume)

    def go_back(self):
        """
        Emit a signal to go back to the ChooseChannelScreen.
        NOTE: We don't stop the player here anymore since it's shared with ChooseChannelScreen.
        """
        # Don't stop the player - let ChooseChannelScreen handle it
        self.go_back_signal.emit()

    def keyPressEvent(self, event):
        """
        Handle key events for basic control: back, mute/unmute, and volume control.
        """
        if event.key() == Qt.Key_Escape:
            self.go_back()
        elif event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        elif event.key() == Qt.Key_Up:
            # Increase volume by 10
            current_volume = self.player.audio_get_volume()
            self.set_volume(min(current_volume + 10, 100))
            self.volume_slider.setValue(min(current_volume + 10, 100))
        elif event.key() == Qt.Key_Down:
            # Decrease volume by 10
            current_volume = self.player.audio_get_volume()
            self.set_volume(max(current_volume - 10, 0))
            self.volume_slider.setValue(max(current_volume - 10, 0))
        event.accept()

    def update_ui(self):
        """
        Update the UI periodically (optional, can be extended for more features).
        """
        pass

    def closeEvent(self, event):
        """
        Handle window close event.

        If using shared player, don't stop or release - the ChooseChannelScreen
        will continue using it. Only cleanup if we created our own player.

        IMPORTANT: On Windows, calling player.stop() can cause access violations.
        We use a safer cleanup approach: pause, set media to None, then release.
        """
        if not self.using_shared_player and self.player:
            # We created our own player, so we should clean it up
            try:
                # Pause first instead of stop (safer on Windows)
                if self.player.is_playing():
                    self.player.set_pause(1)

                # Set media to None to help release internal resources
                try:
                    self.player.set_media(None)
                except Exception:
                    pass

                # On Windows, skip stop() as it can crash
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
            logger.info("Using shared player - skipping cleanup (player continues in channel browser)")

        event.accept()

    def mouseMoveEvent(self, event):
        self.show_controls()
        self.hide_controls_timer.start(HIDE_CONTROLS_MOUSE_DELAY_MS)

    def show_controls(self):
        self.controls_widget.show()
        self.setCursor(Qt.ArrowCursor)

    def hide_controls(self):
        self.controls_widget.hide()
        # if self.is_fullscreen:
        #     self.setCursor(Qt.BlankCursor)

    # ==================== Audio/Subtitle Track Methods ====================

    def _connect_track_signals(self):
        """Connect to SharedPlayerManager signals for audio/subtitle/quality track updates."""
        if get_shared_player and self.using_shared_player:
            shared_player = get_shared_player()
            shared_player.audio_tracks_available.connect(self._on_audio_tracks_available)
            shared_player.subtitles_available.connect(self._on_subtitles_available)
            shared_player.quality_variants_available.connect(self._on_quality_variants_available)
            logger.info("Connected to SharedPlayerManager track signals")

            # Populate existing quality variants if any
            variants = shared_player.get_quality_variants()
            if variants:
                self._on_quality_variants_available(variants)

    def _on_audio_tracks_available(self, tracks):
        """
        Handle audio tracks becoming available.

        Args:
            tracks: List of (track_id, track_name) tuples
        """
        logger.info(f"Audio tracks available: {len(tracks)}")
        self.audio_combo.blockSignals(True)
        self.audio_combo.clear()
        for track_id, track_name in tracks:
            self.audio_combo.addItem(track_name, track_id)
        self.audio_combo.blockSignals(False)

        # Select current track
        if get_shared_player:
            current = get_shared_player().get_current_audio_track()
            for i in range(self.audio_combo.count()):
                if self.audio_combo.itemData(i) == current:
                    self.audio_combo.setCurrentIndex(i)
                    break

    def _on_subtitles_available(self, tracks):
        """
        Handle subtitle tracks becoming available.

        Args:
            tracks: List of (track_id, track_name) tuples
        """
        logger.info(f"Subtitle tracks available: {len(tracks)}")
        self.subtitle_combo.blockSignals(True)
        self.subtitle_combo.clear()
        for track_id, track_name in tracks:
            self.subtitle_combo.addItem(track_name, track_id)
        self.subtitle_combo.blockSignals(False)

        # Select current track
        if get_shared_player:
            current = get_shared_player().get_current_subtitle_track()
            for i in range(self.subtitle_combo.count()):
                if self.subtitle_combo.itemData(i) == current:
                    self.subtitle_combo.setCurrentIndex(i)
                    break

    def _on_audio_track_selected(self, index):
        """Handle audio track selection from combo box."""
        if index < 0:
            return
        track_id = self.audio_combo.itemData(index)
        if track_id is not None:
            if get_shared_player and self.using_shared_player:
                get_shared_player().set_audio_track(track_id)
            elif self.player:
                self.player.audio_set_track(track_id)
            logger.info(f"Selected audio track: {track_id}")

    def _on_subtitle_track_selected(self, index):
        """Handle subtitle track selection from combo box."""
        if index < 0:
            return
        track_id = self.subtitle_combo.itemData(index)
        if track_id is not None:
            if get_shared_player and self.using_shared_player:
                get_shared_player().set_subtitle_track(track_id)
            elif self.player:
                self.player.video_set_spu(track_id)
            logger.info(f"Selected subtitle track: {track_id}")

    def _load_external_subtitle(self):
        """Load an external subtitle file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Subtitle File",
            "",
            "Subtitle Files (*.srt *.sub *.ass *.ssa *.vtt);;All Files (*)"
        )
        if file_path:
            if get_shared_player and self.using_shared_player:
                success = get_shared_player().load_external_subtitle(file_path)
            elif self.player:
                success = self.player.video_set_subtitle_file(file_path)
            else:
                success = False

            if success:
                logger.info(f"Loaded external subtitle: {file_path}")
            else:
                logger.error(f"Failed to load subtitle: {file_path}")

    # ==================== Quality Selection Methods ====================

    def _on_quality_variants_available(self, variants):
        """
        Handle quality variants becoming available.

        Args:
            variants: List of QualityVariant objects
        """
        logger.info(f"Quality variants available: {len(variants)}")
        self.quality_combo.blockSignals(True)
        self.quality_combo.clear()
        self.quality_combo.addItem("Auto", 0)
        for i, variant in enumerate(variants, start=1):
            self.quality_combo.addItem(variant.display_name, i)
        self.quality_combo.blockSignals(False)

    def _on_quality_selected(self, index):
        """Handle quality selection from combo box."""
        if index < 0:
            return
        variant_index = self.quality_combo.itemData(index)
        if variant_index is not None and get_shared_player and self.using_shared_player:
            get_shared_player().set_quality(variant_index)
            logger.info(f"Selected quality: index {variant_index}")


# Testing the FullScreenView class
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Sample channel details
    channel_name = "Sample Channel"
    stream_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    channel_mock = Channel.from_dict({"name" : channel_name, "stream_url": stream_url})
    full_screen_view = FullScreenView(channel_mock)

    # Connect go_back_signal to a function (for now just closing the app)
    full_screen_view.go_back_signal.connect(app.quit)

    full_screen_view.showFullScreen()
    sys.exit(app.exec_())
