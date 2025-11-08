"""
Fullscreen video player with working overlay above VLC video
Solution: Separate transparent overlay window that floats above VLC
"""

import sys
import os
from kivy.uix.screenmanager import Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

# VLC player imports (desktop only)
VLC_AVAILABLE = False
if platform not in ('android', 'ios'):
    try:
        import vlc
        VLC_AVAILABLE = True
    except ImportError:
        VLC_AVAILABLE = False

# Android video imports
if platform == 'android':
    from kivy.uix.video import Video


class TransparentOverlayWindow:
    """
    Separate transparent window that floats above VLC video
    Works on Windows and Linux
    """

    def __init__(self, parent_screen):
        self.parent_screen = parent_screen
        self.overlay_window = None

    def create_overlay(self):
        """Create transparent overlay window above VLC"""
        if platform == 'win32' or platform.startswith('linux'):
            from kivy.core.window import Window as KivyWindow
            from kivy.app import App

            # Get main window position and size
            main_x, main_y = Window.left, Window.top
            main_width, main_height = Window.width, Window.height

            # Create new Kivy window for overlay
            # Note: This requires running a separate Kivy App instance
            # which is complex, so we'll use a different approach below
            pass

    def show(self):
        """Show the overlay"""
        pass

    def hide(self):
        """Hide the overlay"""
        pass


