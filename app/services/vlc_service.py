"""VLC player service with lifecycle management."""
import vlc
import sys
import logging
from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

logger = logging.getLogger(__name__)


class VLCService(QObject):
    """Centralized VLC player management."""

    playback_started = pyqtSignal()
    playback_stopped = pyqtSignal()
    playback_error = pyqtSignal(str)
    time_changed = pyqtSignal(int)
    position_changed = pyqtSignal(float)

    def __init__(self):
        super().__init__()

        self.instance = vlc.Instance([
            '--no-xlib',
            '--network-caching=1000',
            '--live-caching=300',
            '--avcodec-hw=any',
            '--verbose=0'
        ])

        self.player: Optional[vlc.MediaPlayer] = None
        self.current_url: str = ""

        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._emit_position)
        self.position_timer.setInterval(1000)

    def create_player(self, window_id: int) -> vlc.MediaPlayer:
        """Create player for window."""
        if self.player:
            self.player.stop()
            self.player.release()

        self.player = self.instance.media_player_new()

        if sys.platform.startswith('linux'):
            self.player.set_xwindow(window_id)
        elif sys.platform == 'win32':
            self.player.set_hwnd(window_id)
        elif sys.platform == 'darwin':
            self.player.set_nsobject(window_id)

        em = self.player.event_manager()
        em.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_playing)
        em.event_attach(vlc.EventType.MediaPlayerStopped, self._on_stopped)
        em.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_error)

        return self.player

    def play(self, url: str):
        """Play URL."""
        if not self.player:
            logger.error("Player not initialized")
            return

        try:
            self.current_url = url
            media = self.instance.media_new(url)
            media.add_option(':network-caching=1000')
            self.player.set_media(media)
            self.player.play()
            logger.info(f"Playing: {url}")
        except Exception as e:
            logger.error(f"Playback failed: {e}")
            self.playback_error.emit(str(e))

    def stop(self):
        """Stop playback."""
        if self.player:
            self.player.stop()
            self.position_timer.stop()

    def pause(self):
        """Toggle pause."""
        if self.player:
            self.player.pause()

    def is_playing(self) -> bool:
        """Check if playing."""
        return self.player and self.player.is_playing()

    def get_time(self) -> int:
        """Get current time (ms)."""
        return self.player.get_time() if self.player else 0

    def get_length(self) -> int:
        """Get total length (ms)."""
        return self.player.get_length() if self.player else 0

    def set_volume(self, volume: int):
        """Set volume (0-100)."""
        if self.player:
            self.player.audio_set_volume(volume)

    def get_volume(self) -> int:
        """Get volume (0-100)."""
        return self.player.audio_get_volume() if self.player else 0

    def _on_playing(self, event):
        self.playback_started.emit()
        self.position_timer.start()

    def _on_stopped(self, event):
        self.playback_stopped.emit()
        self.position_timer.stop()

    def _on_error(self, event):
        self.playback_error.emit("Playback error")

    def _emit_position(self):
        if self.player and self.player.is_playing():
            time_ms = self.get_time()
            self.time_changed.emit(time_ms)

    def cleanup(self):
        """Release resources."""
        self.stop()
        if self.player:
            self.player.release()
        if self.instance:
            self.instance.release()
