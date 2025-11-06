"""
IPTV-Saba Android Application
Main entry point for the Kivy-based Android app
"""

import os
import sys
from pathlib import Path

# Kivy imports
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.core.window import Window
from kivy.utils import platform

# Import Android-specific modules if running on Android
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from android.storage import primary_external_storage_path
    request_permissions([
        Permission.INTERNET,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.WAKE_LOCK
    ])

# Import app components
from src.android.controller import AndroidController

# Import Android screens
from src.android.screens.login_screen import LoginScreen
from src.android.screens.channel_screen import ChannelScreen
from src.android.screens.easy_mode_screen import EasyModeScreen
from src.android.screens.fullscreen_screen import FullscreenScreen


class IPTVSabaApp(App):
    """Main Kivy application for IPTV-Saba Android"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "IPTV Saba"
        self.icon = 'android/icon.png'

        # Initialize controller (contains managers)
        self.controller = None

        # Screen manager
        self.screen_manager = None

    def build(self):
        """Build the application UI"""
        # Set window properties
        Window.clearcolor = (0.1, 0.1, 0.1, 1)  # Dark background

        # Initialize controller
        self._initialize_controller()

        # Create screen manager with fade transition
        self.screen_manager = ScreenManager(transition=FadeTransition())

        # Add screens
        self.screen_manager.add_widget(LoginScreen(
            name='login',
            controller=self.controller,
            config_manager=self.controller.config_manager
        ))
        self.screen_manager.add_widget(ChannelScreen(
            name='channels',
            controller=self.controller
        ))
        self.screen_manager.add_widget(EasyModeScreen(
            name='easy_mode',
            controller=self.controller
        ))
        self.screen_manager.add_widget(FullscreenScreen(
            name='fullscreen',
            controller=self.controller
        ))

        # Check auto-login
        if self._should_auto_login():
            self.screen_manager.current = 'channels'
        else:
            self.screen_manager.current = 'login'

        return self.screen_manager

    def _initialize_controller(self):
        """Initialize the Android controller"""
        # Controller handles its own storage path detection
        self.controller = AndroidController(
            profiles_file="profiles.json",
            folder_name='IPTV-Saba'
        )

    def _should_auto_login(self):
        """Check if auto-login is enabled and valid"""
        return self.controller.login_logic()

    def on_pause(self):
        """Handle app pause (Android lifecycle)"""
        # Save any pending changes
        if self.controller:
            self.controller.save_state()
        return True

    def on_resume(self):
        """Handle app resume (Android lifecycle)"""
        pass

    def switch_screen(self, screen_name):
        """Switch to a different screen"""
        self.screen_manager.current = screen_name

    def go_back(self):
        """Navigate back"""
        current = self.screen_manager.current

        if current == 'fullscreen':
            self.screen_manager.current = 'channels'
        elif current == 'easy_mode':
            self.screen_manager.current = 'channels'
        elif current == 'channels':
            self.screen_manager.current = 'login'
        elif current == 'login':
            # Exit app
            self.stop()


def main():
    """Main entry point"""
    IPTVSabaApp().run()


if __name__ == '__main__':
    main()