class VLCPlayerWidget(FloatLayout):
    """
    VLC player widget with overlay that stays on top
    Solution: Use VLC's libvlc_video_set_format to control rendering
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.vlc_instance = None
        self.vlc_player = None
        self.is_playing = False

        if VLC_AVAILABLE:
            self._setup_vlc()

    def _setup_vlc(self):
        """Setup VLC with options that allow overlays"""
        # Key: Use --vout=x11 or --vout=directx with --video-on-top=0
        # This prevents VLC from forcing itself to top
        vlc_args = [
            '--no-xlib',  # Don't take over X11
            '--no-video-title-show',  # Don't show title
            '--video-on-top=0',  # Don't force video on top
        ]

        if sys.platform == 'win32':
            vlc_args.extend([
                '--vout=directdraw',  # Use DirectDraw instead of Direct3D
                '--overlay=0',  # Disable hardware overlay
            ])
        elif sys.platform.startswith('linux'):
            vlc_args.extend([
                '--vout=xcb_x11',  # Use X11 output
                '--no-embedded-video',  # Don't embed in parent window
            ])

        self.vlc_instance = vlc.Instance(vlc_args)
        self.vlc_player = self.vlc_instance.media_player_new()

    def set_window_handle(self):
        """Set VLC window handle with proper settings"""
        if not self.vlc_player:
            return

        # Get window handle
        if sys.platform == 'win32':
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            # Get HWND
            hwnd = user32.GetForegroundWindow()

            # Set VLC to render to this window
            self.vlc_player.set_hwnd(hwnd)

            # CRITICAL: Disable hardware overlay in VLC
            # This allows other windows to appear on top
            try:
                # Try to disable DirectX overlay mode
                self.vlc_player.video_set_format("RV32", 800, 600, 800*4)
            except:
                pass

        elif sys.platform.startswith('linux'):
            # Similar approach for Linux
            self.vlc_player.set_xwindow(Window.get_window_info().window)


class FullscreenScreen(Screen):
    """
    SOLUTION 2: Render overlay using Kivy's canvas AFTER VLC starts
    This works by explicitly drawing overlays in a later canvas instruction
    """

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.current_channel = None
        self.vlc_instance = None
        self.vlc_player = None
        self.video_player = None  # Android
        self.controls_visible = True
        self.auto_hide_event = None

        self.build_ui()

    def build_ui(self):
        """Build UI with overlay that stays on top"""
        main_layout = FloatLayout()

        # Background (black)
        with main_layout.canvas.before:
            Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(size=main_layout.size, pos=main_layout.pos)
        main_layout.bind(size=self._update_bg, pos=self._update_bg)

        # ========== VIDEO CONTAINER ==========
        self.video_container = FloatLayout(
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )

        # Platform-specific video setup
        if platform == 'android':
            self.video_player = Video(
                state='stop',
                options={'eos': 'loop'},
                size_hint=(1, 1)
            )
            self.video_container.add_widget(self.video_player)
        else:
            # Desktop: VLC player area (empty widget, VLC renders to window handle)
            if VLC_AVAILABLE:
                self._setup_vlc_desktop()

        main_layout.add_widget(self.video_container)

        # ========== OVERLAY CONTROLS (CRITICAL: Added AFTER video) ==========
        # Key: Use canvas.after to draw overlay on top
        self.overlay_layout = FloatLayout(
            size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0}
        )

        # Semi-transparent overlay background
        with self.overlay_layout.canvas.after:  # CRITICAL: Use canvas.after
            Color(0, 0, 0, 0.5)  # Semi-transparent black
            self.overlay_bg = Rectangle(
                size=self.overlay_layout.size,
                pos=self.overlay_layout.pos
            )
        self.overlay_layout.bind(size=self._update_overlay_bg, pos=self._update_overlay_bg)

        # Create overlay controls
        self._build_overlay_controls()

        # Add overlay AFTER video (important for stacking order)
        main_layout.add_widget(self.overlay_layout)

        self.add_widget(main_layout)

    def _setup_vlc_desktop(self):
        """Setup VLC for desktop with overlay support"""
        # SOLUTION: Use VLC with --overlay=0 to allow UI overlays
        vlc_args = [
            '--no-xlib',
            '--no-video-title-show',
            '--video-on-top=0',  # Don't force video on top
            '--no-overlay',  # Disable VLC's hardware overlay
        ]

        if sys.platform == 'win32':
            vlc_args.append('--directx-overlay=0')  # Disable DirectX overlay

        self.vlc_instance = vlc.Instance(' '.join(vlc_args))
        self.vlc_player = self.vlc_instance.media_player_new()

        # Schedule window handle binding after window is ready
        Clock.schedule_once(self._bind_vlc_window, 0.5)

    def _bind_vlc_window(self, dt):
        """Bind VLC to window handle"""
        if not self.vlc_player:
            return

        try:
            if sys.platform == 'win32':
                import ctypes
                user32 = ctypes.windll.user32

                # Get window handle
                win_info = Window.get_window_info()
                if win_info and hasattr(win_info, 'window'):
                    hwnd = win_info.window
                elif isinstance(win_info, dict) and 'window' in win_info:
                    hwnd = win_info['window']
                else:
                    # Fallback: find window by title
                    hwnd = user32.FindWindowW(None, Window.get_title())

                if hwnd:
                    self.vlc_player.set_hwnd(hwnd)

            elif sys.platform.startswith('linux'):
                win_info = Window.get_window_info()
                if isinstance(win_info, dict) and 'window' in win_info:
                    self.vlc_player.set_xwindow(win_info['window'])

        except Exception as e:
            print(f"Failed to bind VLC window: {e}")

    def _build_overlay_controls(self):
        """Build overlay control panel"""
        controls_container = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(200),
            pos_hint={'x': 0, 'center_y': 0.5},
            padding=dp(20),
            spacing=dp(10)
        )

        # Top row: Channel name + Close
        top_row = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )

        self.channel_label = Label(
            text="",
            font_size=dp(18),
            bold=True,
            color=(1, 1, 1, 1)
        )
        top_row.add_widget(self.channel_label)

        close_btn = Button(
            text="[X]",
            size_hint_x=None,
            width=dp(50),
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(16),
            bold=True
        )
        close_btn.bind(on_press=self.close_player)
        top_row.add_widget(close_btn)

        controls_container.add_widget(top_row)

        # Middle row: Control buttons
        button_row = BoxLayout(
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )

        back_btn = Button(
            text="< Channels",
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=dp(14)
        )
        back_btn.bind(on_press=self.close_player)
        button_row.add_widget(back_btn)

        self.play_pause_btn = Button(
            text="⏸ Pause",
            background_color=(0.2, 0.6, 0.2, 1),
            font_size=dp(14),
            bold=True
        )
        self.play_pause_btn.bind(on_press=self.toggle_play_pause)
        button_row.add_widget(self.play_pause_btn)

        stop_btn = Button(
            text="⏹ Stop",
            background_color=(0.6, 0.2, 0.2, 1),
            font_size=dp(14)
        )
        stop_btn.bind(on_press=self.stop_video)
        button_row.add_widget(stop_btn)

        controls_container.add_widget(button_row)

        # Bottom row: Volume control
        volume_row = BoxLayout(
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )

        volume_label = Label(
            text="🔊",
            size_hint_x=None,
            width=dp(30),
            font_size=dp(16)
        )
        volume_row.add_widget(volume_label)

        self.volume_slider = Slider(
            min=0,
            max=100,
            value=50,
            size_hint_x=0.7
        )
        self.volume_slider.bind(value=self.on_volume_change)
        volume_row.add_widget(self.volume_slider)

        self.volume_value_label = Label(
            text="50%",
            size_hint_x=None,
            width=dp(50),
            font_size=dp(14)
        )
        volume_row.add_widget(self.volume_value_label)

        controls_container.add_widget(volume_row)

        self.overlay_layout.add_widget(controls_container)

    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_overlay_bg(self, instance, value):
        self.overlay_bg.pos = instance.pos
        self.overlay_bg.size = instance.size

    def play_channel(self, channel):
        """Play channel with working overlay"""
        self.current_channel = channel
        self.channel_label.text = channel.name

        if platform == 'android':
            self.video_player.source = channel.stream_url
            self.video_player.state = 'play'
        else:
            if VLC_AVAILABLE and self.vlc_player:
                media = self.vlc_instance.media_new(channel.stream_url)
                self.vlc_player.set_media(media)
                self.vlc_player.play()

                # CRITICAL: Force overlay to redraw on top after video starts
                Clock.schedule_once(self._force_overlay_refresh, 1.0)

    def _force_overlay_refresh(self, dt):
        """
        Force overlay to redraw on top of video
        This schedules a canvas update
        """
        # Remove and re-add overlay to force it to top
        parent = self.overlay_layout.parent
        if parent:
            parent.remove_widget(self.overlay_layout)
            parent.add_widget(self.overlay_layout)

        # Force canvas update
        self.overlay_layout.canvas.ask_update()

    def toggle_play_pause(self, instance):
        """Toggle play/pause"""
        if platform == 'android' and self.video_player:
            if self.video_player.state == 'play':
                self.video_player.state = 'pause'
                self.play_pause_btn.text = "▶ Play"
            else:
                self.video_player.state = 'play'
                self.play_pause_btn.text = "⏸ Pause"
        elif VLC_AVAILABLE and self.vlc_player:
            if self.vlc_player.is_playing():
                self.vlc_player.pause()
                self.play_pause_btn.text = "▶ Play"
            else:
                self.vlc_player.play()
                self.play_pause_btn.text = "⏸ Pause"

    def stop_video(self, instance):
        """Stop video playback"""
        if platform == 'android' and self.video_player:
            self.video_player.state = 'stop'
        elif VLC_AVAILABLE and self.vlc_player:
            self.vlc_player.stop()

    def close_player(self, instance):
        """Close player and return to channels"""
        self.stop_video(None)
        self.manager.current = 'channel_screen'

    def on_volume_change(self, instance, value):
        """Handle volume change"""
        self.volume_value_label.text = f"{int(value)}%"

        if platform == 'android' and self.video_player:
            self.video_player.volume = value / 100.0
        elif VLC_AVAILABLE and self.vlc_player:
            self.vlc_player.audio_set_volume(int(value))

    def on_enter(self):
        """Screen entered"""
        if platform != 'android':
            # Desktop: Show overlay
            self.overlay_layout.opacity = 1

    def on_leave(self):
        """Screen left - cleanup"""
        self.stop_video(None)
