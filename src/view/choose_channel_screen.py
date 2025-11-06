import logging
import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QLabel, QListWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QSlider, QMessageBox, QSplitter,
    QApplication, QSizePolicy, QMenu, QAction, QGraphicsOpacityEffect
)
from PyQt5.QtCore import Qt, pyqtSlot, QObject, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QThread
from PyQt5.QtGui import QFont, QIcon
import vlc

from src.controller.controller import Controller
from src.data.data_loader import DataLoader
from src.model.group_model import Group  # for type hints
from src.model.channel_model import Channel  # for type hints
from src.model.profile import create_mock_profile, Profile
from src.view.full_screen_view import FullScreenView
from src.services.download_record_manager import DownloadRecordManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class LoaderWorker(QObject):
    """Worker thread for loading IPTV data without blocking the UI"""
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller
        self.loader = controller.data_loader
        self.source = controller.active_profile.url
        self.active_profile = controller.active_profile
        self.config_dir = controller.config_dir

    def run(self):
        try:
            data_path = Path(os.path.join(self.config_dir, (self.active_profile.name + "data.json")))
            # load from File
            print(type(self.active_profile))
            if self.active_profile.is_within_24_hours() is True and data_path.is_file():
                logger.info("Loading Data from file since last login was recently")
                self.loader.load_from_json(data_path)
            else:
                success = self.loader.load(self.source)
                if not success:
                    self.error.emit("Failed to load IPTV data")
                    logger.info("Loading Data from file since last login was recently")
                    self.loader.load_from_json(data_path)
                else:
                    self.loader.save_to_json(data_path)
                    self.controller.active_profile.update_last_loaded()
                    self.controller.profile_manager.update_profile(self.controller.active_profile)
                    self.controller.profile_manager.export_profiles(self.controller.profile_path)
            self.finished.emit()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            self.error.emit(f"Error loading IPTV data: {str(e)}")
            self.finished.emit()


