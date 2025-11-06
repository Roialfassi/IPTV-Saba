"""
Easy Mode Screen for IPTV-Saba Android
Simplified interface with large buttons for elderly users
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.video import Video
from kivy.uix.slider import Slider
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock


class EasyModeScreen(Screen):
    """Easy mode screen with large buttons and simple controls"""

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.favorite_channels = []
        self.current_index = 0
        self.video_player = None
        self.controls_visible = True
        self.hide_timer = None

        self.build_ui()

    def build_ui(self):
        """Build the easy mode UI"""
        # Main layout
        main_layout = BoxLayout(orientation='vertical')

        # Set background
        with main_layout.canvas.before:
            Color(0, 0, 0, 1)  # Black background
            self.bg_rect = Rectangle(size=main_layout.size, pos=main_layout.pos)
        main_layout.bind(size=self._update_bg, pos=self._update_bg)

        # Video player area
        self.video_container = BoxLayout(size_hint_y=0.8)

        # Video player (will be created when playing)
        self.video_player = Video(
            state='stop',
            options={'eos': 'loop'}
        )
        self.video_container.add_widget(self.video_player)

        main_layout.add_widget(self.video_container)

        # Controls container
        self.controls_container = BoxLayout(
            orientation='vertical',
            size_hint_y=0.2,
            padding=dp(10),
            spacing=dp(10)
        )

        # Set controls background
        with self.controls_container.canvas.before:
            Color(0.15, 0.15, 0.15, 0.9)
            self.controls_bg = Rectangle(
                size=self.controls_container.size,
                pos=self.controls_container.pos
            )
        self.controls_container.bind(
            size=self._update_controls_bg,
            pos=self._update_controls_bg
        )

        # Channel info
        self.channel_label = Label(
            text="No channel selected",
            size_hint_y=0.3,
            font_size=dp(24),
            bold=True,
            color=(1, 1, 1, 1)
        )
        self.controls_container.add_widget(self.channel_label)

        # Navigation buttons
        nav_layout = BoxLayout(size_hint_y=0.4, spacing=dp(20), padding=[dp(20), 0])

        # Previous button
        prev_btn = Button(
            text="◀ Previous",
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=dp(28),
            bold=True
        )
        prev_btn.bind(on_press=self.previous_channel)
        nav_layout.add_widget(prev_btn)

        # Play/Pause button
        self.play_pause_btn = Button(
            text="▶ Play",
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(28),
            bold=True
        )
        self.play_pause_btn.bind(on_press=self.toggle_play_pause)
        nav_layout.add_widget(self.play_pause_btn)

        # Next button
        next_btn = Button(
            text="Next ▶",
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=dp(28),
            bold=True
        )
        next_btn.bind(on_press=self.next_channel)
        nav_layout.add_widget(next_btn)

        self.controls_container.add_widget(nav_layout)

        # Volume and back button
        bottom_layout = BoxLayout(size_hint_y=0.3, spacing=dp(10))

        # Volume slider
        volume_layout = BoxLayout(size_hint_x=0.7, spacing=dp(10))
        volume_layout.add_widget(Label(text="🔊", font_size=dp(20), size_hint_x=0.15))

        self.volume_slider = Slider(
            min=0,
            max=100,
            value=50,
            size_hint_x=0.85
        )
        self.volume_slider.bind(value=self.on_volume_change)
        volume_layout.add_widget(self.volume_slider)

        bottom_layout.add_widget(volume_layout)

        # Back button
        back_btn = Button(
            text="Back",
            size_hint_x=0.3,
            background_color=(0.098, 0.467, 0.949, 1),
            font_size=dp(20),
            bold=True
        )
        back_btn.bind(on_press=self.go_back)
        bottom_layout.add_widget(back_btn)

        self.controls_container.add_widget(bottom_layout)

        main_layout.add_widget(self.controls_container)

        self.add_widget(main_layout)

        # Bind touch event for auto-hiding controls
        self.bind(on_touch_down=self.on_screen_touch)

    def _update_bg(self, instance, value):
        """Update background rectangle"""
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def _update_controls_bg(self, instance, value):
        """Update controls background rectangle"""
        self.controls_bg.size = instance.size
        self.controls_bg.pos = instance.pos

    def on_enter(self):
        """Called when entering the screen"""
        super().on_enter()
        self.load_favorites()

        # Start auto-hide timer
        self.schedule_hide_controls()

    def load_favorites(self):
        """Load favorite channels"""
        if not self.controller.active_profile:
            return

        profile = self.controller.active_profile
        favorites = profile.favorites

        # Get channel objects from favorites
        # This requires access to the loaded channels from data_loader
        # For simplicity, we'll store channel names for now
        self.favorite_channels = favorites.copy()

        if self.favorite_channels:
            self.current_index = 0
            self.update_channel_display()

    def update_channel_display(self):
        """Update the current channel display"""
        if not self.favorite_channels:
            self.channel_label.text = "No favorite channels"
            return

        current_channel_name = self.favorite_channels[self.current_index]
        self.channel_label.text = f"{current_channel_name}\n({self.current_index + 1}/{len(self.favorite_channels)})"

    def previous_channel(self, instance):
        """Go to previous channel"""
        if not self.favorite_channels:
            return

        self.current_index = (self.current_index - 1) % len(self.favorite_channels)
        self.update_channel_display()
        self.play_current_channel()

    def next_channel(self, instance):
        """Go to next channel"""
        if not self.favorite_channels:
            return

        self.current_index = (self.current_index + 1) % len(self.favorite_channels)
        self.update_channel_display()
        self.play_current_channel()

    def play_current_channel(self):
        """Play the current channel"""
        if not self.favorite_channels:
            return

        # Get current channel URL
        # For now, we'll just update the display
        # In a full implementation, you'd get the channel object and play its stream
        self.update_channel_display()

        # TODO: Actually play the stream using the video player
        # channel = self.get_channel_by_name(self.favorite_channels[self.current_index])
        # if channel:
        #     self.video_player.source = channel.stream_url
        #     self.video_player.state = 'play'

    def toggle_play_pause(self, instance):
        """Toggle play/pause"""
        if self.video_player.state == 'play':
            self.video_player.state = 'pause'
            self.play_pause_btn.text = "▶ Play"
        else:
            self.play_current_channel()
            self.video_player.state = 'play'
            self.play_pause_btn.text = "⏸ Pause"

    def on_volume_change(self, instance, value):
        """Handle volume change"""
        if self.video_player:
            self.video_player.volume = value / 100.0

    def on_screen_touch(self, instance, touch):
        """Handle screen touch to show/hide controls"""
        if self.controls_container.collide_point(*touch.pos):
            # Touch is on controls, don't hide
            return

        # Toggle controls visibility
        if self.controls_visible:
            self.hide_controls()
        else:
            self.show_controls()

    def show_controls(self):
        """Show controls"""
        self.controls_visible = True
        self.controls_container.opacity = 1
        self.schedule_hide_controls()

    def hide_controls(self):
        """Hide controls"""
        self.controls_visible = False
        self.controls_container.opacity = 0

    def schedule_hide_controls(self):
        """Schedule auto-hide of controls"""
        # Cancel existing timer
        if self.hide_timer:
            self.hide_timer.cancel()

        # Schedule hide after 3 seconds
        self.hide_timer = Clock.schedule_once(lambda dt: self.hide_controls(), 3)

    def go_back(self, instance):
        """Go back to channel screen"""
        # Stop playback
        if self.video_player:
            self.video_player.state = 'stop'

        App.get_running_app().switch_screen('channels')

    def on_leave(self):
        """Called when leaving the screen"""
        # Cancel hide timer
        if self.hide_timer:
            self.hide_timer.cancel()

        # Stop playback
        if self.video_player:
            self.video_player.state = 'stop'
