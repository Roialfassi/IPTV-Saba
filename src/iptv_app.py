import ctypes
import logging
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
from src.controller.controller import Controller
from src.utils.resource_path import resource_path
from src.model.profile import create_mock_profile
from src.view.easy_mode_screen import EasyModeScreen
from src.view.login_view import LoginScreen
from src.view.choose_channel_screen import ChooseChannelScreen
from src.services.shared_player_manager import SharedPlayerManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class IPTVApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.controller = Controller()
        self.login_screen = None
        self.choose_channel_screen = None
        self.easy_mode_screen = None
        # self.controller.error_occurred.connect(self.handle_error)
        
        # Connect app aboutToQuit signal to cleanup shared player
        self.app.aboutToQuit.connect(self.cleanup)

    def cleanup(self):
        """
        Cleanup all shared resources when app is closing.

        This method is called via the aboutToQuit signal and ensures:
        1. Active screens clean up their resources
        2. Easy Mode VLC instance is released
        3. Shared player manager is properly reset

        IMPORTANT: VLC on Windows is prone to crashes during cleanup.
        We use a careful approach to minimize access violations.
        """
        logger.info("IPTVApp: Starting application cleanup...")

        # Cleanup ChooseChannelScreen (downloads, recordings, etc.)
        if self.choose_channel_screen:
            try:
                if hasattr(self.choose_channel_screen, '_perform_full_cleanup'):
                    self.choose_channel_screen._perform_full_cleanup(for_logout=False)
                logger.info("IPTVApp: ChooseChannelScreen cleanup complete")
            except Exception as e:
                logger.error(f"Error cleaning up ChooseChannelScreen: {e}")

        # Cleanup EasyModeScreen VLC resources
        if self.easy_mode_screen:
            try:
                if hasattr(self.easy_mode_screen, 'player') and self.easy_mode_screen.player:
                    # Pause first instead of stop to avoid Windows VLC crashes
                    try:
                        if self.easy_mode_screen.player.is_playing():
                            self.easy_mode_screen.player.set_pause(1)
                    except Exception:
                        pass
                    # Set media to None before release
                    try:
                        self.easy_mode_screen.player.set_media(None)
                    except Exception:
                        pass
                    try:
                        self.easy_mode_screen.player.release()
                    except Exception as e:
                        logger.warning(f"Error releasing EasyMode player: {e}")
                if hasattr(self.easy_mode_screen, 'vlc_instance') and self.easy_mode_screen.vlc_instance:
                    try:
                        self.easy_mode_screen.vlc_instance.release()
                    except Exception as e:
                        logger.warning(f"Error releasing EasyMode VLC instance: {e}")
                logger.info("IPTVApp: EasyModeScreen cleanup complete")
            except Exception as e:
                logger.error(f"Error cleaning up EasyModeScreen: {e}")

        # Finally, cleanup the shared player manager
        try:
            SharedPlayerManager.reset_instance()
            logger.info("IPTVApp: SharedPlayerManager reset complete")
        except Exception as e:
            logger.error(f"Error cleaning up SharedPlayerManager: {e}")

        logger.info("IPTVApp: Application cleanup finished")

    def transition_to_login_screen(self):
        if self.choose_channel_screen:
            self.choose_channel_screen.hide()
        self.login_screen = LoginScreen(self.controller)
        self.login_screen.login_success.connect(self.transition_to_channel_selection_screen)
        self.login_screen.easy_mode_success.connect(self.open_easy_mode_screen)
        self.login_screen.show()

    def transition_to_channel_selection_screen(self):
        self.choose_channel_screen = ChooseChannelScreen(self.controller)
        self.choose_channel_screen.logout_signal.connect(self.logout_choose_channel_screen)
        self.choose_channel_screen.show()
        # Saving profile after update
        # self.controller.active_profile.update_last_loaded()
        self.controller.profile_manager.update_profile(self.controller.active_profile)
        self.controller.profile_manager.export_profiles(self.controller.profile_path)
        if self.login_screen:
            self.login_screen.hide()

    def open_easy_mode_screen(self):
        try:
            self.easy_mode_screen = EasyModeScreen(self.controller.active_profile)
            self.easy_mode_screen.show()
            self.login_screen.hide()
        except Exception as e:
            logger.error(f"Error opening easy mode screen: {e}")

    def logout_choose_channel_screen(self):
        self.controller.config_manager.set_value("auto_login_enabled", False)
        self.transition_to_login_screen()

    def handle_first_run(self):
        self.controller.config_manager.set_value("first_run", False)
        default_profile = create_mock_profile()
        self.controller.create_profile(default_profile.name, default_profile.url)
        self.controller.profile_manager.export_profiles(self.controller.profile_path)

    def run(self):
        if self.controller.login_logic():
            self.transition_to_channel_selection_screen()
        else:
            if self.controller.config_manager.get_value("first_run"):
                self.handle_first_run()
            self.transition_to_login_screen()
        sys.exit(self.app.exec_())


def main():
    myappid = 'RoiAlfassi.IPTV-Saba.PC-Version.1.0.0'  # Arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # Note: IPTVApp creates its own QApplication, don't create one here
    iptv = IPTVApp()
    iptv.app.setWindowIcon(QIcon(resource_path("Assets/iptv-logo2.ico")))  # This sets the taskbar icon
    iptv.run()


if __name__ == '__main__':
    main()
