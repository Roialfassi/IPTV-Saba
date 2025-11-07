"""
Fullscreen Screen for IPTV-Saba Android
Full-screen video player with touch controls
Desktop: Embedded VLC player using python-vlc (with external fallback)
Android: Uses Kivy Video widget with native backend
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
        self.vlc_process = None  # For external VLC fallback
        self.use_external_vlc = False  # Flag for external VLC mode

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

        # Controls overlay container - increased height for more controls
        self.controls_overlay = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=dp(200),
            pos_hint={'x': 0, 'bottom': 1},
            padding=dp(15),
            spacing=dp(10)
        )

        # Set semi-transparent background for controls
        with self.controls_overlay.canvas.before:
            Color(0, 0, 0, 0.8)
            self.controls_bg = Rectangle(
                size=self.controls_overlay.size,
                pos=self.controls_overlay.pos
            )
        self.controls_overlay.bind(
            size=self._update_controls_bg,
            pos=self._update_controls_bg
        )

        # Top row: Channel info and close button
        top_row = BoxLayout(size_hint_y=0.25, spacing=dp(10))

        self.channel_label = Label(
            text="",
            size_hint_x=0.8,
            font_size=dp(18),
            bold=True,
            color=(1, 1, 1, 1),
            halign='left',
            valign='middle'
        )
        self.channel_label.bind(size=self.channel_label.setter('text_size'))
        top_row.add_widget(self.channel_label)

        # Close/Back button (always visible)
        close_btn = Button(
            text="X",
            size_hint_x=0.2,
            background_color=(0.898, 0.035, 0.078, 1),
            font_size=dp(20),
            bold=True
        )
        close_btn.bind(on_press=self.go_back)
        top_row.add_widget(close_btn)

        self.controls_overlay.add_widget(top_row)

        # Middle row: Play/Pause and navigation buttons
        middle_row = BoxLayout(size_hint_y=0.3, spacing=dp(10))

        # Back to channels button
        back_channels_btn = Button(
            text="< Channels",
            size_hint_x=0.33,
            background_color=(0.3, 0.3, 0.3, 1),
            font_size=dp(14),
            bold=True
        )
        back_channels_btn.bind(on_press=self.go_back)
        middle_row.add_widget(back_channels_btn)

        # Play/Pause button (for both Android and desktop with VLC)
        if platform == 'android' or VLC_AVAILABLE:
            self.play_pause_btn = Button(
                text="Pause",
                size_hint_x=0.34,
                background_color=(0.2, 0.6, 0.2, 1),
                font_size=dp(16),
                bold=True
            )
            self.play_pause_btn.bind(on_press=self.toggle_play_pause)
            middle_row.add_widget(self.play_pause_btn)

        # Stop button
        stop_btn = Button(
            text="Stop",
            size_hint_x=0.33,
            background_color=(0.6, 0.2, 0.2, 1),
            font_size=dp(14),
            bold=True
        )
        stop_btn.bind(on_press=self.stop_playback)
        middle_row.add_widget(stop_btn)

        self.controls_overlay.add_widget(middle_row)

        # Volume row (always show for both platforms)
        volume_row = BoxLayout(size_hint_y=0.25, spacing=dp(10))

        volume_label = Label(
            text="Volume:",
            size_hint_x=0.2,
            font_size=dp(14),
            color=(1, 1, 1, 1)
        )
        volume_row.add_widget(volume_label)

        self.volume_slider = Slider(
            min=0,
            max=100,
            value=50,
            size_hint_x=0.6
        )
        self.volume_slider.bind(value=self.on_volume_change)
        volume_row.add_widget(self.volume_slider)

        self.volume_value_label = Label(
            text="50%",
            size_hint_x=0.2,
            font_size=dp(14),
            color=(1, 1, 1, 1)
        )
        volume_row.add_widget(self.volume_value_label)

        self.controls_overlay.add_widget(volume_row)

        # Status label
        self.status_label = Label(
            text="",
            size_hint_y=0.2,
            font_size=dp(12),
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

            # On desktop, keep controls visible
            # On Android, schedule auto-hide controls
            if platform == 'android':
                self.schedule_hide_controls()
            else:
                # Desktop: keep controls visible
                self.controls_visible = True
                self.controls_overlay.opacity = 1

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

                # Set initial volume
                self.video_player.volume = self.volume_slider.value / 100.0

                self.status_label.text = "Loading stream..."
                self.status_label.color = (0.8, 0.8, 0.8, 1)

                # Bind to video events to track playback
                self.video_player.bind(on_load=self._on_video_load)
                self.video_player.bind(on_error=self._on_video_error)
            else:
                # Desktop: Use embedded VLC player
                if VLC_AVAILABLE and self.vlc_player:
                    try:
                        # Get window handle based on platform
                        import sys

                        # Try to get window handle
                        if sys.platform.startswith('linux'):
                            # Linux - try to get X window ID
                            try:
                                win_info = Window.get_window_info()
                                if win_info and hasattr(win_info, 'window'):
                                    self.vlc_player.set_xwindow(win_info.window)
                                elif isinstance(win_info, dict) and 'window' in win_info:
                                    self.vlc_player.set_xwindow(win_info['window'])
                                else:
                                    # Fallback: get from SDL
                                    from ctypes import pythonapi, c_void_p
                                    pythonapi.SDL_GetWindowWMInfo.restype = c_void_p
                                    # Continue without setting window (will open in separate window)
                            except Exception as e:
                                self.status_label.text = f"Window handle error (Linux): {e}"

                        elif sys.platform == 'win32':
                            # Windows - try to get HWND
                            try:
                                win_info = Window.get_window_info()
                                if win_info and hasattr(win_info, 'window'):
                                    self.vlc_player.set_hwnd(win_info.window)
                                elif isinstance(win_info, dict) and 'window' in win_info:
                                    self.vlc_player.set_hwnd(win_info['window'])
                                else:
                                    # Fallback: Try using ctypes to get HWND
                                    import ctypes
                                    from ctypes import wintypes
                                    user32 = ctypes.windll.user32
                                    # Get window title and find window
                                    hwnd = user32.FindWindowW(None, Window.get_title())
                                    if hwnd:
                                        self.vlc_player.set_hwnd(hwnd)
                            except Exception as e:
                                self.status_label.text = f"Window handle error (Windows): {e}"

                        elif sys.platform == 'darwin':
                            # macOS - try to get NSView
                            try:
                                win_info = Window.get_window_info()
                                if win_info and hasattr(win_info, 'nsview'):
                                    self.vlc_player.set_nsobject(win_info.nsview)
                                elif isinstance(win_info, dict) and 'nsview' in win_info:
                                    self.vlc_player.set_nsobject(win_info['nsview'])
                            except Exception as e:
                                self.status_label.text = f"Window handle error (macOS): {e}"

                        # Load and play media
                        media = self.vlc_instance.media_new(self.channel.stream_url)
                        self.vlc_player.set_media(media)
                        self.vlc_player.play()

                        # Set initial volume
                        self.vlc_player.audio_set_volume(int(self.volume_slider.value))

                        self.status_label.text = "Playing embedded..."
                        self.status_label.color = (0.2, 1, 0.2, 1)

                    except Exception as e:
                        # Fallback to external VLC if embedding fails
                        self.status_label.text = f"Embedding failed, opening external VLC..."
                        self.status_label.color = (1, 1, 0.2, 1)
                        self.open_external_vlc()
                else:
                    # No python-vlc, try external VLC
                    self.status_label.text = "Opening external VLC..."
                    self.status_label.color = (1, 1, 0.2, 1)
                    self.open_external_vlc()

        except Exception as e:
            self.status_label.text = f"Error: {str(e)}"
            self.status_label.color = (1, 0.2, 0.2, 1)

    def open_external_vlc(self):
        """Open stream in external VLC player (fallback)"""
        if not self.channel:
            return

        try:
            import sys
            stream_url = self.channel.stream_url

            if sys.platform == 'win32':
                # Try common VLC installation paths on Windows
                vlc_paths = [
                    r'C:\Program Files\VideoLAN\VLC\vlc.exe',
                    r'C:\Program Files (x86)\VideoLAN\VLC\vlc.exe',
                ]
                vlc_exe = None
                for path in vlc_paths:
                    if os.path.exists(path):
                        vlc_exe = path
                        break

                if vlc_exe:
                    self.vlc_process = subprocess.Popen([vlc_exe, stream_url])
                else:
                    # Try to open with default handler
                    self.vlc_process = subprocess.Popen(['vlc', stream_url], shell=True)

                self.use_external_vlc = True
                self.status_label.text = "Playing in external VLC"
                self.status_label.color = (0.2, 1, 0.2, 1)

            elif sys.platform.startswith('linux'):
                self.vlc_process = subprocess.Popen(['vlc', stream_url])
                self.use_external_vlc = True
                self.status_label.text = "Playing in external VLC"
                self.status_label.color = (0.2, 1, 0.2, 1)

            elif sys.platform == 'darwin':
                self.vlc_process = subprocess.Popen(['open', '-a', 'VLC', stream_url])
                self.use_external_vlc = True
                self.status_label.text = "Playing in external VLC"
                self.status_label.color = (0.2, 1, 0.2, 1)

        except FileNotFoundError:
            self.status_label.text = "VLC not found. Please install VLC."
            self.status_label.color = (1, 0.2, 0.2, 1)
        except Exception as e:
            self.status_label.text = f"Error opening VLC: {str(e)}"
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
        if platform == 'android' and self.video_player:
            self.video_player.state = 'stop'
            if hasattr(self, 'play_pause_btn'):
                self.play_pause_btn.text = "Play"
            self.status_label.text = "Stopped"
        elif VLC_AVAILABLE and self.vlc_player and not self.use_external_vlc:
            self.vlc_player.stop()
            if hasattr(self, 'play_pause_btn'):
                self.play_pause_btn.text = "Play"
            self.status_label.text = "Stopped"

    def on_volume_change(self, instance, value):
        """Handle volume change"""
        # Update volume label
        self.volume_value_label.text = f"{int(value)}%"

        # Apply volume to player
        if platform == 'android' and self.video_player:
            self.video_player.volume = value / 100.0
        elif VLC_AVAILABLE and self.vlc_player and not self.use_external_vlc:
            self.vlc_player.audio_set_volume(int(value))

        # Reset hide timer on Android
        if platform == 'android':
            self.schedule_hide_controls()

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
        elif VLC_AVAILABLE and self.vlc_player and not self.use_external_vlc:
            if self.vlc_player.is_playing():
                self.vlc_player.pause()
                self.play_pause_btn.text = "Play"
                self.status_label.text = "Paused"
            else:
                self.vlc_player.play()
                self.play_pause_btn.text = "Pause"
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
        elif VLC_AVAILABLE and self.vlc_player and not self.use_external_vlc:
            # Stop embedded VLC player on desktop
            self.vlc_player.stop()
        elif self.vlc_process:
            # Terminate external VLC process
            try:
                self.vlc_process.terminate()
            except:
                pass

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
        elif VLC_AVAILABLE and self.vlc_player and not self.use_external_vlc:
            # Stop embedded VLC player on desktop
            self.vlc_player.stop()
        elif self.vlc_process:
            # Terminate external VLC process
            try:
                self.vlc_process.terminate()
            except:
                pass

        # Cancel hide timer
        if self.hide_timer:
            self.hide_timer.cancel()
