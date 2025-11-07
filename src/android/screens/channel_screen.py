"""
Netflix-Style Channel Screen for IPTV-Saba Android
Modern card-based layout with horizontal group browsing
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
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock, mainthread

from src.data.data_loader import DataLoader

# Optional: Download/Record manager (requires pyjnius)
try:
    from src.android.download_record_manager import DownloadRecordManager
    DOWNLOAD_RECORD_AVAILABLE = True
except ImportError:
    DOWNLOAD_RECORD_AVAILABLE = False
    DownloadRecordManager = None


class LoadingPopup(Popup):
    """Loading popup with spinner"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Loading"
        self.size_hint = (0.6, 0.3)
        self.auto_dismiss = False

        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))

        spinner = Label(
            text="Loading...",
            font_size=dp(16),
            color=(0.898, 0.035, 0.078, 1)
        )
        content.add_widget(spinner)

        self.message_label = Label(
            text="Loading channels...",
            font_size=dp(16)
        )
        content.add_widget(self.message_label)

        self.content = content


class ChannelCard(BoxLayout):
    """Netflix-style channel card"""

    def __init__(self, channel, on_select, is_favorite=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(140)
        self.spacing = 0
        self.padding = 0
        self.channel = channel

        # Card background with rounded corners
        with self.canvas.before:
            Color(0.15, 0.15, 0.15, 1)
            self.card_bg = RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(8)]
            )
        self.bind(size=self._update_card, pos=self._update_card)

        # Channel thumbnail/placeholder
        thumbnail = Button(
            background_color=(0.2, 0.2, 0.2, 1),
            background_normal='',
            size_hint_y=0.7
        )
        thumbnail.bind(on_press=lambda x: on_select(channel))

        # Thumbnail placeholder with first letter
        thumbnail_label = Label(
            text=channel.name[0].upper() if channel.name else "?",
            font_size=dp(36),
            bold=True,
            color=(0.898, 0.035, 0.078, 1)
        )
        thumbnail.add_widget(thumbnail_label)
        self.add_widget(thumbnail)

        # Channel info
        info_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=0.3,
            padding=[dp(8), dp(4)]
        )

        # Channel name
        name_label = Label(
            text=channel.name,
            font_size=dp(12),
            bold=True,
            color=(1, 1, 1, 1),
            shorten=True,
            shorten_from='right',
            text_size=(self.width - dp(16), None),
            halign='left',
            valign='top'
        )
        info_layout.add_widget(name_label)

        # Favorite indicator
        if is_favorite:
            fav_label = Label(
                text="♥ Favorite",
                font_size=dp(10),
                color=(0.898, 0.035, 0.078, 1),
                size_hint_y=None,
                height=dp(15)
            )
            info_layout.add_widget(fav_label)

        self.add_widget(info_layout)

    def _update_card(self, *args):
        self.card_bg.size = self.size
        self.card_bg.pos = self.pos


class GroupButton(Button):
    """Horizontal scrollable group button"""

    def __init__(self, group_name, is_selected=False, **kwargs):
        super().__init__(**kwargs)
        self.text = group_name
        self.size_hint_x = None
        self.width = dp(120)
        self.height = dp(35)
        self.font_size = dp(13)
        self.bold = is_selected

        # Netflix-style button colors
        if is_selected:
            self.background_color = (0.898, 0.035, 0.078, 1)  # Netflix red
        else:
            self.background_color = (0.2, 0.2, 0.2, 1)


