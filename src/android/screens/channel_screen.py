"""
Channel Screen for IPTV-Saba Android
Main screen for browsing and selecting channels
"""

import os
from pathlib import Path
from threading import Thread

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock, mainthread

from src.data.data_loader import DataLoader


class LoadingPopup(Popup):
    """Loading popup with spinner"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Loading"
        self.size_hint = (0.6, 0.3)
        self.auto_dismiss = False

        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        spinner = Label(
            text="⟳",
            font_size=dp(50),
            color=(0.898, 0.035, 0.078, 1)
        )
        content.add_widget(spinner)

        self.message_label = Label(
            text="Loading channels...",
            font_size=dp(16)
        )
        content.add_widget(self.message_label)

        self.content = content


class ChannelScreen(Screen):
    """Main channel browsing screen"""

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.data_loader = None
        self.groups = []
        self.channels = []
        self.filtered_channels = []
        self.selected_channel = None
        self.loading_popup = None

        self.build_ui()

    def build_ui(self):
        """Build the channel screen UI"""
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        # Set background
        with main_layout.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.bg_rect = Rectangle(size=main_layout.size, pos=main_layout.pos)
        main_layout.bind(size=self._update_bg, pos=self._update_bg)

        # Top bar
        top_bar = BoxLayout(size_hint_y=0.08, spacing=dp(10))

        # Profile info
        profile_name = self.controller.active_profile.name if self.controller.active_profile else "No Profile"
        profile_label = Label(
            text=f"Profile: {profile_name}",
            size_hint_x=0.5,
            font_size=dp(14),
            color=(1, 1, 1, 1)
        )
        top_bar.add_widget(profile_label)

        # Logout button
        logout_btn = Button(
            text="Logout",
            size_hint_x=0.25,
            background_color=(0.8, 0.2, 0.2, 1),
            font_size=dp(14)
        )
        logout_btn.bind(on_press=self.logout)
        top_bar.add_widget(logout_btn)

        # Easy mode button
        easy_mode_btn = Button(
            text="Easy Mode",
            size_hint_x=0.25,
            background_color=(0.098, 0.467, 0.949, 1),
            font_size=dp(14)
        )
        easy_mode_btn.bind(on_press=self.switch_to_easy_mode)
        top_bar.add_widget(easy_mode_btn)

        main_layout.add_widget(top_bar)

        # Search bar
        search_layout = BoxLayout(size_hint_y=0.08, spacing=dp(10))

        self.search_input = TextInput(
            hint_text="Search channels...",
            size_hint_x=0.7,
            multiline=False,
            font_size=dp(14),
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[dp(10), dp(10)]
        )
        self.search_input.bind(text=self.on_search_text_changed)
        search_layout.add_widget(self.search_input)

        # Group filter spinner
        self.group_spinner = Spinner(
            text='All Groups',
            size_hint_x=0.3,
            background_color=(0.2, 0.2, 0.2, 1),
            font_size=dp(14)
        )
        self.group_spinner.bind(text=self.on_group_selected)
        search_layout.add_widget(self.group_spinner)

        main_layout.add_widget(search_layout)

        # Filter buttons (Favorites, History, All)
        filter_layout = BoxLayout(size_hint_y=0.07, spacing=dp(5))

        all_btn = Button(
            text="All",
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=dp(14)
        )
        all_btn.bind(on_press=lambda x: self.filter_channels('all'))
        filter_layout.add_widget(all_btn)

        favorites_btn = Button(
            text="Favorites",
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=dp(14)
        )
        favorites_btn.bind(on_press=lambda x: self.filter_channels('favorites'))
        filter_layout.add_widget(favorites_btn)

        history_btn = Button(
            text="History",
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=dp(14)
        )
        history_btn.bind(on_press=lambda x: self.filter_channels('history'))
        filter_layout.add_widget(history_btn)

        main_layout.add_widget(filter_layout)

        # Channel list
        scroll = ScrollView(size_hint_y=0.7)
        self.channel_list = GridLayout(
            cols=1,
            spacing=dp(5),
            size_hint_y=None,
            padding=[dp(5), dp(5)]
        )
        self.channel_list.bind(minimum_height=self.channel_list.setter('height'))
        scroll.add_widget(self.channel_list)
        main_layout.add_widget(scroll)

        # Bottom buttons
        bottom_layout = BoxLayout(size_hint_y=0.1, spacing=dp(10))

        play_btn = Button(
            text="Play",
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(16),
            bold=True
        )
        play_btn.bind(on_press=self.play_channel)
        bottom_layout.add_widget(play_btn)

        fullscreen_btn = Button(
            text="Fullscreen",
            background_color=(0.098, 0.467, 0.949, 1),
            font_size=dp(16),
            bold=True
        )
        fullscreen_btn.bind(on_press=self.play_fullscreen)
        bottom_layout.add_widget(fullscreen_btn)

        main_layout.add_widget(bottom_layout)

        self.add_widget(main_layout)

    def _update_bg(self, instance, value):
        """Update background rectangle"""
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def on_enter(self):
        """Called when entering the screen"""
        super().on_enter()
        self.load_channels()

    def load_channels(self):
        """Load channels from profile URL"""
        if not self.controller.active_profile:
            return

        # Show loading popup
        self.loading_popup = LoadingPopup()
        self.loading_popup.open()

        # Load data in background thread
        thread = Thread(target=self._load_data_thread)
        thread.daemon = True
        thread.start()

    def _load_data_thread(self):
        """Load data in background thread"""
        try:
            profile = self.controller.active_profile
            config_dir = self.controller.config_dir
            data_path = Path(os.path.join(config_dir, (profile.name + "data.json")))

            # Create data loader
            self.data_loader = DataLoader()

            # Load from cache if within 24 hours
            if profile.is_within_24_hours() and data_path.is_file():
                self.data_loader.load_from_json(data_path)
            else:
                success = self.data_loader.load(profile.url)
                if success:
                    self.data_loader.save_to_json(data_path)
                    profile.update_last_loaded()
                    self.controller.profile_manager.update_profile(profile)
                else:
                    # Fallback to cached data
                    if data_path.is_file():
                        self.data_loader.load_from_json(data_path)

            # Update UI on main thread
            Clock.schedule_once(self._on_data_loaded, 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: self._on_load_error(str(e)), 0)

    @mainthread
    def _on_data_loaded(self, dt):
        """Handle successful data load"""
        if self.loading_popup:
            self.loading_popup.dismiss()

        # Get groups and channels
        self.groups = self.data_loader.get_groups()
        self.channels = []
        for group in self.groups:
            self.channels.extend(group.channels)

        # Update group spinner
        group_names = ['All Groups'] + [group.name for group in self.groups]
        self.group_spinner.values = group_names

        # Display all channels initially
        self.filtered_channels = self.channels.copy()
        self.update_channel_list()

    @mainthread
    def _on_load_error(self, error_msg):
        """Handle load error"""
        if self.loading_popup:
            self.loading_popup.dismiss()

        error_popup = Popup(
            title='Error',
            content=Label(text=f'Failed to load channels: {error_msg}'),
            size_hint=(0.8, 0.3)
        )
        error_popup.open()

    def update_channel_list(self):
        """Update the channel list display"""
        self.channel_list.clear_widgets()

        if not self.filtered_channels:
            no_channels = Label(
                text="No channels found",
                size_hint_y=None,
                height=dp(50),
                color=(0.7, 0.7, 0.7, 1)
            )
            self.channel_list.add_widget(no_channels)
            return

        # Add channel buttons
        for channel in self.filtered_channels:
            channel_layout = BoxLayout(
                size_hint_y=None,
                height=dp(60),
                spacing=dp(10),
                padding=[dp(5), dp(5)]
            )

            # Channel button
            channel_btn = Button(
                text=channel.name,
                background_color=(0.2, 0.2, 0.2, 1),
                font_size=dp(14)
            )
            channel_btn.bind(on_press=lambda x, c=channel: self.on_channel_selected(c))
            channel_layout.add_widget(channel_btn)

            # Favorite button
            is_favorite = self.is_favorite(channel)
            fav_btn = Button(
                text="★" if is_favorite else "☆",
                size_hint_x=0.15,
                background_color=(0.898, 0.035, 0.078, 1) if is_favorite else (0.3, 0.3, 0.3, 1),
                font_size=dp(18)
            )
            fav_btn.bind(on_press=lambda x, c=channel: self.toggle_favorite(c))
            channel_layout.add_widget(fav_btn)

            self.channel_list.add_widget(channel_layout)

    def on_channel_selected(self, channel):
        """Handle channel selection"""
        self.selected_channel = channel

        # Highlight selected channel
        for child in self.channel_list.children:
            if isinstance(child, BoxLayout):
                btn = child.children[1]  # Channel button (reversed order)
                if isinstance(btn, Button):
                    if btn.text == channel.name:
                        btn.background_color = (0.898, 0.035, 0.078, 1)
                    else:
                        btn.background_color = (0.2, 0.2, 0.2, 1)

    def on_search_text_changed(self, instance, value):
        """Handle search text change"""
        search_text = value.lower().strip()

        if not search_text:
            self.filtered_channels = self.channels.copy()
        else:
            self.filtered_channels = [
                ch for ch in self.channels
                if search_text in ch.name.lower()
            ]

        self.update_channel_list()

    def on_group_selected(self, spinner, text):
        """Handle group selection"""
        if text == 'All Groups':
            self.filtered_channels = self.channels.copy()
        else:
            # Find group and get its channels
            for group in self.groups:
                if group.name == text:
                    self.filtered_channels = group.channels.copy()
                    break

        self.update_channel_list()

    def filter_channels(self, filter_type):
        """Filter channels by type (all, favorites, history)"""
        if filter_type == 'all':
            self.filtered_channels = self.channels.copy()
        elif filter_type == 'favorites':
            favorites = self.controller.active_profile.favorites if self.controller.active_profile else []
            self.filtered_channels = [ch for ch in self.channels if ch.name in favorites]
        elif filter_type == 'history':
            history = self.controller.active_profile.history if self.controller.active_profile else []
            self.filtered_channels = [ch for ch in self.channels if ch.name in history]

        self.update_channel_list()

    def is_favorite(self, channel):
        """Check if channel is in favorites"""
        if not self.controller.active_profile:
            return False
        return channel.name in self.controller.active_profile.favorites

    def toggle_favorite(self, channel):
        """Toggle channel favorite status"""
        if not self.controller.active_profile:
            return

        profile = self.controller.active_profile
        if channel.name in profile.favorites:
            profile.favorites.remove(channel.name)
        else:
            profile.add_to_favorites(channel.name)

        # Save profile
        self.controller.profile_manager.update_profile(profile)
        self.update_channel_list()

    def play_channel(self, instance):
        """Play selected channel in embedded player"""
        if not self.selected_channel:
            error_popup = Popup(
                title='Error',
                content=Label(text='Please select a channel first'),
                size_hint=(0.7, 0.3)
            )
            error_popup.open()
            return

        # Add to history
        if self.controller.active_profile:
            self.controller.active_profile.add_to_history(self.selected_channel.name)
            self.controller.profile_manager.update_profile(self.controller.active_profile)

        # For now, just go to fullscreen
        # In future, could add embedded player here
        self.play_fullscreen(instance)

    def play_fullscreen(self, instance):
        """Play selected channel in fullscreen"""
        if not self.selected_channel:
            error_popup = Popup(
                title='Error',
                content=Label(text='Please select a channel first'),
                size_hint=(0.7, 0.3)
            )
            error_popup.open()
            return

        # Add to history
        if self.controller.active_profile:
            self.controller.active_profile.add_to_history(self.selected_channel.name)
            self.controller.profile_manager.update_profile(self.controller.active_profile)

        # Navigate to fullscreen with channel data
        app = App.get_running_app()
        fullscreen_screen = app.screen_manager.get_screen('fullscreen')
        fullscreen_screen.set_channel(self.selected_channel)
        app.switch_screen('fullscreen')

    def switch_to_easy_mode(self, instance):
        """Switch to easy mode screen"""
        App.get_running_app().switch_screen('easy_mode')

    def logout(self, instance):
        """Logout and return to login screen"""
        # Clear auto-login
        self.controller.config_manager.set('auto_login_enabled', False)
        self.controller.config_manager.save()

        # Return to login
        App.get_running_app().switch_screen('login')
