import logging
import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QSlider, QMessageBox, QSplitter,
    QApplication, QSizePolicy, QMenu, QAction, QGraphicsOpacityEffect,
    QStackedWidget, QFrame, QScrollArea, QSpacerItem
)
from PyQt5.QtCore import (
    Qt, pyqtSlot, QObject, pyqtSignal, QTimer, QPropertyAnimation,
    QEasingCurve, QThread, QSize
)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QColor, QPalette

import vlc

from src.controller.controller import Controller
from src.data.data_loader import DataLoader
from src.model.group_model import Group  # for type hints
from src.model.channel_model import Channel  # for type hints
from src.model.profile import create_mock_profile, Profile
from src.view.full_screen_view import FullScreenView

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

APP_ICON_PATH = ":/assets/app_icon.png"  # Change to your app logo if you have one

class LoaderWorker(QObject):
    """Worker thread for loading IPTV data without blocking the UI"""
    finished = pyqtSignal()
    progress = pyqtSignal(int)  # Progress percentage (0-100)
    progress_message = pyqtSignal(str)  # Status message
    error = pyqtSignal(str)
    
    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller
        self.loader = controller.data_loader
        self.source = controller.active_profile.url
        self.active_profile = controller.active_profile
        self.config_dir = controller.config_dir

    def _progress_callback(self, current: int, total: int, message: str):
        """Callback for DataLoader progress updates"""
        if total > 0:
            percent = int((current / total) * 100)
            self.progress.emit(percent)
        self.progress_message.emit(message)

    def run(self):
        try:
            data_path = Path(os.path.join(self.config_dir, (self.active_profile.name + "data.json")))
            if self.active_profile.is_within_24_hours() and data_path.is_file():
                logger.info("Loading Data from file since last login was recently")
                self.progress_message.emit("Loading from cache...")
                self.loader.load_from_json(data_path)
            else:
                self.progress_message.emit("Downloading playlist...")
                success = self.loader.load(
                    self.source,
                    progress_callback=self._progress_callback
                )
                if not success:
                    self.error.emit("Failed to load IPTV data from URL")
                    self.progress_message.emit("Falling back to cached data...")
                    self.loader.load_from_json(data_path)
                else:
                    self.progress_message.emit("Saving to cache...")
                    self.loader.save_to_json(data_path)
                    self.controller.active_profile.update_last_loaded()
                    self.controller.profile_manager.update_profile(self.controller.active_profile)
                    self.controller.profile_manager.export_profiles(self.controller.profile_path)
            
            self.progress_message.emit("Loading complete!")
            self.finished.emit()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            logger.error(f"{exc_type.__name__} in {fname} line {exc_tb.tb_lineno}: {e}")
            self.error.emit(f"Error loading IPTV data: {str(e)}")
            self.finished.emit()


class LoadingOverlay(QWidget):
    # Unicode spinner characters for animation
    SPINNER_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: rgba(20,20,20,150); border-radius: 28px;")
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Animated spinner (Unicode character cycling)
        self.spinner_index = 0
        self.spinner_label = QLabel(self.SPINNER_CHARS[0])
        self.spinner_label.setAlignment(Qt.AlignCenter)
        self.spinner_label.setStyleSheet("font-size: 90px; color: #E50914;")
        layout.addWidget(self.spinner_label)

        self.text_label = QLabel("Loading channels...")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("font-size: 24px; color: white; margin-top: 20px;")
        layout.addWidget(self.text_label)

        # Spinner animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_spinner)
        self.timer.start(80)  # 80ms for smooth animation
        self.hide()

    def rotate_spinner(self):
        """Animate the spinner by cycling through characters"""
        self.spinner_index = (self.spinner_index + 1) % len(self.SPINNER_CHARS)
        self.spinner_label.setText(self.SPINNER_CHARS[self.spinner_index])

    def showEvent(self, event):
        super().showEvent(event)
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(400)
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.opacity_anim.start()

    def update_text(self, text):
        self.text_label.setText(text)


