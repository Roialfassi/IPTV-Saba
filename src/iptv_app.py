import ctypes
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox
from src.controller.controller import Controller
from src.model.profile import create_mock_profile
from src.view.easy_mode_screen import EasyModeScreen
from src.view.login_view import LoginScreen
from src.view.choose_channel_screen import ChooseChannelScreen


class IPTVApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.controller = Controller()
        self.login_screen = None
        self.choose_channel_screen = None
        self.easy_mode_screen = None
        # self.controller.error_occurred.connect(self.handle_error)

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
        self.controller.active_profile.update_last_loaded()
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
            print(f"open_easy_mode_screen {e}")

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
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("Assets/iptv-logo2.ico"))  # This sets the taskbar icon
    iptv = IPTVApp()
    iptv.run()


if __name__ == '__main__':
    main()
