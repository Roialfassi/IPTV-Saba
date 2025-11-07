"""
Fullscreen Screen for IPTV-Saba Android
Full-screen video player with touch controls
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.video import Video
from kivy.uix.slider import Slider
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window


class FullscreenScreen(Screen):
    """Fullscreen video player with auto-hiding controls"""

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.channel = None
        self.video_player = None
        self.controls_visible = True
        self.hide_timer = None

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

        # Video player (full screen)
        self.video_player = Video(
            state='stop',
            options={'eos': 'loop'},
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )
        main_layout.add_widget(self.video_player)

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
            size_hint_x=0.25,
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=dp(16),
            bold=True
        )
        back_btn.bind(on_press=self.go_back)
        controls_layout.add_widget(back_btn)

        # Play/Pause button
        self.play_pause_btn = Button(
            text="Pause",
            size_hint_x=0.25,
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(16),
            bold=True
        )
        self.play_pause_btn.bind(on_press=self.toggle_play_pause)
        controls_layout.add_widget(self.play_pause_btn)

        # Volume controls
        volume_layout = BoxLayout(size_hint_x=0.5, spacing=dp(10))
        volume_layout.add_widget(Label(
            text="Vol",
            font_size=dp(14),
            size_hint_x=0.15
        ))

        self.volume_slider = Slider(
            min=0,
            max=100,
            value=50,
            size_hint_x=0.85
        )
        self.volume_slider.bind(value=self.on_volume_change)
        volume_layout.add_widget(self.volume_slider)

        controls_layout.add_widget(volume_layout)

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

            # Schedule auto-hide controls
            self.schedule_hide_controls()

    def play_stream(self):
        """Start playing the stream"""
        if not self.channel:
            return

        try:
            # Set video source
            self.video_player.source = self.channel.stream_url
            self.video_player.state = 'play'
            self.play_pause_btn.text = "Pause"

            # Set initial volume
            self.video_player.volume = self.volume_slider.value / 100.0

            self.status_label.text = "Loading stream..."
            self.status_label.color = (0.8, 0.8, 0.8, 1)

            # Bind to video events to track playback
            self.video_player.bind(on_load=self._on_video_load)
            self.video_player.bind(on_error=self._on_video_error)

        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
            self.status_label.color = (1, 0.2, 0.2, 1)

    def _on_video_load(self, instance):
        """Called when video successfully loads"""
        self.status_label.text = "Playing..."
        self.status_label.color = (0.2, 1, 0.2, 1)

    def _on_video_error(self, instance, error):
        """Called when video playback error occurs"""
        error_msg = "Video backend not available. Install GStreamer or ffpyplayer."
        self.status_label.text = error_msg
        self.status_label.color = (1, 0.2, 0.2, 1)

    def toggle_play_pause(self, instance):
        """Toggle play/pause"""
        if self.video_player.state == 'play':
            self.video_player.state = 'pause'
            self.play_pause_btn.text = "Play"
            self.status_label.text = "Paused"
        else:
            self.video_player.state = 'play'
            self.play_pause_btn.text = "Pause"
            self.status_label.text = "Playing..."

        # Reset hide timer
        self.schedule_hide_controls()

    def on_volume_change(self, instance, value):
        """Handle volume change"""
        if self.video_player:
            self.video_player.volume = value / 100.0

        # Reset hide timer
        self.schedule_hide_controls()

    def on_screen_touch(self, instance, touch):
        """Handle screen touch to show/hide controls"""
        # If touch is on controls, don't toggle
        if self.controls_overlay.collide_point(*touch.pos):
            # Reset hide timer when interacting with controls
            self.schedule_hide_controls()
            return

        # Toggle controls visibility
        if self.controls_visible:
            self.hide_controls()
        else:
            self.show_controls()

    def show_controls(self):
        """Show controls overlay"""
        self.controls_visible = True
        self.controls_overlay.opacity = 1
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
        if self.video_player:
            self.video_player.state = 'stop'
            self.video_player.source = ''

        # Cancel hide timer
        if self.hide_timer:
            self.hide_timer.cancel()

        # Go back to channels
        App.get_running_app().switch_screen('channels')

    def on_leave(self):
        """Called when leaving the screen"""
        # Stop playback
        if self.video_player:
            self.video_player.state = 'stop'
            self.video_player.source = ''

        # Cancel hide timer
        if self.hide_timer:
            self.hide_timer.cancel()
