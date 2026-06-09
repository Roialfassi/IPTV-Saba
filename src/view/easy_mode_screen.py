import logging
import sys
from typing import List, Dict, Optional
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QMessageBox, QProgressBar, QSlider)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor
import vlc

from src.model.profile import create_mock_profile, Profile
from src.utils.resource_path import resource_path
from src.utils.vlc_helpers import (
    vlc_instance_args,
    safe_release_player,
    safe_release_instance,
)

# Logging is configured centrally in iptv_app.py; just get a module logger.
logger = logging.getLogger(__name__)

# Constants
HIDE_CONTROLS_DELAY_MS = 2000  # Milliseconds to wait before hiding controls
DEFAULT_VOLUME = 50  # Default volume level (0-100)
WINDOW_ICON_PATH = resource_path("Assets/iptv-logo2.ico")

class EasyModeScreen(QWidget):
    """
    A simplified IPTV viewing screen designed for easy navigation.

    Provides a streamlined interface with large buttons for navigating
    through favorite channels, ideal for elderly users or remote control use.

    Attributes:
        exit_easy_mode_signal: Signal emitted when exiting Easy Mode.
        profile: The user profile containing favorites and settings.
        current_channel_index: Index of the currently playing channel in favorites.
    """
    exit_easy_mode_signal = pyqtSignal()  # Signal to emit when exiting Easy Mode

    def __init__(self, profile: Profile) -> None:
        """
        Initialize the Easy Mode screen.

        Args:
            profile: The user profile containing favorite channels to display.
        """
        super().__init__()
        self.profile = profile
        self.current_channel_index = 0
        # EasyMode keeps its own VLC instance (it does NOT use
        # SharedPlayerManager), but shares the same plugin-path detection.
        self.vlc_instance = vlc.Instance(vlc_instance_args())
        self.player = self.vlc_instance.media_player_new()
        self.init_ui()
        self.play_channel()
        self.hide_controls_timer = QTimer(self, interval=HIDE_CONTROLS_DELAY_MS)
        self.hide_controls_timer.timeout.connect(self.hide_controls)
        self.setMouseTracking(True)
        self.volume = DEFAULT_VOLUME
        self.player.audio_set_volume(self.volume)
        self.hide_controls_timer.start(HIDE_CONTROLS_DELAY_MS)
        self.is_fullscreen = False


    def init_ui(self) -> None:
        """Initialize the user interface components."""
        self.setWindowTitle('IPTV Easy Mode')
        self.setWindowIcon(QIcon(WINDOW_ICON_PATH))
        self.setStyleSheet("""
            QWidget {
                background-color: #141414;
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
            QProgressBar {
                border: 2px solid grey;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: rgba(229, 9, 20, 0.8);
                width: 10px;
                margin: 0.5px;
            }
        """)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Video frame
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_frame, 1)

        # Controls overlay
        self.controls_widget = QWidget(self)
        controls_layout = QVBoxLayout(self.controls_widget)
        controls_layout.setAlignment(Qt.AlignBottom)

        # Channel info
        channel_info_layout = QHBoxLayout()
        self.channel_label = QLabel()
        self.channel_label.setAlignment(Qt.AlignCenter)
        channel_info_layout.addWidget(self.channel_label)
        controls_layout.addLayout(channel_info_layout)

        # Buttons row
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignCenter)
        buttons_layout.setSpacing(12)

        self.prev_button = QPushButton("\u25C0  Previous")
        self.prev_button.setToolTip("Previous channel (Left arrow)")
        self.prev_button.clicked.connect(self.previous_channel)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(229, 9, 20, 0.8);
                border: none;
                color: white;
                padding: 14px 24px;
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                min-width: 150px;
                margin: 4px 2px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(229, 9, 20, 1);
            }
        """)
        buttons_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("Next  \u25B6")
        self.next_button.setToolTip("Next channel (Right arrow)")
        self.next_button.clicked.connect(self.next_channel)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(229, 9, 20, 0.8);
                border: none;
                color: white;
                padding: 14px 24px;
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                min-width: 150px;
                margin: 4px 2px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(229, 9, 20, 1);
            }
        """)
        buttons_layout.addWidget(self.next_button)

        self.exit_button = QPushButton("Exit Easy Mode")
        self.exit_button.setToolTip("Return to main interface (Escape)")
        self.exit_button.clicked.connect(self.exit_easy_mode)
        self.exit_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                border: 1px solid #666;
                color: white;
                padding: 14px 24px;
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        buttons_layout.addWidget(self.exit_button)

        self.fullscreen_button = QPushButton("Fullscreen")
        self.fullscreen_button.setToolTip("Toggle fullscreen (F)")
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.fullscreen_button.setStyleSheet("""
            QPushButton {
                background-color: #2c5282;
                border: 1px solid #3b6aa0;
                color: white;
                padding: 14px 24px;
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3b6aa0;
            }
        """)
        buttons_layout.addWidget(self.fullscreen_button)

        controls_layout.addLayout(buttons_layout)

        # Volume controls row
        volume_layout = QHBoxLayout()
        volume_layout.setAlignment(Qt.AlignCenter)
        volume_layout.setSpacing(10)

        self.vol_down_button = QPushButton("Vol -")
        self.vol_down_button.setToolTip("Decrease volume (Down arrow)")
        self.vol_down_button.clicked.connect(lambda: self._adjust_volume_step(-5))
        self.vol_down_button.setFixedSize(70, 50)
        self.vol_down_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                border: 1px solid #666;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        volume_layout.addWidget(self.vol_down_button)

        self.volume_label = QLabel(f"{DEFAULT_VOLUME}%")
        self.volume_label.setAlignment(Qt.AlignCenter)
        self.volume_label.setFixedWidth(80)
        self.volume_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        volume_layout.addWidget(self.volume_label)

        self.vol_up_button = QPushButton("Vol +")
        self.vol_up_button.setToolTip("Increase volume (Up arrow)")
        self.vol_up_button.clicked.connect(lambda: self._adjust_volume_step(5))
        self.vol_up_button.setFixedSize(70, 50)
        self.vol_up_button.setStyleSheet("""
            QPushButton {
                background-color: #444444;
                border: 1px solid #666;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #555555;
            }
        """)
        volume_layout.addWidget(self.vol_up_button)

        # Keep the slider for programmatic use but also as an option
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(DEFAULT_VOLUME)
        self.volume_slider.setToolTip("Adjust playback volume (0-100)")
        self.volume_slider.setFixedWidth(200)
        self.volume_slider.valueChanged.connect(self.adjust_volume)
        volume_layout.addWidget(self.volume_slider)

        controls_layout.addLayout(volume_layout)

        main_layout.addWidget(self.controls_widget)

        # Set up the VLC player
        self.player.set_hwnd(self.video_frame.winId())

        # Update UI timer
        self.update_timer = QTimer(self, interval=1000)  # Update every second

    def _adjust_volume_step(self, step: int) -> None:
        """Adjust volume by a step amount via buttons."""
        new_val = max(0, min(100, self.volume_slider.value() + step))
        self.volume_slider.setValue(new_val)

    def play_channel(self) -> None:
        """
        Play the currently selected channel from favorites.

        Loads the channel at current_channel_index and starts playback.
        If favorites list is empty, prompts the user to add channels.
        """
        if not self.profile.favorites:
            self.handle_empty_favorites()
            return

        channel = self.profile.favorites[self.current_channel_index]
        logger.debug(f"Playing channel: {channel.name}")
        media = self.vlc_instance.media_new(channel.stream_url)
        self.player.set_media(media)
        self.player.play()
        total = len(self.profile.favorites)
        pos = self.current_channel_index + 1
        self.channel_label.setText(f"{channel.name}  (Channel {pos} / {total})")

    def next_channel(self) -> None:
        """
        Navigate to and play the next channel in favorites.

        Wraps around to the first channel if at the end of the list.
        """
        if not self.profile.favorites:
            return

        self.current_channel_index = (self.current_channel_index + 1) % len(self.profile.favorites)
        self.play_channel()

    def previous_channel(self) -> None:
        """
        Navigate to and play the previous channel in favorites.

        Wraps around to the last channel if at the beginning of the list.
        """
        if not self.profile.favorites:
            return

        self.current_channel_index = (self.current_channel_index - 1) % len(self.profile.favorites)
        self.play_channel()

    def exit_easy_mode(self):
        """
        Exit Easy Mode with proper resource cleanup.

        Note: close() will trigger closeEvent which handles the actual cleanup.
        """
        self.exit_easy_mode_signal.emit()
        self.close()

    def handle_empty_favorites(self) -> None:
        """
        Handle the case when the favorites list is empty.

        Displays a dialog informing the user and exits Easy Mode
        regardless of user response since Easy Mode requires favorites.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Your favorites list is empty.")
        msg.setInformativeText("Would you like to add some channels to your favorites?")
        msg.setWindowTitle("Empty Favorites")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        ret = msg.exec_()

        if ret == QMessageBox.Yes:
            # Here you would typically navigate to the favorites management screen
            # For this example, we'll just exit Easy Mode
            self.exit_easy_mode()
        else:
            self.exit_easy_mode()

    def update_ui(self) -> None:
        """
        Periodic UI update callback.

        Currently a placeholder for future enhancements such as
        progress bar updates or stream status indicators.
        """
        pass

    def mouseMoveEvent(self, event) -> None:
        """
        Handle mouse movement to show controls.

        Args:
            event: The mouse move event.
        """
        self.show_controls()
        self.hide_controls_timer.start(HIDE_CONTROLS_DELAY_MS)

    def show_controls(self) -> None:
        """Show the control overlay and restore the cursor."""
        self.controls_widget.show()
        self.setCursor(Qt.ArrowCursor)

    def hide_controls(self) -> None:
        """Hide the control overlay and optionally hide cursor in fullscreen."""
        self.controls_widget.hide()
        if self.is_fullscreen:
            self.setCursor(Qt.BlankCursor)

    def keyPressEvent(self, event) -> None:
        """
        Handle keyboard shortcuts for Easy Mode.

        Supported keys:
            - Escape: Exit fullscreen or Easy Mode
            - Right Arrow: Next channel
            - Left Arrow: Previous channel
            - Space: Play/Pause toggle
            - Up Arrow: Volume up
            - Down Arrow: Volume down
            - F: Toggle fullscreen

        Args:
            event: The key press event.
        """
        # Show controls and reset hide timer on any keypress
        self.show_controls()
        self.hide_controls_timer.start(HIDE_CONTROLS_DELAY_MS)

        if event.key() == Qt.Key_Escape:
            if self.is_fullscreen:
                self.toggle_fullscreen()
            else:
                self.exit_easy_mode()
        elif event.key() == Qt.Key_Right:
            self.next_channel()
        elif event.key() == Qt.Key_Left:
            self.previous_channel()
        elif event.key() == Qt.Key_Space:
            if self.player.is_playing():
                self.player.pause()
            else:
                self.player.play()
        elif event.key() == Qt.Key_Up:
            self.volume_slider.setValue(min(100, self.volume_slider.value() + 5))
        elif event.key() == Qt.Key_Down:
            self.volume_slider.setValue(max(0, self.volume_slider.value() - 5))
        elif event.key() == Qt.Key_F:
            self.toggle_fullscreen()
        event.accept()

    def closeEvent(self, event):
        """
        Handle window close with proper VLC resource cleanup.

        Ensures VLC player and instance are properly released to prevent
        memory leaks and potential crashes.

        IMPORTANT: On Windows, calling player.stop() can cause access violations
        due to VLC's internal threading. We use a gentler approach:
        1. Pause first (safe operation)
        2. Set media to None
        3. Only then release resources
        """
        # Exit fullscreen first if needed
        if self.is_fullscreen:
            self.toggle_fullscreen()

        # Windows-safe VLC teardown (shared with SharedPlayerManager). Null out
        # the references so a later cleanup pass (e.g. app aboutToQuit) is a
        # no-op rather than a double-release.
        safe_release_player(getattr(self, 'player', None))
        self.player = None
        safe_release_instance(getattr(self, 'vlc_instance', None))
        self.vlc_instance = None

        event.accept()

    def toggle_fullscreen(self) -> None:
        """
        Toggle between fullscreen and normal window mode.

        In fullscreen mode, controls are initially hidden and cursor
        is hidden after inactivity. In normal mode, controls are shown.
        """
        if not self.is_fullscreen:
            self.showFullScreen()
            self.is_fullscreen = True
            self.fullscreen_button.setText("Exit Fullscreen")
            self.hide_controls_timer.stop()
            self.hide_controls()
        else:
            self.showNormal()
            self.is_fullscreen = False
            self.fullscreen_button.setText("Fullscreen")
            self.show_controls()
            self.hide_controls_timer.start(HIDE_CONTROLS_DELAY_MS)

    def adjust_volume(self, value: int) -> None:
        """
        Adjust the playback volume.

        Args:
            value: The new volume level (0-100).
        """
        self.volume = value
        self.player.audio_set_volume(self.volume)
        self.volume_label.setText(f"{value}%")


# Mock class for testing
class MockProfile:
    def __init__(self):
        self.favorites = [
            {"name": "Channel 1",
             "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"},
            {"name": "Channel 2",
             "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"},
            {"name": "Channel 3",
             "url": "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4"},
        ]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    test_profile = create_mock_profile()
    logger.info(f"Profile type: {type(test_profile)}")
    screen = EasyModeScreen(test_profile)
    screen.showFullScreen()
    sys.exit(app.exec_())
