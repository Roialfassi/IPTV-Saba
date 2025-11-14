"""Main application window."""
import logging
from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal

from app.core.config import Config
from app.services.vlc_service import VLCService
from app.services.playlist_service import PlaylistService
from app.services.download_service import DownloadService
from app.ui.views.login_view import LoginView
from app.ui.views.main_view import MainView
from app.ui.views.player_view import PlayerView
from app.ui.dialogs.downloads_dialog import DownloadsDialog
from app.models.channel import Channel

logger = logging.getLogger(__name__)


class IPTVApplication(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        self.setWindowTitle("IPTV Saba")
        self.setMinimumSize(1280, 720)

        settings = Config.get_settings()
        if settings.window_maximized:
            self.showMaximized()
        else:
            self.resize(settings.window_width, settings.window_height)

        self.vlc_service = VLCService()
        self.playlist_service = PlaylistService()
        self.download_service = DownloadService(Config.get_downloads_dir())

        self.current_profile = None

        self._setup_ui()
        self._setup_connections()
        self._apply_theme()

        self._check_auto_login()

    def _setup_ui(self):
        """Setup UI."""
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_view = LoginView()
        self.main_view = MainView(self.playlist_service)
        self.player_view = PlayerView(self.vlc_service, self.download_service)

        self.stack.addWidget(self.login_view)
        self.stack.addWidget(self.main_view)
        self.stack.addWidget(self.player_view)

        self.downloads_dialog = None

    def _setup_connections(self):
        """Setup signal connections."""
        self.login_view.login_success.connect(self._on_login_success)
        self.main_view.play_channel.connect(self._on_play_channel)
        self.main_view.logout_requested.connect(self._on_logout)
        self.main_view.downloads_requested.connect(self._show_downloads)
        self.player_view.exit_player.connect(self._on_exit_player)

    def _apply_theme(self):
        """Apply dark theme."""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0f0f0f;
                color: #ffffff;
            }
            QPushButton {
                background-color: #e50914;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f40612;
            }
            QPushButton:pressed {
                background-color: #b20710;
            }
            QLineEdit {
                background-color: #1a1a1a;
                color: white;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
            }
            QLineEdit:focus {
                border: 1px solid #e50914;
            }
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #333;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:selected {
                background-color: #e50914;
            }
            QListWidget::item:hover {
                background-color: #242424;
            }
        """)

    def _check_auto_login(self):
        """Check for auto-login."""
        settings = Config.get_settings()

        if settings.auto_login and settings.last_profile:
            profile = Config.get_profile(settings.last_profile)
            if profile:
                self._load_profile(settings.last_profile, profile)
                return

        self.stack.setCurrentWidget(self.login_view)

    def _on_login_success(self, profile_name: str):
        """Handle successful login."""
        profile = Config.get_profile(profile_name)
        if profile:
            self._load_profile(profile_name, profile)

    def _load_profile(self, profile_name: str, profile: dict):
        """Load profile and playlist."""
        self.current_profile = profile_name

        Config.update_profile(profile_name, last_used=str(datetime.now()))

        if self.playlist_service.load_from_url(profile['url']):
            self.main_view.load_data(profile)
            self.stack.setCurrentWidget(self.main_view)
        else:
            QMessageBox.critical(self, "Error", "Failed to load playlist")

    def _on_logout(self):
        """Handle logout."""
        self.current_profile = None
        Config.update_settings(auto_login=False, last_profile="")
        self.stack.setCurrentWidget(self.login_view)

    def _on_play_channel(self, channel: Channel):
        """Play channel."""
        self.player_view.play_channel(channel)
        self.stack.setCurrentWidget(self.player_view)

        if self.current_profile:
            profile = Config.get_profile(self.current_profile)
            if profile:
                history = profile.get('history', [])
                channel_dict = {'name': channel.name, 'url': channel.url}
                if channel_dict not in history:
                    history.insert(0, channel_dict)
                    history = history[:50]
                    Config.update_profile(self.current_profile, history=history)

    def _on_exit_player(self):
        """Exit player view."""
        self.player_view.stop()
        self.stack.setCurrentWidget(self.main_view)

    def _show_downloads(self):
        """Show downloads dialog."""
        if not self.downloads_dialog:
            self.downloads_dialog = DownloadsDialog(self.download_service, self)

        self.downloads_dialog.show()
        self.downloads_dialog.raise_()

    def closeEvent(self, event):
        """Handle window close."""
        settings = Config.get_settings()
        Config.update_settings(
            window_width=self.width(),
            window_height=self.height(),
            window_maximized=self.isMaximized()
        )

        self.player_view.cleanup()
        self.vlc_service.cleanup()
        self.download_service.cleanup()

        event.accept()


from datetime import datetime