class ChannelCard(QFrame):
    """Custom channel card with logo, name, and preview."""
    def __init__(self, channel: Channel, parent=None):
        super().__init__(parent)
        self.channel = channel
        self.setObjectName("ChannelCard")
        self.setStyleSheet("""
            QFrame#ChannelCard {
                background: rgba(40,40,40,0.75);
                border-radius: 18px;
                border: 1.5px solid #313131;
                margin: 4px 0;
            }
            QFrame#ChannelCard:hover {
                background: rgba(229,9,20,0.12);
                border: 2.5px solid #E50914;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(14)

        self.logo_label = QLabel()
        self.logo_label.setFixedSize(48, 48)
        # Load logo from path or pixmap if present (replace below)
        if hasattr(channel, "logo") and channel.logo:
            self.logo_label.setPixmap(QPixmap(channel.logo).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.logo_label.setPixmap(QPixmap(":/assets/tv_icon.png").scaled(48, 48, Qt.KeepAspectRatio))
        layout.addWidget(self.logo_label)

        self.title_label = QLabel(channel.name)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_label.setStyleSheet("color: #FFF;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Optionally: preview thumbnail, favorite icon, etc.
        # You can add extra widgets to the right as needed.

        self.setFixedHeight(68)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.parent().parent().parent().channel_card_clicked.emit(self.channel)


class ChooseChannelScreen(QWidget):
    logout_signal = pyqtSignal(str)
    channel_card_clicked = pyqtSignal(Channel)

    def __init__(self, controller: Controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("IPTV - Choose Channel")
        self.setWindowIcon(QIcon(APP_ICON_PATH))
        self.setMinimumSize(900, 620)
        self.setStyleSheet("""
            QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #222, stop:1 #111); color: #f4f4f4;}
            QLabel#headerLabel { font-size: 26px; font-weight: bold; color: #E50914; }
            QPushButton { background-color: #E50914; color: #FFF; border-radius: 6px; font-weight: 600; font-size: 17px; padding: 9px 16px; }
            QPushButton:hover { background-color: #F6121D; }
            QPushButton:pressed { background-color: #BF0811; }
            QLineEdit { background: #232323; border: 1.2px solid #353535; border-radius: 7px; padding: 7px; color: #fff; font-size: 16px;}
            QSlider::groove:horizontal { height: 5px; background: #353535; border-radius: 2px;}
            QSlider::handle:horizontal { background: #E50914; width: 16px; border-radius: 8px;}
        """)
        self.init_ui()
        self.connect_signals()
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.hide()
        QTimer.singleShot(120, self.load_playlist_with_progress)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Animated Header
        header = QFrame()
        header.setObjectName("headerWidget")
        header.setStyleSheet("""
            QFrame#headerWidget { background: rgba(16,16,16,0.92); border-bottom: 1.8px solid #292929;}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 3, 16, 3)
        header_label = QLabel("Live IPTV Channels")
        header_label.setObjectName("headerLabel")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        self.theme_button = QPushButton("☀️")
        self.theme_button.setToolTip("Toggle Dark/Light Mode")
        header_layout.addWidget(self.theme_button)
        self.logout_button = QPushButton("Logout")
        self.logout_button.setToolTip("Log out from your profile")
        header_layout.addWidget(self.logout_button)
        main_layout.addWidget(header)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setHandleWidth(2)
        main_layout.addWidget(main_splitter, 1)

        # ----------------- Left Panel: Groups & Search -----------------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(16, 14, 12, 12)
        left_layout.setSpacing(10)

        self.group_search = QLineEdit()
        self.group_search.setPlaceholderText("🔍 Search Categories")
        left_layout.addWidget(self.group_search)

        self.group_list = QListWidget()
        self.group_list.setFont(QFont("Segoe UI", 13))
        self.group_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self.group_list)

        main_splitter.addWidget(left_panel)
        main_splitter.setSizes([240, 760])

        # ----------------- Right Panel: Channels, Player, Controls -----------------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 14, 18, 12)
        right_layout.setSpacing(12)

        # Quick filter chips (Favorites, History)
        chip_row = QHBoxLayout()
        chip_row.setSpacing(8)
        self.fav_chip = QPushButton("❤️ Favorites")
        self.hist_chip = QPushButton("🕒 History")
        chip_row.addWidget(self.fav_chip)
        chip_row.addWidget(self.hist_chip)
        chip_row.addStretch()
        right_layout.addLayout(chip_row)

        # Channel search bar
        self.channel_search = QLineEdit()
        self.channel_search.setPlaceholderText("🔎 Search Channels")
        right_layout.addWidget(self.channel_search)

        # Scroll area for channel cards
        self.channel_area = QScrollArea()
        self.channel_area.setWidgetResizable(True)
        self.channel_list_widget = QWidget()
        self.channel_area_layout = QVBoxLayout(self.channel_list_widget)
        self.channel_area_layout.setAlignment(Qt.AlignTop)
        self.channel_area.setWidget(self.channel_list_widget)
        right_layout.addWidget(self.channel_area, 2)

        # Video player frame
        self.video_frame = QFrame()
        self.video_frame.setMinimumHeight(260)
        self.video_frame.setStyleSheet("background: #101010; border-radius: 18px;")
        right_layout.addWidget(self.video_frame)

        # Controls row
        controls_row = QHBoxLayout()
        controls_row.setSpacing(11)
        self.play_btn = QPushButton("▶️")
        self.pause_btn = QPushButton("⏸")
        self.stop_btn = QPushButton("⏹")
        self.fullscreen_btn = QPushButton("🖵 Fullscreen")
        controls_row.addWidget(self.play_btn)
        controls_row.addWidget(self.pause_btn)
        controls_row.addWidget(self.stop_btn)
        controls_row.addWidget(self.fullscreen_btn)
        controls_row.addStretch()
        vol_lbl = QLabel("🔊")
        controls_row.addWidget(vol_lbl)
        self.vol_slider = QSlider(Qt.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(48)
        self.vol_slider.setFixedWidth(110)
        controls_row.addWidget(self.vol_slider)
        right_layout.addLayout(controls_row)
        main_splitter.addWidget(right_panel)

        # VLC init
        vlc_plugins_path = r'C:\Program Files\VideoLAN\VLC\plugins'
        args = ['--no-plugins-cache', '--plugin-path=' + vlc_plugins_path]
        self.instance = vlc.Instance(args)
        self.player = self.instance.media_player_new()

        # Store current state
        self.groups_dict = {}
        self.all_groups = []
        self.all_channels = []
        self.active_channel = None
        self.fullscreen_view = None

    def connect_signals(self):
        self.logout_button.clicked.connect(self.logout)
        self.theme_button.clicked.connect(self.toggle_theme)
        self.group_search.textChanged.connect(self.filter_groups)
        self.channel_search.textChanged.connect(self.filter_channels)
        self.group_list.itemClicked.connect(self.on_group_selected)
        self.fav_chip.clicked.connect(self.show_favorites)
        self.hist_chip.clicked.connect(self.show_history)
        self.channel_card_clicked.connect(self.on_channel_card_clicked)
        self.play_btn.clicked.connect(self.play_channel)
        self.pause_btn.clicked.connect(self.pause_channel)
        self.stop_btn.clicked.connect(self.stop_channel)
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        self.vol_slider.valueChanged.connect(self.set_volume)
        self.controller.data_loaded.connect(self.on_data_loaded)
        self.controller.error_occurred.connect(self.show_error)

    def load_playlist_with_progress(self):
        """Start loading the playlist with progress indicators"""
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
        
        # Connect progress message to update loading overlay text
        self.worker.progress_message.connect(self.loading_overlay.update_text)
        
        self.thread.start()

    def on_loading_finished(self):
        self.loading_overlay.hide()
        self.load_groups()

    def load_groups(self):
        self.group_list.clear()
        groups = self.controller.list_groups()
        self.all_groups = groups
        self.group_list.addItems(groups)
        if groups:
            self.group_list.setCurrentRow(0)
            self.on_group_selected()

    @pyqtSlot(dict)
    def on_data_loaded(self, groups: dict):
        """
        Slot to receive loaded group data from the controller.
        Expects a dictionary with group names as keys and Group objects as values.
        """
        self.groups_dict = groups
        self.populate_group_list()

    def filter_groups(self, text: str):
        self.group_list.clear()
        filtered = [g for g in self.all_groups if text.lower() in g.lower()]
        self.group_list.addItems(filtered)

    def on_group_selected(self):
        item = self.group_list.currentItem()
        if item:
            group_name = item.text()
            channels = self.controller.list_channels_in_group(group_name)
            self.all_channels = channels
            self.populate_channel_cards(channels)

    def filter_channels(self, text: str):
        filtered = [ch for ch in self.all_channels if text.lower() in ch.lower()]
        self.populate_channel_cards(filtered)

    def populate_channel_cards(self, channel_names):
        # Clear and repopulate channel card layout
        for i in reversed(range(self.channel_area_layout.count())):
            widget = self.channel_area_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        for ch_name in sorted(channel_names):
            ch_obj = self.controller.find_channel_by_name(ch_name)
            card = ChannelCard(ch_obj, self.channel_list_widget)
            self.channel_area_layout.addWidget(card)

    def on_channel_card_clicked(self, channel: Channel):
        if channel and channel.stream_url:
            self.play_stream(channel.stream_url)
            self.add_to_history(channel)
            self.active_channel = channel
        else:
            QMessageBox.critical(self, "Stream Error", "Selected channel does not have a valid stream URL.")

    def play_stream(self, stream_url):
        try:
            if sys.platform.startswith('linux'):
                self.player.set_xwindow(self.video_frame.winId())
            elif sys.platform == "win32":
                self.player.set_hwnd(self.video_frame.winId())
            elif sys.platform == "darwin":
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
        else:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()

    def set_volume(self, value):
        if self.player:
            self.player.audio_set_volume(value)

    def add_to_history(self, channel: Channel):
        self.controller.add_to_history(channel)

    def show_favorites(self):
        favs = self.controller.active_profile.list_channels_in_favorites()
        self.populate_channel_cards(favs)

    def show_history(self):
        hist = self.controller.active_profile.list_channels_in_history()
        self.populate_channel_cards(hist)

    def show_error(self, message: str):
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        """
        Ensures that resources are properly released when the widget is closed.
        """
        logger.info("ccs_v2: Performing cleanup on close")
        
        # Close fullscreen view if open
        if self.fullscreen_view:
            try:
                self.fullscreen_view.close()
                self.fullscreen_view = None
            except Exception as e:
                logger.error(f"Error closing fullscreen view: {e}")
        
        # Properly release VLC resources
        try:
            if self.player:
                self.player.stop()
                self.player.release()
                self.player = None
            if self.instance:
                self.instance.release()
                self.instance = None
            logger.info("VLC resources released")
        except Exception as e:
            logger.error(f"Error releasing VLC resources: {e}")
        
        event.accept()

    def open_fullscreen_view(self, channel: Channel):
        self.fullscreen_view = FullScreenView(channel)
        self.fullscreen_view.go_back_signal.connect(self.on_fullscreen_view_closed)
        self.fullscreen_view.showFullScreen()
        self.hide()

    def on_fullscreen_view_closed(self):
        self.show()
        self.fullscreen_view = None

    @pyqtSlot()
    def logout(self):
        """
        Handle logout with proper resource cleanup.
        
        Ensures player is stopped and state is properly reset
        before transitioning back to login screen.
        """
        reply = QMessageBox.question(
            self, 'Logout Confirmation',
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            logger.info("User confirmed logout - performing cleanup")
            
            # Close fullscreen view if open
            if self.fullscreen_view:
                try:
                    self.fullscreen_view.close()
                    self.fullscreen_view = None
                except Exception as e:
                    logger.error(f"Error closing fullscreen view: {e}")
            
            # Stop playback
            if self.player:
                try:
                    self.player.stop()
                except Exception as e:
                    logger.error(f"Error stopping player: {e}")
            
            # Reset active channel
            self.active_channel = None
            
            self.logout_signal.emit("logging Out")

    def toggle_theme(self):
        # Simple theme toggle (demo: add your own palette swap here)
        if self.palette().color(QPalette.Window) == QColor("#222222"):
            pal = self.palette()
            pal.setColor(QPalette.Window, QColor("#e5e5e5"))
            pal.setColor(QPalette.WindowText, QColor("#141414"))
            self.setPalette(pal)
            self.setStyleSheet("QWidget { background: #e5e5e5; color: #111; }")
            self.theme_button.setText("🌙")
        else:
            self.setStyleSheet("""
                QWidget { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #222, stop:1 #111); color: #f4f4f4;}
            """)
            self.theme_button.setText("☀️")

def main():
    app = QApplication(sys.argv)
    controller = Controller()
    controller.active_profile = create_mock_profile()
    screen = ChooseChannelScreen(controller)
    screen.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