class LoadingOverlay(QWidget):
    """Custom overlay widget with loading animation"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Make the overlay transparent for mouse events
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Set up the overlay
        self.setStyleSheet("background-color: rgba(0, 0, 0, 180);")

        # Create loading indicator
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Loading spinner animation (use Unicode character for simplicity)
        self.spinner_label = QLabel("⟳")
        self.spinner_label.setAlignment(Qt.AlignCenter)
        self.spinner_label.setStyleSheet("""
            font-size: 70px;
            color: #E50914;
        """)
        layout.addWidget(self.spinner_label)

        # Loading text
        self.text_label = QLabel("Loading channels...")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("""
            font-size: 20px;
            color: white;
            margin-top: 10px;
        """)
        layout.addWidget(self.text_label)

        # Start rotation animation
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_spinner)
        self.timer.start(30)  # Update every 30ms for smooth animation

        # Initially hidden
        self.hide()

    def rotate_spinner(self):
        """Rotate the spinner character"""
        self.angle = (self.angle + 5) % 360
        self.spinner_label.setStyleSheet(f"""
            font-size: 70px;
            color: #E50914;
            transform: rotate({self.angle}deg);
        """)

    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        # Create fade-in effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(500)
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.opacity_anim.start()

    def hideEvent(self, event):
        """Handle hide event"""
        super().hideEvent(event)
        self.timer.stop()

    def update_text(self, text):
        """Update the loading text"""
        self.text_label.setText(text)


class ChooseChannelScreen(QWidget):
    logout_signal = pyqtSignal(str)

    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.all_groups = {}  # Keep a copy for filtering
        self.controller = controller
        self.init_ui()
        self.connect_signals()
        # self.load_groups()
        self.active_channel = None
        self.fullscreen_view = None
        self.thread = None
        self.worker = None

        # Initialize download/record manager
        downloads_dir = os.path.join(controller.config_dir, "downloads")
        self.download_manager = DownloadRecordManager(downloads_dir)
        self.setup_download_manager_signals()

        # Track active downloads/recordings
        self.active_recordings = {}  # {channel_name: recording_id}

        # Init loading overlay
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()
        # Start loading data with progress indicators
        QTimer.singleShot(100, self.load_playlist_with_progress)

    def init_ui(self):
        self.setWindowTitle("IPTV - Choose Channel")
        self.setMinimumSize(800, 600)
        self.resize(1200, 700)

        # Overall stylesheet for a futuristic look with a compact header
        self.setStyleSheet("""       
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #121212, stop:1 #0d0d0d);
                color: #FFFFFF;
                font-family: 'Netflix Sans', Arial, sans-serif;
            }
            
            /* Compact Header styling */
            QLabel#headerLabel {
                font-size: 20px;
                font-weight: bold;
                color: #E50914;
            }
            
            QWidget#headerWidget {
                background-color: #1a1a1a;
                border-bottom: 1px solid #333;
            }
            
            /* List and input fields */
            QListWidget, QLineEdit {
                background-color: #2c2c2c;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px;
                color: #FFFFFF;
            }
            
            QListWidget::item:selected {
                background-color: #E50914;
                color: #FFFFFF;
            }
            
            QLineEdit:focus, QListWidget:focus {
                border: 1px solid #E50914;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #E50914;
                color: #FFFFFF;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 16px;
            }
            
            QPushButton:hover {
                background-color: #F6121D;
            }
            
            QPushButton:pressed {
                background-color: #BF0811;
            }
            
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
            
            /* Sliders */
            QSlider::groove:horizontal {
                height: 4px;
                background: #444;
                border-radius: 2px;
            }
            
            QSlider::handle:horizontal {
                background: #E50914;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ---------- Compact Header with Logout Button ----------
        header_widget = QWidget()
        header_widget.setObjectName("headerWidget")
        header_widget.setFixedHeight(50)
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(10)
        header_layout.addStretch()

        self.logout_button = QPushButton("Logout")
        header_layout.addWidget(self.logout_button)
        self.logout_button.clicked.connect(self.logout)
        main_layout.addWidget(header_widget)

        # ---------- Main Content Splitter ----------
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(2)
        main_layout.addWidget(main_splitter)

        # ---------- Left Panel ----------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(10)

        # Search Bar for Groups
        self.group_search_bar = QLineEdit()
        self.group_search_bar.setPlaceholderText("Search Groups...")
        self.group_search_bar.setFont(QFont("Segoe UI", 12))
        left_layout.addWidget(self.group_search_bar)
        self.group_search_bar.textChanged.connect(self.filter_groups)

        # List of Groups (populated from groups_dict)
        self.group_list = QListWidget()
        self.group_list.setFont(QFont("Segoe UI", 12))
        self.group_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self.group_list)
        self.group_list.itemClicked.connect(self.on_group_selected)

        # Search Bar for Channels
        self.channel_search_bar = QLineEdit()
        self.channel_search_bar.setPlaceholderText("Search Channels...")
        self.channel_search_bar.setFont(QFont("Segoe UI", 12))
        left_layout.addWidget(self.channel_search_bar)
        self.channel_search_bar.textChanged.connect(self.filter_channels)

        # List of Channels
        self.channel_list = QListWidget()
        self.channel_list.setFont(QFont("Segoe UI", 12))
        self.channel_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self.channel_list)

        main_splitter.addWidget(left_widget)

        # ---------- Right Panel ----------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 10, 10, 10)
        right_layout.setSpacing(10)

        # Video Player Area
        self.video_frame = QWidget()
        self.video_frame.setStyleSheet("background-color: #000000;")
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout.addWidget(self.video_frame)

        # Initialize VLC player
        vlc_plugins_path = r'C:\Program Files\VideoLAN\VLC\plugins'  # Update if needed
        args = ['--no-plugins-cache', '--plugin-path=' + vlc_plugins_path]
        self.instance = vlc.Instance(args)
        self.player = self.instance.media_player_new()

        # Playback Controls Layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        self.play_button = QPushButton("Play")
        controls_layout.addWidget(self.play_button)
        self.pause_button = QPushButton("Pause")
        controls_layout.addWidget(self.pause_button)
        self.stop_button = QPushButton("Stop")
        controls_layout.addWidget(self.stop_button)
        self.fullscreen_button = QPushButton("Fullscreen")
        controls_layout.addWidget(self.fullscreen_button)
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume")
        volume_layout.addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        volume_layout.addWidget(self.volume_slider)
        controls_layout.addLayout(volume_layout)
        right_layout.addLayout(controls_layout)

        # Favorites and History Buttons Layout
        favorites_history_layout = QHBoxLayout()
        favorites_history_layout.setSpacing(10)
        self.favorites_button = QPushButton("Favorites")
        favorites_history_layout.addWidget(self.favorites_button)
        self.history_button = QPushButton("History")
        favorites_history_layout.addWidget(self.history_button)
        right_layout.addLayout(favorites_history_layout)

        main_splitter.addWidget(right_widget)
        main_splitter.setSizes([300, 900])  # Adjust panel sizes as desired

    def connect_signals(self):
        # Group search
        self.group_search_bar.textChanged.connect(self.filter_groups)

        # Channel search
        self.channel_search_bar.textChanged.connect(self.filter_channels)

        # Group selection
        self.group_list.itemClicked.connect(self.on_group_selected)

        # Channel selection
        self.channel_list.itemClicked.connect(self.on_channel_selected)

        # Playback controls
        self.play_button.clicked.connect(self.play_channel)
        self.pause_button.clicked.connect(self.pause_channel)
        self.stop_button.clicked.connect(self.stop_channel)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.volume_slider.valueChanged.connect(self.set_volume)

        # Favorites and History
        self.favorites_button.clicked.connect(self.show_favorites)
        self.history_button.clicked.connect(self.show_history)

        # Context Menu for Channels
        self.channel_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.channel_list.customContextMenuRequested.connect(self.open_context_menu)

        # Controller signals
        self.controller.data_loaded.connect(self.on_data_loaded)
        self.controller.error_occurred.connect(self.show_error)

    def load_playlist_with_progress(self):
        try:
            """Start loading the playlist with progress indicators"""
            # Show loading overlay
            self.loading_overlay.resize(self.size())
            self.loading_overlay.show()

            # Create and configure worker thread
            self.thread = QThread()
            self.worker = LoaderWorker(self.controller)
            self.worker.moveToThread(self.thread)

            # Connect signals
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            self.thread.finished.connect(self.on_loading_finished)
            self.worker.error.connect(self.show_error)

            # Start the thread
            self.thread.start()
        except Exception as e:
            print(e)
            self.show_error(f"Failed to start loading: {str(e)}")


    def on_loading_finished(self):
        """Called when loading has completed"""
        # Hide loading overlay
        self.loading_overlay.hide()
        self.load_groups()

        # # Select first group if any
        # if self.group_list.count() > 0:
        #     self.group_list.setCurrentRow(0)
        #     selected_item = self.group_list.item(0)
        #     if selected_item:
        #         self.on_group_selected()

    def load_groups(self):
        """
        Loads groups from the Controller and populates the group list.
        """
        self.group_list.clear()
        groups = self.controller.list_groups()
        self.all_groups = groups  # Keep a copy for filtering
        self.group_list.addItems(groups)

    def populate_group_list(self):
        """Populate the group list widget using the keys from groups_dict."""
        self.group_list.clear()
        for group_name in sorted(self.groups_dict.keys()):
            self.group_list.addItem(group_name)

    def filter_groups(self, text: str):
        """
        Filters the group list based on the search text.
        """
        self.group_list.clear()
        filtered_groups = [group for group in self.all_groups if text.lower() in group.lower()]
        self.group_list.addItems(filtered_groups)

    def filter_channels(self, text: str):
        """
        Filters the channel list based on the search text.
        """
        if self.channel_list:
            self.channel_list.clear()
            filtered_channels = [channel for channel in self.all_channels if text.lower() in channel.lower()]
            self.channel_list.addItems(filtered_channels)


    def on_channel_selected(self):
        """
        Handles the event when a channel is selected.
        Plays the selected channel's stream.
        """
        selected_item = self.channel_list.currentItem()
        if selected_item:
            channel_name = selected_item.text()
            channel = self.controller.find_channel_by_name(channel_name)
            if channel and channel.stream_url:
                self.play_stream(channel.stream_url)
                self.add_to_history(channel)
                self.active_channel = channel
            else:
                QMessageBox.critical(self, "Stream Error", "Selected channel does not have a valid stream URL.")

    def play_stream(self, stream_url):
        """
        Plays the given stream URL in the video player.

        Args:
            stream_url (str): The URL of the stream to play.
        """
        try:
            if sys.platform.startswith('linux'):  # for Linux using the X Server
                self.player.set_xwindow(self.video_frame.winId())
            elif sys.platform == "win32":  # for Windows
                self.player.set_hwnd(self.video_frame.winId())
            elif sys.platform == "darwin":  # for MacOS
                self.player.set_nsobject(int(self.video_frame.winId()))
            else:
                QMessageBox.critical(self, "Platform Error", "Unsupported platform for video playback.")
                return

            media = self.instance.media_new(stream_url)
            self.player.set_media(media)
            self.player.play()
        except Exception as e:
            QMessageBox.critical(self, "Playback Error", f"An error occurred while trying to play the stream:\n{e}")

    def play_channel(self):
        """
        Plays or resumes the video stream.
        """
        if self.player:
            self.player.play()

    def pause_channel(self):
        """
        Pauses the video stream.
        """
        if self.player:
            self.player.pause()

    def stop_channel(self):
        """
        Stops the video stream.
        """
        if self.player:
            self.player.stop()

    def toggle_fullscreen(self):
        """
        Toggles fullscreen mode for the video player.
        """
        if self.active_channel:
            self.open_fullscreen_view(self.active_channel)
        else:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

    def set_volume(self, value):
        """
        Sets the playback volume.

        Args:
            value (int): Volume level (0-100).
        """
        if self.player:
            self.player.audio_set_volume(value)

    def set_position(self, position):
        """
        Seeks to the specified position in the video stream.

        Args:
            position (int): Position value (0-1000).
        """
        if self.player:
            self.player.set_position(position / 1000.0)

    def add_to_history(self, channel: Channel):
        """
        Adds the watched channel to the history.

        Args:
            channel (Channel): Channel
        """
        self.controller.add_to_history(channel)

    def show_favorites(self):
        """
        Displays the favorites channels.
        """
        if not self.controller.active_profile.favorites:
            QMessageBox.information(self, "Favorites", "No favorites added yet.")
            return

        self.channel_list.clear()
        self.channel_list.addItems(self.controller.active_profile.list_channels_in_favorites())

    def show_history(self):
        """
        Displays the recently watched channels.
        """
        if not self.controller.active_profile.history:
            QMessageBox.information(self, "History", "No channels watched yet.")
            return

        self.channel_list.clear()
        self.channel_list.addItems(self.controller.active_profile.list_channels_in_history())

    def open_context_menu(self, position):
        """
        Opens a context menu for channel list items.

        Args:
            position (QPoint): Position where the menu is requested.
        """
        selected_item = self.channel_list.currentItem()
        if not selected_item:
            return

        channel_name = selected_item.text()
        channel = self.controller.find_channel_by_name(channel_name)

        menu = QMenu()

        add_favorite_action = QAction("Add to Favorites", self)
        add_favorite_action.triggered.connect(self.add_selected_to_favorites)
        menu.addAction(add_favorite_action)

        remove_favorite_action = QAction("Remove from Favorites", self)
        remove_favorite_action.triggered.connect(self.remove_selected_from_favorites)
        menu.addAction(remove_favorite_action)

        menu.addSeparator()

        # Download/Record options
        if channel and channel.stream_url:
            if self.download_manager.is_media_file(channel.stream_url):
                # It's a downloadable media file
                download_action = QAction("📥 Download", self)
                download_action.triggered.connect(lambda: self.download_channel(channel))
                menu.addAction(download_action)
            else:
                # It's a livestream - can record
                if channel_name in self.active_recordings:
                    # Currently recording
                    stop_record_action = QAction("⏹️ Stop Recording", self)
                    stop_record_action.triggered.connect(lambda: self.stop_recording_channel(channel))
                    menu.addAction(stop_record_action)
                else:
                    # Not recording
                    record_action = QAction("🔴 Start Recording", self)
                    record_action.triggered.connect(lambda: self.start_recording_channel(channel))
                    menu.addAction(record_action)

        menu.exec_(self.channel_list.viewport().mapToGlobal(position))

    def add_selected_to_favorites(self):
        """
        Adds the selected channel to favorites.
        """
        selected_item = self.channel_list.currentItem()
        if selected_item:
            channel_name = selected_item.text()
            self.add_to_favorites(channel_name)

    def remove_selected_from_favorites(self):
        """
        Removes the selected channel from favorites.
        """
        selected_item = self.channel_list.currentItem()
        if selected_item:
            channel_name = selected_item.text()
            self.remove_from_favorites(channel_name)

    def add_to_favorites(self, channel_name: str):
        """
        Adds a channel to the favorites list via the Controller.
        """
        self.controller.add_to_favorites(channel_name)

    def remove_from_favorites(self, channel_name: str):
        """
        Removes a channel from the favorites list via the Controller.
        """
        self.controller.remove_from_favorites(channel_name)

    @pyqtSlot(dict)
    def on_data_loaded(self, groups: dict):
        """
        Slot to receive loaded group data from the controller.
        Expects a dictionary with group names as keys and Group objects as values.
        """
        self.groups_dict = groups
        self.populate_group_list()

    @pyqtSlot()
    def on_group_selected(self):
        """
        Handles the event when a group is selected.
        Loads and displays channels within the selected group.
        """
        selected_item = self.group_list.currentItem()
        if selected_item:
            group_name = selected_item.text()
            self.channel_list.clear()
            channels = self.controller.list_channels_in_group(group_name)
            self.all_channels = channels  # Keep a copy for filtering
            self.channel_list.addItems(channels)

    def populate_channel_list(self, channel_names: list):
        """Populate the channel list widget using a list of channel names."""
        self.channel_list.clear()
        for name in sorted(channel_names):
            self.channel_list.addItem(name)

    @pyqtSlot(str)
    def on_error_occurred(self, error_message: str):
        """Display error messages emitted by the controller."""
        QMessageBox.critical(self, "Error", error_message)

    @pyqtSlot(str)
    def show_error(self, message: str):
        """
        Displays an error message to the user.

        Args:
            message (str): The error message to display.
        """
        QMessageBox.critical(self, "Error", message)

    def setup_download_manager_signals(self):
        """Setup signals for download/record manager."""
        self.download_manager.download_progress.connect(self.on_download_progress)
        self.download_manager.download_complete.connect(self.on_download_complete)
        self.download_manager.download_error.connect(self.on_download_error)
        self.download_manager.recording_started.connect(self.on_recording_started)
        self.download_manager.recording_stopped.connect(self.on_recording_stopped)

    def download_channel(self, channel: Channel):
        """Start downloading a media file."""
        download_id = f"download_{channel.name}_{id(channel)}"

        reply = QMessageBox.question(
            self, 'Download Channel',
            f"Download '{channel.name}'?\n\nFile will be saved to:\n{self.download_manager.downloads_dir}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.download_manager.start_download(download_id, channel.name, channel.stream_url)
            if success:
                QMessageBox.information(
                    self, 'Download Started',
                    f"Download started for '{channel.name}'\n\nCheck the downloads folder for progress."
                )
            else:
                QMessageBox.warning(
                    self, 'Download Failed',
                    f"Failed to start download for '{channel.name}'"
                )

    def start_recording_channel(self, channel: Channel):
        """Start recording a livestream."""
        recording_id = f"record_{channel.name}_{id(channel)}"

        reply = QMessageBox.question(
            self, 'Record Channel',
            f"Start recording '{channel.name}'?\n\nRecording will be saved to:\n{self.download_manager.downloads_dir}\n\nYou can stop recording from the context menu.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.download_manager.start_recording(recording_id, channel.name, channel.stream_url)
            if success:
                self.active_recordings[channel.name] = recording_id
                QMessageBox.information(
                    self, 'Recording Started',
                    f"Recording started for '{channel.name}'\n\nRight-click the channel to stop recording."
                )
            else:
                QMessageBox.warning(
                    self, 'Recording Failed',
                    f"Failed to start recording for '{channel.name}'"
                )

    def stop_recording_channel(self, channel: Channel):
        """Stop recording a livestream."""
        if channel.name not in self.active_recordings:
            return

        recording_id = self.active_recordings[channel.name]

        reply = QMessageBox.question(
            self, 'Stop Recording',
            f"Stop recording '{channel.name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            success = self.download_manager.stop_recording(recording_id)
            if success:
                del self.active_recordings[channel.name]

    def on_download_progress(self, download_id: str, bytes_downloaded: int, total_bytes: int):
        """Handle download progress updates."""
        if total_bytes > 0:
            percent = (bytes_downloaded / total_bytes) * 100
            logger.debug(f"Download progress: {percent:.1f}% ({bytes_downloaded}/{total_bytes} bytes)")

    def on_download_complete(self, download_id: str, filepath: str):
        """Handle download completion."""
        logger.info(f"Download complete: {filepath}")
        QMessageBox.information(
            self, 'Download Complete',
            f"Download completed successfully!\n\nSaved to:\n{filepath}"
        )

    def on_download_error(self, download_id: str, error_message: str):
        """Handle download errors."""
        logger.error(f"Download error: {error_message}")
        QMessageBox.critical(
            self, 'Download Error',
            f"Download failed:\n{error_message}"
        )

    def on_recording_started(self, recording_id: str):
        """Handle recording start."""
        logger.info(f"Recording started: {recording_id}")

    def on_recording_stopped(self, recording_id: str, filepath: str):
        """Handle recording stop."""
        logger.info(f"Recording stopped: {filepath}")
        QMessageBox.information(
            self, 'Recording Saved',
            f"Recording saved successfully!\n\nSaved to:\n{filepath}"
        )

    def attach_player_to_window(self):
        """
        Attach the VLC player to the video frame window using platform-specific methods.
        """
        if not hasattr(self, 'player') or not self.player:
            return

        if not hasattr(self, 'video_frame'):
            return

        try:
            if sys.platform.startswith('linux'):
                self.player.set_xwindow(int(self.video_frame.winId()))
                logger.info(f"Attached player to Linux window: {self.video_frame.winId()}")
            elif sys.platform == "win32":
                self.player.set_hwnd(int(self.video_frame.winId()))
                logger.info(f"Attached player to Windows window: {self.video_frame.winId()}")
            elif sys.platform == "darwin":
                self.player.set_nsobject(int(self.video_frame.winId()))
                logger.info(f"Attached player to Mac window: {self.video_frame.winId()}")

            # Force player to refresh video output after reattaching
            if self.player.is_playing():
                logger.info("Player is playing - forcing video refresh on main window")
                current_pos = self.player.get_position()
                self.player.pause()
                QTimer.singleShot(50, lambda: self.player.play())
                if current_pos > 0.0:
                    QTimer.singleShot(100, lambda: self.player.set_position(current_pos))
            else:
                logger.warning("Player not playing - starting playback")
                self.player.play()

        except Exception as e:
            logger.error(f"Error attaching player to window: {e}")

    def showEvent(self, event):
        """
        Called when the widget is shown. Reattach the player to ensure video continues.
        """
        super().showEvent(event)
        # Reattach player when returning from fullscreen (with small delay)
        if hasattr(self, 'player') and self.player:
            logger.info("ChooseChannelScreen showEvent triggered - reattaching player")
            QTimer.singleShot(100, self.attach_player_to_window)

    def closeEvent(self, event):
        """
        Ensures that the VLC player is properly released when the widget is closed.
        """
        # Clean up all downloads and recordings
        if hasattr(self, 'download_manager'):
            self.download_manager.cleanup_all()

        if self.player:
            self.player.stop()
            self.player.release()
        if self.instance:
            self.instance.release()
        event.accept()

    def open_fullscreen_view(self, channel: Channel):
        """
        Open fullscreen view. Stop current player and let fullscreen create its own.
        This matches the working pattern from the test code.
        """
        # Stop the player in this window
        if hasattr(self, 'player') and self.player:
            logger.info("Stopping player before fullscreen")
            self.player.stop()

        # Create fullscreen view WITHOUT passing player (let it create its own)
        # This matches the test code pattern that works
        self.fullscreen_view = FullScreenView(channel)
        self.fullscreen_view.go_back_signal.connect(self.on_fullscreen_view_closed)

        # Show fullscreen
        self.fullscreen_view.showFullScreen()

        # Hide this window
        self.hide()

        logger.info("Opened fullscreen view with new player instance")

    def on_fullscreen_view_closed(self):
        """
        Handle returning from fullscreen view.
        Restart playback of the channel that was playing.
        """
        # Close and cleanup fullscreen view
        if self.fullscreen_view:
            self.fullscreen_view.close()
            self.fullscreen_view = None

        # Show this window
        self.show()

        # Restart the channel that was playing
        if self.active_channel:
            logger.info(f"Restarting playback of {self.active_channel.name}")
            self.play_stream(self.active_channel.stream_url)
        else:
            logger.info("No active channel to restart")

        logger.info("Returned from fullscreen view")

    @pyqtSlot()
    def logout(self):
        reply = QMessageBox.question(
            self, 'Logout Confirmation',
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.player:
                self.player.stop()
            self.logout_signal.emit("logging Out")

            # QApplication.quit()


def main():
    app = QApplication(sys.argv)
    controller = Controller()
    controller.active_profile = create_mock_profile()
    choose_channel_screen = ChooseChannelScreen(controller)
    choose_channel_screen.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