class ChannelScreen(Screen):
    """Netflix-style channel browsing screen"""

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.data_loader = None
        self.groups = []
        self.channels = []
        self.filtered_channels = []
        self.selected_channel = None
        self.loading_popup = None
        self.current_group = "All"
        self.group_buttons = {}

        # Initialize download/record manager (optional - requires pyjnius)
        self.download_manager = None
        self.active_recording_id = None

        if DOWNLOAD_RECORD_AVAILABLE:
            self.download_manager = DownloadRecordManager()
            # Bind to download/record events
            self.download_manager.bind(on_download_complete=self.on_download_complete)
            self.download_manager.bind(on_download_error=self.on_download_error)
            self.download_manager.bind(on_recording_started=self.on_recording_started)
            self.download_manager.bind(on_recording_stopped=self.on_recording_stopped)

        self.build_ui()

    def build_ui(self):
        """Build the Netflix-style channel screen UI"""
        # Main layout with dark background
        main_layout = BoxLayout(orientation='vertical', padding=0, spacing=0)

        # Set dark background
        with main_layout.canvas.before:
            Color(0.08, 0.08, 0.08, 1)  # Netflix dark gray
            self.bg_rect = Rectangle(size=main_layout.size, pos=main_layout.pos)
        main_layout.bind(size=self._update_bg, pos=self._update_bg)

        # ==================== TOP BAR ====================
        top_bar = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            padding=[dp(15), dp(10)],
            spacing=dp(10)
        )

        # Set top bar background
        with top_bar.canvas.before:
            Color(0.06, 0.06, 0.06, 1)  # Darker top bar
            self.top_bar_bg = Rectangle(size=top_bar.size, pos=top_bar.pos)
        top_bar.bind(size=self._update_top_bar_bg, pos=self._update_top_bar_bg)

        # App logo/title
        logo_label = Label(
            text="IPTV SABA",
            size_hint_x=0.3,
            font_size=dp(24),
            bold=True,
            color=(0.898, 0.035, 0.078, 1)  # Netflix red
        )
        top_bar.add_widget(logo_label)

        # Profile name
        profile_name = self.controller.active_profile.name if self.controller.active_profile else "No Profile"
        self.profile_label = Label(
            text=f"{profile_name}",
            size_hint_x=0.35,
            font_size=dp(14),
            color=(0.9, 0.9, 0.9, 1)
        )
        top_bar.add_widget(self.profile_label)

        # Logout button
        logout_btn = Button(
            text="Logout",
            size_hint_x=0.18,
            background_color=(0.2, 0.2, 0.2, 1),
            font_size=dp(12)
        )
        logout_btn.bind(on_press=self.logout)
        top_bar.add_widget(logout_btn)

        # Play button (quick access)
        play_btn = Button(
            text="Play",
            size_hint_x=0.17,
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(14),
            bold=True
        )
        play_btn.bind(on_press=self.play_fullscreen)
        top_bar.add_widget(play_btn)

        main_layout.add_widget(top_bar)

        # ==================== GROUP SELECTOR (Horizontal Scroll) ====================
        group_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(55),
            padding=[0, dp(5)]
        )

        # Group selector header
        group_header = BoxLayout(
            size_hint_y=None,
            height=dp(20),
            padding=[dp(15), 0]
        )
        group_header_label = Label(
            text="Browse by Category",
            size_hint_x=None,
            width=dp(150),
            font_size=dp(12),
            color=(0.7, 0.7, 0.7, 1),
            halign='left'
        )
        group_header.add_widget(group_header_label)
        group_container.add_widget(group_header)

        # Horizontal scrollable group buttons
        self.group_scroll = ScrollView(
            size_hint_y=None,
            height=dp(35),
            do_scroll_y=False,
            do_scroll_x=True,
            bar_width=0  # Hide scrollbar for cleaner look
        )

        self.group_buttons_layout = BoxLayout(
            size_hint_x=None,
            spacing=dp(10),
            padding=[dp(15), 0]
        )
        self.group_buttons_layout.bind(minimum_width=self.group_buttons_layout.setter('width'))

        self.group_scroll.add_widget(self.group_buttons_layout)
        group_container.add_widget(self.group_scroll)

        main_layout.add_widget(group_container)

        # ==================== SEARCH BAR ====================
        search_container = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            padding=[dp(15), dp(5)],
            spacing=dp(10)
        )

        self.search_input = TextInput(
            hint_text="🔍 Search channels...",
            multiline=False,
            size_hint_x=0.7,
            font_size=dp(14),
            background_color=(0.15, 0.15, 0.15, 1),
            foreground_color=(1, 1, 1, 1),
            hint_text_color=(0.5, 0.5, 0.5, 1),
            padding=[dp(12), dp(12)]
        )
        self.search_input.bind(text=self.on_search)
        search_container.add_widget(self.search_input)

        # Favorites button
        fav_btn = Button(
            text="Favorites",
            size_hint_x=0.3,
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(12)
        )
        fav_btn.bind(on_press=self.show_favorites)
        search_container.add_widget(fav_btn)

        main_layout.add_widget(search_container)

        # ==================== CHANNEL GRID (Netflix-style cards) ====================
        self.channel_scroll = ScrollView(
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(6),
            bar_color=(0.898, 0.035, 0.078, 0.8)
        )

        # Grid layout for channel cards
        self.channel_grid = GridLayout(
            cols=2,  # 2 columns for mobile
            spacing=dp(12),
            padding=[dp(15), dp(10)],
            size_hint_y=None,
            row_default_height=dp(140),
            row_force_default=True
        )
        self.channel_grid.bind(minimum_height=self.channel_grid.setter('height'))

        self.channel_scroll.add_widget(self.channel_grid)
        main_layout.add_widget(self.channel_scroll)

        self.add_widget(main_layout)

    def _update_bg(self, instance, value):
        """Update background rectangle"""
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def _update_top_bar_bg(self, instance, value):
        """Update top bar background"""
        self.top_bar_bg.size = instance.size
        self.top_bar_bg.pos = instance.pos

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
            # Sanitize profile name for safe file naming (remove path separators)
            safe_name = profile.name.replace('/', '_').replace('\\', '_').replace(':', '_')
            data_path = Path(os.path.join(config_dir, (safe_name + "data.json")))

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
        # DataLoader.groups is Dict[str, Group], convert to list
        self.groups = list(self.data_loader.groups.values())
        self.channels = []
        for group in self.groups:
            self.channels.extend(group.channels)

        # Populate group buttons
        self.populate_group_buttons()

        # Display all channels initially
        self.filtered_channels = self.channels.copy()
        self.update_channel_grid()

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

    def populate_group_buttons(self):
        """Populate horizontal group selector"""
        self.group_buttons_layout.clear_widgets()
        self.group_buttons = {}

        # Add "All" button
        all_btn = GroupButton("All", is_selected=True)
        all_btn.bind(on_press=lambda x: self.on_group_button_pressed("All"))
        self.group_buttons["All"] = all_btn
        self.group_buttons_layout.add_widget(all_btn)

        # Add group buttons
        for group in self.groups:
            btn = GroupButton(group.name, is_selected=False)
            btn.bind(on_press=lambda x, g=group.name: self.on_group_button_pressed(g))
            self.group_buttons[group.name] = btn
            self.group_buttons_layout.add_widget(btn)

    def on_group_button_pressed(self, group_name):
        """Handle group button press"""
        # Update button states
        for name, btn in self.group_buttons.items():
            if name == group_name:
                btn.background_color = (0.898, 0.035, 0.078, 1)
                btn.bold = True
            else:
                btn.background_color = (0.2, 0.2, 0.2, 1)
                btn.bold = False

        self.current_group = group_name
        self.filter_by_group(group_name)

    def filter_by_group(self, group_name):
        """Filter channels by group"""
        if group_name == "All":
            self.filtered_channels = self.channels.copy()
        else:
            self.filtered_channels = []
            for group in self.groups:
                if group.name == group_name:
                    self.filtered_channels = group.channels
                    break

        self.update_channel_grid()

    def on_search(self, instance, text):
        """Handle search input"""
        if not text:
            # Reset to current group
            self.filter_by_group(self.current_group)
            return

        # Filter channels by search text
        search_lower = text.lower()
        if self.current_group == "All":
            base_channels = self.channels
        else:
            base_channels = []
            for group in self.groups:
                if group.name == self.current_group:
                    base_channels = group.channels
                    break

        self.filtered_channels = [
            ch for ch in base_channels
            if search_lower in ch.name.lower()
        ]
        self.update_channel_grid()

    def show_favorites(self, instance):
        """Show only favorite channels"""
        if not self.controller.active_profile:
            return

        favorites = self.controller.active_profile.favorites
        fav_names = [fav.name for fav in favorites]

        self.filtered_channels = [
            ch for ch in self.channels
            if ch.name in fav_names
        ]
        self.update_channel_grid()

    def update_channel_grid(self):
        """Update the channel grid with cards"""
        self.channel_grid.clear_widgets()

        if not self.filtered_channels:
            no_channels = Label(
                text="No channels found",
                size_hint_y=None,
                height=dp(50),
                color=(0.7, 0.7, 0.7, 1),
                font_size=dp(16)
            )
            self.channel_grid.add_widget(no_channels)
            return

        # Get favorite channel names
        fav_names = []
        if self.controller.active_profile:
            fav_names = [fav.name for fav in self.controller.active_profile.favorites]

        # Add channel cards
        for channel in self.filtered_channels:
            is_fav = channel.name in fav_names
            card = ChannelCard(
                channel,
                on_select=self.on_channel_selected,
                is_favorite=is_fav
            )
            self.channel_grid.add_widget(card)

    def on_channel_selected(self, channel):
        """Handle channel selection"""
        self.selected_channel = channel
        # Auto-play on selection
        self.play_fullscreen(None)

    def play_fullscreen(self, instance):
        """Play selected channel in fullscreen"""
        if not self.selected_channel:
            # No channel selected, show message
            popup = Popup(
                title='Select Channel',
                content=Label(text='Please select a channel first'),
                size_hint=(0.7, 0.3)
            )
            popup.open()
            return

        # Add to history
        if self.controller.active_profile:
            self.controller.active_profile.add_to_history(self.selected_channel)

        # Go to fullscreen
        app = App.get_running_app()
        fullscreen_screen = app.screen_manager.get_screen('fullscreen')
        fullscreen_screen.set_channel(self.selected_channel)
        app.switch_screen('fullscreen')

    def logout(self, instance):
        """Logout and return to login screen"""
        app = App.get_running_app()
        self.controller.active_profile = None
        app.switch_screen('login')

    # Dummy methods for download/record (not fully implemented without pyjnius)
    def on_download_complete(self, *args):
        pass

    def on_download_error(self, *args):
        pass

    def on_recording_started(self, *args):
        pass

    def on_recording_stopped(self, *args):
        pass
