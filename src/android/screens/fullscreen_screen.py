"""
Fullscreen Screen for IPTV-Saba
Full-screen video player with side-by-side control panel
Uses VLC on desktop for reliable playback with dedicated video space
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

# VLC for desktop
VLC_AVAILABLE = False
if platform not in ('android', 'ios'):
    try:
        import vlc
        VLC_AVAILABLE = True
    except ImportError:
        print("VLC not available - video playback will not work on desktop")
        print("Install with: pip install python-vlc")

# Import Kivy Video widget for Android
from kivy.uix.video import Video


class FullscreenScreen(Screen):
    """Fullscreen video player with side-by-side control panel"""

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.channel = None
        self.video_player = None
        self.vlc_instance = None
        self.vlc_player = None
        self.controls_visible = False  # Panel starts collapsed

        self.build_ui()

    def build_ui(self):
        """Build the fullscreen UI with side-by-side layout"""
        # Main horizontal layout: [Video Section (expands/shrinks)] [Control Panel (0/400dp)]
        main_layout = BoxLayout(orientation='horizontal', spacing=0)

        # ========== LEFT SECTION: VIDEO PLAYER ==========
        # This section dynamically resizes when control panel opens/closes
        self.video_section = FloatLayout()

        # Black background
        with self.video_section.canvas.before:
            Color(0, 0, 0, 1)
            self.video_bg = Rectangle(size=self.video_section.size, pos=self.video_section.pos)
        self.video_section.bind(size=self._update_video_bg, pos=self._update_video_bg)

        # Platform-specific video player
        if platform in ('android', 'ios'):
            # Android: Use Kivy Video widget
            self.video_player = Video(
                state='stop',
                options={'eos': 'loop'},
                size_hint=(1, 1),
                pos_hint={'center_x': 0.5, 'center_y': 0.5},
                allow_stretch=True,
                keep_ratio=True
            )
            self.video_section.add_widget(self.video_player)
        else:
            # Desktop: Use VLC in dedicated space (no z-index issues!)
            if VLC_AVAILABLE:
                # Create VLC instance with minimal args
                vlc_args = ['--no-xlib']
                try:
                    self.vlc_instance = vlc.Instance(' '.join(vlc_args))
                    if not self.vlc_instance:
                        self.vlc_instance = vlc.Instance()
                except:
                    self.vlc_instance = vlc.Instance()

                if self.vlc_instance:
                    self.vlc_player = self.vlc_instance.media_player_new()

                    # VLC will render here when we bind the window handle
                    # Bind happens in on_enter after layout is ready
            else:
                # Fallback: show error message
                error_label = Label(
                    text="VLC not installed!\n\nInstall with:\npip install python-vlc",
                    color=(1, 0.2, 0.2, 1),
                    font_size=dp(20),
                    halign='center'
                )
                error_label.bind(size=error_label.setter('text_size'))
                self.video_section.add_widget(error_label)

        # Toggle button in top-right of video section
        self.toggle_button = Button(
            text="☰",
            size_hint=(None, None),
            size=(dp(60), dp(60)),
            pos_hint={'right': 1, 'top': 1},
            background_color=(0.898, 0.035, 0.078, 0.95),
            font_size=dp(28),
            bold=True
        )
        self.toggle_button.bind(on_press=self.toggle_controls)
        self.video_section.add_widget(self.toggle_button)

        main_layout.add_widget(self.video_section)

        # ========== RIGHT SECTION: CONTROL PANEL ==========
        # Starts at width=0 (hidden), expands to 400dp when toggled
        self.controls_panel = FloatLayout(
            size_hint=(None, 1),
            width=0  # Starts collapsed
        )

        # Panel background
        with self.controls_panel.canvas.before:
            Color(0.15, 0.15, 0.15, 1)  # Dark gray
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
            size_hint_y=None,
            height=dp(500),
            pos_hint={'center_y': 0.5}
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

        # Add controls to panel (centered vertically)
        self.controls_panel.add_widget(controls_container)

        # Add panel to main layout (starts with width=0)
        main_layout.add_widget(self.controls_panel)

        # Track panel state
        self.controls_visible = False

        self.add_widget(main_layout)

    def _update_video_bg(self, instance, value):
        """Update video container background rectangle"""
        self.video_bg.size = instance.size
        self.video_bg.pos = instance.pos

    def _update_panel_bg(self, instance, value):
        """Update panel background rectangle"""
        self.panel_bg.size = instance.size
        self.panel_bg.pos = instance.pos

    def toggle_controls(self, instance):
        """Toggle control panel - video section resizes automatically"""
        from kivy.animation import Animation

        if self.controls_visible:
            # Collapse panel (width → 0, video section expands to full screen)
            anim = Animation(width=0, duration=0.35, t='out_cubic')
            anim.start(self.controls_panel)
            self.toggle_button.text = "☰"  # Menu icon
            self.controls_visible = False
        else:
            # Expand panel (width → 400dp, video section shrinks automatically)
            anim = Animation(width=dp(400), duration=0.35, t='out_cubic')
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

        # Desktop: Bind VLC to window handle after layout is ready
        if platform not in ('android', 'ios') and self.vlc_player:
            Clock.schedule_once(self._bind_vlc_window, 0.1)

        if self.channel:
            # Start playback
            Clock.schedule_once(lambda dt: self.play_stream(), 0.2)

    def _bind_vlc_window(self, dt):
        """Bind VLC player to window handle (desktop only)"""
        if not self.vlc_player:
            return

        try:
            # Get the window handle
            import sys
            if sys.platform.startswith('linux'):
                self.vlc_player.set_xwindow(Window.native_handle)
            elif sys.platform == 'win32':
                self.vlc_player.set_hwnd(Window.native_handle)
            elif sys.platform == 'darwin':
                self.vlc_player.set_nsobject(Window.native_handle)

            print(f"[VLC] Bound to window handle: {Window.native_handle}")
        except Exception as e:
            print(f"[VLC] Failed to bind window: {e}")

    def play_stream(self):
        """Start playing the stream (platform-specific)"""
        if not self.channel:
            return

        try:
            if platform in ('android', 'ios'):
                # Android: Use Kivy Video widget
                if self.video_player:
                    self.video_player.source = self.channel.stream_url
                    self.video_player.state = 'play'
                    self.video_player.volume = self.volume_slider.value / 100.0

                    # Bind events
                    self.video_player.bind(on_load=self._on_video_load)
                    self.video_player.bind(on_error=self._on_video_error)

                    self.status_label.text = "Loading stream..."
                    self.status_label.color = (0.8, 0.8, 0.8, 1)
            else:
                # Desktop: Use VLC
                if self.vlc_player:
                    print(f"[VLC] Playing stream: {self.channel.stream_url}")

                    # Create media and play
                    media = self.vlc_instance.media_new(self.channel.stream_url)
                    self.vlc_player.set_media(media)
                    self.vlc_player.play()

                    # Set volume (0-100)
                    volume = int(self.volume_slider.value)
                    self.vlc_player.audio_set_volume(volume)

                    self.status_label.text = "Playing with VLC..."
                    self.status_label.color = (0.2, 1, 0.2, 1)

            if hasattr(self, 'play_pause_btn'):
                self.play_pause_btn.text = "⏸ Pause"

        except Exception as e:
            error_msg = str(e)
            print(f"[PLAYBACK ERROR] {error_msg}")
            self.status_label.text = f"Error: {error_msg}"
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
        """Stop playback completely (platform-specific)"""
        if platform in ('android', 'ios'):
            if self.video_player:
                self.video_player.state = 'stop'
        else:
            if self.vlc_player:
                self.vlc_player.stop()

        if hasattr(self, 'play_pause_btn'):
            self.play_pause_btn.text = "▶ Play"
        self.status_label.text = "Stopped"

    def on_volume_change(self, instance, value):
        """Handle volume change (platform-specific)"""
        # Update volume label
        self.volume_value_label.text = f"{int(value)}%"

        # Apply volume to player
        if platform in ('android', 'ios'):
            if self.video_player:
                self.video_player.volume = value / 100.0
        else:
            if self.vlc_player:
                self.vlc_player.audio_set_volume(int(value))

    def toggle_play_pause(self, instance):
        """Toggle play/pause (platform-specific)"""
        if platform in ('android', 'ios'):
            if self.video_player:
                if self.video_player.state == 'play':
                    self.video_player.state = 'pause'
                    self.play_pause_btn.text = "▶ Play"
                    self.status_label.text = "Paused"
                else:
                    self.video_player.state = 'play'
                    self.play_pause_btn.text = "⏸ Pause"
                    self.status_label.text = "Playing..."
        else:
            if self.vlc_player:
                if self.vlc_player.is_playing():
                    self.vlc_player.pause()
                    self.play_pause_btn.text = "▶ Play"
                    self.status_label.text = "Paused"
                else:
                    self.vlc_player.play()
                    self.play_pause_btn.text = "⏸ Pause"
                    self.status_label.text = "Playing..."

    # Note: Old show/hide/schedule controls methods removed
    # Now using toggle_controls() method with slide-in panel

    def go_back(self, instance):
        """Go back to previous screen"""
        # Stop playback (platform-specific)
        if platform in ('android', 'ios'):
            if self.video_player:
                self.video_player.state = 'stop'
                self.video_player.source = ''
        else:
            if self.vlc_player:
                self.vlc_player.stop()

        # Go back to channels
        App.get_running_app().switch_screen('channels')

    def on_leave(self):
        """Called when leaving the screen"""
        # Stop playback (platform-specific)
        if platform in ('android', 'ios'):
            if self.video_player:
                self.video_player.state = 'stop'
                self.video_player.source = ''
        else:
            if self.vlc_player:
                self.vlc_player.stop()

