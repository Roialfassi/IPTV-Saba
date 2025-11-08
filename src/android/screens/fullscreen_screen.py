"""
Fullscreen Screen for IPTV-Saba
Full-screen video player with collapsible control panel
Uses Kivy Video widget for both desktop and Android (perfect overlay support)
"""

import os
import subprocess
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

# Import Kivy Video widget for both desktop and Android
from kivy.uix.video import Video


class FullscreenScreen(Screen):
    """Fullscreen video player with collapsible controls overlay"""

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.channel = None
        self.video_player = None
        self.controls_visible = False  # Panel starts collapsed

        self.build_ui()

    def build_ui(self):
        """Build the fullscreen UI"""
        # Main layout (FloatLayout for overlay controls)
        main_layout = FloatLayout()

        # Set background to black
        with main_layout.canvas.before:
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(size=main_layout.size, pos=main_layout.pos)
        main_layout.bind(size=self._update_bg, pos=self._update_bg)

        # ========== VIDEO PLAYER (Kivy Video Widget) ==========
        # Use Kivy Video widget for both Android AND Desktop
        # This ensures overlays work perfectly (no VLC z-order issues)

        # Container for video with black background
        video_container = FloatLayout(
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )

        # Black background for video container
        with video_container.canvas.before:
            Color(0, 0, 0, 1)
            self.video_bg = Rectangle(size=video_container.size, pos=video_container.pos)
        video_container.bind(size=self._update_video_bg, pos=self._update_video_bg)

        self.video_player = Video(
            state='stop',
            options={'eos': 'loop'},
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
            allow_stretch=True,  # Stretch video to fill container
            keep_ratio=True      # Keep aspect ratio
        )

        video_container.add_widget(self.video_player)
        main_layout.add_widget(video_container)

        # ========== COLLAPSIBLE CONTROL PANEL ==========
        # Small toggle button always visible, slides in full controls when clicked

        # Toggle button (always visible in top-right corner)
        self.toggle_button = Button(
            text="☰",  # Menu icon
            size_hint=(None, None),
            size=(dp(50), dp(50)),
            pos_hint={'right': 1, 'top': 1},
            background_color=(0.898, 0.035, 0.078, 0.9),  # Netflix red, semi-transparent
            font_size=dp(24),
            bold=True
        )
        self.toggle_button.bind(on_press=self.toggle_controls)
        main_layout.add_widget(self.toggle_button)

        # Collapsible control panel (slides in from right)
        self.controls_panel = FloatLayout(
            size_hint=(None, 1),
            width=dp(300),  # Panel width
            pos_hint={'right': 0, 'y': 0}  # Start off-screen to the right
        )

        # Panel background
        with self.controls_panel.canvas.before:
            Color(0.1, 0.1, 0.1, 0.95)  # Dark semi-transparent
            self.panel_bg = Rectangle(
                size=self.controls_panel.size,
                pos=self.controls_panel.pos
            )
        self.controls_panel.bind(
            size=self._update_panel_bg,
            pos=self._update_panel_bg
        )

        # Container for controls inside panel
        controls_container = BoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(15),
            size_hint=(1, None),
            height=dp(500),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )

        # Channel name header
        self.channel_label = Label(
            text="No Channel",
            size_hint_y=None,
            height=dp(40),
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle'
        )
        self.channel_label.bind(size=self.channel_label.setter('text_size'))
        controls_container.add_widget(self.channel_label)

        # Separator line
        separator1 = Label(
            text="─" * 20,
            size_hint_y=None,
            height=dp(10),
            color=(0.5, 0.5, 0.5, 1)
        )
        controls_container.add_widget(separator1)

        # Close button
        close_btn = Button(
            text="✕ Close Player",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(16),
            bold=True
        )
        close_btn.bind(on_press=self.go_back)
        controls_container.add_widget(close_btn)

        # Play/Pause button (always available now)
        self.play_pause_btn = Button(
            text="⏸ Pause",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.2, 0.6, 0.2, 1),
            font_size=dp(16),
            bold=True
        )
        self.play_pause_btn.bind(on_press=self.toggle_play_pause)
        controls_container.add_widget(self.play_pause_btn)

        # Stop button (always available now)
        stop_btn = Button(
            text="⏹ Stop",
            size_hint_y=None,
            height=dp(50),
            background_color=(0.6, 0.2, 0.2, 1),
            font_size=dp(16)
        )
        stop_btn.bind(on_press=self.stop_playback)
        controls_container.add_widget(stop_btn)

        # Volume control section
        volume_label = Label(
            text="🔊 Volume",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(14),
            color=(0.9, 0.9, 0.9, 1)
        )
        controls_container.add_widget(volume_label)

        volume_box = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )

        self.volume_slider = Slider(
            min=0,
            max=100,
            value=50,
            size_hint_x=0.75
        )
        self.volume_slider.bind(value=self.on_volume_change)
        volume_box.add_widget(self.volume_slider)

        self.volume_value_label = Label(
            text="50%",
            size_hint_x=0.25,
            font_size=dp(14),
            color=(1, 1, 1, 1)
        )
        volume_box.add_widget(self.volume_value_label)

        controls_container.add_widget(volume_box)

        # Status label
        self.status_label = Label(
            text="Ready",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(12),
            color=(0.7, 0.7, 0.7, 1),
            halign='center',
            valign='middle',
            text_size=(dp(260), None)
        )
        controls_container.add_widget(self.status_label)

        # Add controls to panel
        self.controls_panel.add_widget(controls_container)

        # Add panel to main layout (starts hidden off-screen)
        main_layout.add_widget(self.controls_panel)

        # Track panel state
        self.controls_visible = False

        self.add_widget(main_layout)

    def _update_bg(self, instance, value):
        """Update background rectangle"""
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def _update_video_bg(self, instance, value):
        """Update video container background rectangle"""
        self.video_bg.size = instance.size
        self.video_bg.pos = instance.pos

    def _update_panel_bg(self, instance, value):
        """Update panel background rectangle"""
        self.panel_bg.size = instance.size
        self.panel_bg.pos = instance.pos

    def toggle_controls(self, instance):
        """Toggle slide-in control panel"""
        from kivy.animation import Animation

        if self.controls_visible:
            # Slide out (hide panel)
            anim = Animation(pos_hint={'right': 0, 'y': 0}, duration=0.3, t='out_quad')
            anim.start(self.controls_panel)
            self.toggle_button.text = "☰"  # Menu icon
            self.controls_visible = False
        else:
            # Slide in (show panel)
            anim = Animation(pos_hint={'right': 1, 'y': 0}, duration=0.3, t='out_quad')
            anim.start(self.controls_panel)
            self.toggle_button.text = "✕"  # Close icon
            self.controls_visible = True

    def set_channel(self, channel):
        """Set the channel to play"""
        self.channel = channel
        self.channel_label.text = channel.name

        # Update status
        self.status_label.text = f"Stream: {channel.stream_url[:50]}..."

    def on_enter(self):
        """Called when entering the screen"""
        super().on_enter()

        if self.channel:
            # Start playback
            self.play_stream()

            # Panel starts collapsed on both platforms
            # User can click toggle button to open

    def play_stream(self):
        """Start playing the stream using Kivy Video widget"""
        if not self.channel:
            return

        try:
            # Check video backend
            import os
            backend = os.environ.get('KIVY_VIDEO', 'auto')
            print(f"[VIDEO] Using backend: {backend}")
            print(f"[VIDEO] Stream URL: {self.channel.stream_url}")

            # Use Kivy Video widget for both Android and Desktop
            # This ensures overlays work perfectly (no VLC z-order issues!)
            self.video_player.source = self.channel.stream_url
            self.video_player.state = 'play'

            if hasattr(self, 'play_pause_btn'):
                self.play_pause_btn.text = "⏸ Pause"

            # Set initial volume
            self.video_player.volume = self.volume_slider.value / 100.0

            self.status_label.text = f"Loading stream...\nBackend: {backend}"
            self.status_label.color = (0.8, 0.8, 0.8, 1)

            # Bind to video events to track playback
            self.video_player.bind(on_load=self._on_video_load)
            self.video_player.bind(on_error=self._on_video_error)

        except Exception as e:
            error_msg = str(e)
            print(f"[VIDEO ERROR] {error_msg}")
            self.status_label.text = f"Error: {error_msg}\n\nMake sure you installed:\npip install ffpyplayer"
            self.status_label.color = (1, 0.2, 0.2, 1)

    def _on_video_load(self, instance):
        """Called when video successfully loads (Android only)"""
        self.status_label.text = "Playing..."
        self.status_label.color = (0.2, 1, 0.2, 1)

    def _on_video_error(self, instance, error):
        """Called when video playback error occurs (Android only)"""
        self.status_label.text = f"Playback error: {error}"
        self.status_label.color = (1, 0.2, 0.2, 1)

    def stop_playback(self, instance):
        """Stop playback completely"""
        if self.video_player:
            self.video_player.state = 'stop'
            if hasattr(self, 'play_pause_btn'):
                self.play_pause_btn.text = "▶ Play"
            self.status_label.text = "Stopped"

    def on_volume_change(self, instance, value):
        """Handle volume change"""
        # Update volume label
        self.volume_value_label.text = f"{int(value)}%"

        # Apply volume to player
        if self.video_player:
            self.video_player.volume = value / 100.0

    def toggle_play_pause(self, instance):
        """Toggle play/pause"""
        if self.video_player:
            if self.video_player.state == 'play':
                self.video_player.state = 'pause'
                self.play_pause_btn.text = "▶ Play"
                self.status_label.text = "Paused"
            else:
                self.video_player.state = 'play'
                self.play_pause_btn.text = "⏸ Pause"
                self.status_label.text = "Playing..."

    # Note: Old show/hide/schedule controls methods removed
    # Now using toggle_controls() method with slide-in panel

    def go_back(self, instance):
        """Go back to previous screen"""
        # Stop playback
        if self.video_player:
            self.video_player.state = 'stop'
            self.video_player.source = ''

        # Go back to channels
        App.get_running_app().switch_screen('channels')

    def on_leave(self):
        """Called when leaving the screen"""
        # Stop playback
        if self.video_player:
            self.video_player.state = 'stop'
            self.video_player.source = ''

