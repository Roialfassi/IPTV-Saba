"""
Fullscreen Screen for IPTV-Saba Android
Full-screen video player with touch controls
Desktop: Embedded VLC player using python-vlc
Android: Uses Kivy Video widget with native backend
"""

import os
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

# Desktop VLC player
if platform != 'android':
    try:
        import vlc
        VLC_AVAILABLE = True
    except ImportError:
        VLC_AVAILABLE = False
else:
    VLC_AVAILABLE = False


class FullscreenScreen(Screen):
    """Fullscreen video player with auto-hiding controls"""

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.channel = None
        self.video_player = None
        self.controls_visible = True
        self.hide_timer = None

        # Desktop VLC player
        self.vlc_instance = None
        self.vlc_player = None
        self.video_frame = None

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

        # Video widget - platform specific
        if platform == 'android':
            from kivy.uix.video import Video
            # Video player (full screen)
            self.video_player = Video(
                state='stop',
                options={'eos': 'loop'},
                size_hint=(1, 1),
                pos_hint={'x': 0, 'y': 0}
            )
            main_layout.add_widget(self.video_player)
        else:
            # Desktop: Create placeholder for VLC or show message if not available
            if VLC_AVAILABLE:
                # Initialize VLC
                self.vlc_instance = vlc.Instance('--no-xlib')  # No xlib for better Kivy compatibility
                self.vlc_player = self.vlc_instance.media_player_new()

                # Create a dummy widget for video area
                from kivy.uix.widget import Widget
                self.video_frame = Widget(
                    size_hint=(1, 1),
                    pos_hint={'x': 0, 'y': 0}
                )
                main_layout.add_widget(self.video_frame)
            else:
                # VLC not available
                self.desktop_label = Label(
                    text="VLC library not found.\n\nPlease install python-vlc:\npip install python-vlc",
                    size_hint=(0.8, 0.3),
                    pos_hint={'center_x': 0.5, 'center_y': 0.5},
                    font_size=dp(16),
                    halign='center',
                    color=(1, 1, 1, 1)
                )
                main_layout.add_widget(self.desktop_label)

        # Controls overlay container
        self.controls_overlay = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(150),
            pos_hint={'x': 0, 'bottom': 1},
            padding=dp(15),
            spacing=dp(10)
        )

        # Set semi-transparent background for controls
        with self.controls_overlay.canvas.before:
            Color(0, 0, 0, 0.7)
            self.controls_bg = Rectangle(
                size=self.controls_overlay.size,
                pos=self.controls_overlay.pos
            )
        self.controls_overlay.bind(
            size=self._update_controls_bg,
            pos=self._update_controls_bg
        )

        # Channel info
        self.channel_label = Label(
            text="",
            size_hint_y=0.3,
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 1)
        )
        self.controls_overlay.add_widget(self.channel_label)

        # Control buttons
        controls_layout = BoxLayout(size_hint_y=0.4, spacing=dp(15))

        # Back button
        back_btn = Button(
            text="Back",
            size_hint_x=0.5,
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(16),
            bold=True
        )
        back_btn.bind(on_press=self.go_back)
        controls_layout.add_widget(back_btn)

        # Play/Pause button (for both Android and desktop with VLC)
        if platform == 'android' or VLC_AVAILABLE:
            self.play_pause_btn = Button(
                text="Pause",
                size_hint_x=0.5,
                background_color=(0.3, 0.3, 0.3, 1),
                font_size=dp(16),
                bold=True
            )
            self.play_pause_btn.bind(on_press=self.toggle_play_pause)
            controls_layout.add_widget(self.play_pause_btn)

        self.controls_overlay.add_widget(controls_layout)

        # Add status label
        self.status_label = Label(
            text="",
            size_hint_y=0.3,
            font_size=dp(14),
            color=(0.8, 0.8, 0.8, 1)
        )
        self.controls_overlay.add_widget(self.status_label)

        main_layout.add_widget(self.controls_overlay)

        self.add_widget(main_layout)

        # Bind touch event for showing/hiding controls
        self.bind(on_touch_down=self.on_screen_touch)

    def _update_bg(self, instance, value):
        """Update background rectangle"""
        self.bg_rect.size = instance.size
        self.bg_rect.pos = instance.pos

    def _update_controls_bg(self, instance, value):
        """Update controls background rectangle"""
        self.controls_bg.size = instance.size
        self.controls_bg.pos = instance.pos

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

            # Schedule auto-hide controls (only for Android)
            if platform == 'android':
                self.schedule_hide_controls()

    def play_stream(self):
        """Start playing the stream"""
        if not self.channel:
            return

        try:
            if platform == 'android':
                # Android: Use Kivy Video widget
                self.video_player.source = self.channel.stream_url
                self.video_player.state = 'play'
                if hasattr(self, 'play_pause_btn'):
                    self.play_pause_btn.text = "Pause"

                self.status_label.text = "Loading stream..."
                self.status_label.color = (0.8, 0.8, 0.8, 1)

                # Bind to video events to track playback
                self.video_player.bind(on_load=self._on_video_load)
                self.video_player.bind(on_error=self._on_video_error)
            else:
                # Desktop: Use embedded VLC player
                if VLC_AVAILABLE and self.vlc_player:
                    # Set window handle for VLC to render into
                    import sys
                    if sys.platform.startswith('linux'):
                        self.vlc_player.set_xwindow(Window.get_window_info()[0])
                    elif sys.platform == 'win32':
                        self.vlc_player.set_hwnd(Window.get_window_info()[0])
                    elif sys.platform == 'darwin':
                        self.vlc_player.set_nsobject(Window.get_window_info()[0])

                    # Load and play media
                    media = self.vlc_instance.media_new(self.channel.stream_url)
                    self.vlc_player.set_media(media)
                    self.vlc_player.play()

                    self.status_label.text = "Playing..."
                    self.status_label.color = (0.2, 1, 0.2, 1)
                else:
                    self.status_label.text = "VLC not available"
                    self.status_label.color = (1, 0.2, 0.2, 1)

        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
            self.status_label.color = (1, 0.2, 0.2, 1)

    def _on_video_load(self, instance):
        """Called when video successfully loads (Android only)"""
        self.status_label.text = "Playing..."
        self.status_label.color = (0.2, 1, 0.2, 1)

    def _on_video_error(self, instance, error):
        """Called when video playback error occurs (Android only)"""
        self.status_label.text = f"Playback error: {error}"
        self.status_label.color = (1, 0.2, 0.2, 1)

    def toggle_play_pause(self, instance):
        """Toggle play/pause"""
        if platform == 'android' and self.video_player:
            if self.video_player.state == 'play':
                self.video_player.state = 'pause'
                self.play_pause_btn.text = "Play"
                self.status_label.text = "Paused"
            else:
                self.video_player.state = 'play'
                self.play_pause_btn.text = "Pause"
                self.status_label.text = "Playing..."
            self.schedule_hide_controls()
        elif VLC_AVAILABLE and self.vlc_player:
            if self.vlc_player.is_playing():
                self.vlc_player.pause()
                self.status_label.text = "Paused"
            else:
                self.vlc_player.play()
                self.status_label.text = "Playing..."

    def on_screen_touch(self, instance, touch):
        """Handle screen touch to show/hide controls"""
        # If touch is on controls, don't toggle
        if self.controls_overlay.collide_point(*touch.pos):
            # Reset hide timer when interacting with controls
            if platform == 'android':
                self.schedule_hide_controls()
            return

        # Toggle controls visibility (only on Android)
        if platform == 'android':
            if self.controls_visible:
                self.hide_controls()
            else:
                self.show_controls()

    def show_controls(self):
        """Show controls overlay"""
        self.controls_visible = True
        self.controls_overlay.opacity = 1
        if platform == 'android':
            self.schedule_hide_controls()

    def hide_controls(self):
        """Hide controls overlay"""
        self.controls_visible = False
        self.controls_overlay.opacity = 0

    def schedule_hide_controls(self):
        """Schedule auto-hide of controls after 3 seconds"""
        # Cancel existing timer
        if self.hide_timer:
            self.hide_timer.cancel()

        # Schedule new hide timer
        self.hide_timer = Clock.schedule_once(lambda dt: self.hide_controls(), 3)

    def go_back(self, instance):
        """Go back to previous screen"""
        # Stop playback
        if platform == 'android' and self.video_player:
            self.video_player.state = 'stop'
            self.video_player.source = ''
        elif VLC_AVAILABLE and self.vlc_player:
            # Stop VLC player on desktop
            self.vlc_player.stop()

        # Cancel hide timer
        if self.hide_timer:
            self.hide_timer.cancel()

        # Go back to channels
        App.get_running_app().switch_screen('channels')

    def on_leave(self):
        """Called when leaving the screen"""
        # Stop playback
        if platform == 'android' and self.video_player:
            self.video_player.state = 'stop'
            self.video_player.source = ''
        elif VLC_AVAILABLE and self.vlc_player:
            # Stop VLC player on desktop
            self.vlc_player.stop()

        # Cancel hide timer
        if self.hide_timer:
            self.hide_timer.cancel()
