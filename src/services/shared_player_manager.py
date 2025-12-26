"""
Shared Player Manager - Singleton for managing VLC player across views.

This module provides a centralized VLC player instance that can be attached
to different video frames, enabling seamless transitions between the
ChooseChannelScreen and FullScreenView without playback interruption.

Uses a state machine pattern to manage view transitions properly.
"""
import sys
import logging
from enum import Enum, auto
from typing import Optional, Callable
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget
import vlc

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class PlayerViewState(Enum):
    """States for the player view state machine."""
    IDLE = auto()           # No view attached, player stopped
    EMBEDDED = auto()       # Playing in embedded view (ChooseChannelScreen)
    TRANSITIONING = auto()  # Transitioning between views
    FULLSCREEN = auto()     # Playing in fullscreen view


class SharedPlayerManager(QObject):
    """
    Singleton class that manages a shared VLC player instance with proper
    state machine for view transitions.
    
    The state machine ensures:
    1. Player is properly detached before transitioning
    2. New window is fully ready before attachment
    3. Media continues playing without interruption
    """
    
    # Singleton instance
    _instance: Optional['SharedPlayerManager'] = None
    
    # Signals
    state_changed = pyqtSignal(object)  # PlayerViewState
    channel_changed = pyqtSignal(object)  # Channel or None
    playback_started = pyqtSignal()
    playback_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __new__(cls, *args, **kwargs):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(SharedPlayerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the SharedPlayerManager."""
        if self._initialized:
            return
            
        super().__init__()
        
        # VLC initialization with platform-specific settings
        args = self._get_vlc_args()
        self._vlc_instance = vlc.Instance(args)
        self._player = self._vlc_instance.media_player_new()
        
        # State machine
        self._state = PlayerViewState.IDLE
        self._pending_state: Optional[PlayerViewState] = None
        
        # View references
        self._embedded_frame: Optional[QWidget] = None
        self._fullscreen_frame: Optional[QWidget] = None
        self._current_frame: Optional[QWidget] = None
        
        # Channel tracking
        self._current_channel = None
        self._current_url: Optional[str] = None
        
        # Playback state
        self._volume: int = 50
        self._was_playing: bool = False
        self._saved_position: float = 0.0
        
        # Set initial volume
        self._player.audio_set_volume(self._volume)
        
        self._initialized = True
        logger.info("SharedPlayerManager initialized with state machine")
    
    def _get_vlc_args(self) -> list:
        """Get platform-specific VLC arguments."""
        if sys.platform == "win32":
            vlc_plugins_path = r'C:\Program Files\VideoLAN\VLC\plugins'
            return ['--no-plugins-cache', f'--plugin-path={vlc_plugins_path}']
        return []
    
    @classmethod
    def get_instance(cls) -> 'SharedPlayerManager':
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset the singleton instance (mainly for app cleanup)."""
        if cls._instance is not None:
            cls._instance.cleanup()
            cls._instance = None
    
    # ========================= Properties =========================
    
    @property
    def player(self) -> vlc.MediaPlayer:
        """Get the underlying VLC player instance."""
        return self._player
    
    @property
    def vlc_instance(self) -> vlc.Instance:
        """Get the VLC instance."""
        return self._vlc_instance
    
    @property
    def state(self) -> PlayerViewState:
        """Get the current view state."""
        return self._state
    
    @property
    def current_channel(self):
        """Get the currently playing channel."""
        return self._current_channel
    
    @property
    def is_playing(self) -> bool:
        """Check if the player is currently playing."""
        return self._player.is_playing() == 1
    
    @property
    def volume(self) -> int:
        """Get the current volume (0-100)."""
        return self._volume
    
    @volume.setter
    def volume(self, value: int):
        """Set the volume (0-100)."""
        self._volume = max(0, min(100, value))
        self._player.audio_set_volume(self._volume)
    
    # ========================= State Machine =========================
    
    def _set_state(self, new_state: PlayerViewState):
        """Update state and emit signal."""
        old_state = self._state
        self._state = new_state
        logger.info(f"State transition: {old_state.name} -> {new_state.name}")
        self.state_changed.emit(new_state)
    
    # ========================= Frame Registration =========================
    
    def register_embedded_frame(self, frame: QWidget):
        """Register the embedded video frame (from ChooseChannelScreen)."""
        self._embedded_frame = frame
        logger.info(f"Registered embedded frame: {frame}")
    
    def register_fullscreen_frame(self, frame: QWidget):
        """Register the fullscreen video frame."""
        self._fullscreen_frame = frame
        logger.info(f"Registered fullscreen frame: {frame}")
    
    def unregister_fullscreen_frame(self):
        """Unregister the fullscreen frame (when closing fullscreen)."""
        self._fullscreen_frame = None
        logger.info("Unregistered fullscreen frame")
    
    # ========================= Platform-Specific Attachment =========================
    
    def _attach_to_frame(self, frame: QWidget) -> bool:
        """Attach the player to a frame using platform-specific methods."""
        if not frame:
            logger.error("Cannot attach to None frame")
            return False
        
        try:
            win_id = int(frame.winId())
            logger.info(f"Attaching player to window ID: {win_id}")
            
            if sys.platform.startswith('linux'):
                self._player.set_xwindow(win_id)
            elif sys.platform == "win32":
                self._player.set_hwnd(win_id)
            elif sys.platform == "darwin":
                self._player.set_nsobject(win_id)
            else:
                logger.error(f"Unsupported platform: {sys.platform}")
                return False
            
            self._current_frame = frame
            logger.info(f"✓ Player attached to window ID: {win_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error attaching player: {e}")
            return False
    
    # ========================= Playback Control =========================
    
    def play_channel(self, channel, frame: QWidget = None) -> bool:
        """
        Start playing a channel.
        
        Args:
            channel: The channel object to play (must have stream_url)
            frame: The video frame to attach to (defaults to embedded frame)
        """
        if not channel or not hasattr(channel, 'stream_url'):
            logger.error("Invalid channel object")
            return False
        
        target_frame = frame or self._embedded_frame
        if not target_frame:
            logger.error("No frame available for playback")
            return False
        
        try:
            # Attach to frame first
            if not self._attach_to_frame(target_frame):
                return False
            
            # Create and set media
            media = self._vlc_instance.media_new(channel.stream_url)
            if not media:
                self.error_occurred.emit(f"Failed to create media for {channel.name}")
                return False
            
            self._player.set_media(media)
            
            # Start playback
            result = self._player.play()
            
            if result == 0:
                self._current_channel = channel
                self._current_url = channel.stream_url
                self._set_state(PlayerViewState.EMBEDDED if target_frame == self._embedded_frame 
                               else PlayerViewState.FULLSCREEN)
                self.channel_changed.emit(channel)
                self.playback_started.emit()
                logger.info(f"Started playing: {channel.name}")
                return True
            else:
                self.error_occurred.emit(f"Failed to start playback")
                return False
                
        except Exception as e:
            logger.error(f"Error playing channel: {e}")
            self.error_occurred.emit(str(e))
            return False
    
    def play(self):
        """Resume playback."""
        if self._player.get_media():
            self._player.play()
            self.playback_started.emit()
    
    def pause(self):
        """Pause playback."""
        self._player.pause()
    
    def stop(self):
        """Stop playback."""
        self._player.stop()
        self._set_state(PlayerViewState.IDLE)
        self.playback_stopped.emit()
    
    def set_volume(self, value: int):
        """Set volume level (0-100)."""
        self.volume = value
    
    # ========================= View Transitions =========================
    
    def transition_to_fullscreen(self, fullscreen_frame: QWidget) -> bool:
        """
        Transition from embedded to fullscreen view.
        
        This handles the complete transition:
        1. Save current playback state
        2. Register fullscreen frame
        3. Stop current playback (VLC requirement for clean window switch)
        4. Reattach to fullscreen frame
        5. Restart playback
        """
        if self._state == PlayerViewState.FULLSCREEN:
            logger.warning("Already in fullscreen state")
            return True
        
        logger.info("=== TRANSITION TO FULLSCREEN ===")
        self._set_state(PlayerViewState.TRANSITIONING)
        
        # Save current state
        self._was_playing = self.is_playing
        self._saved_position = self._player.get_position() or 0.0
        saved_url = self._current_url
        
        logger.info(f"Saved state: playing={self._was_playing}, pos={self._saved_position}")
        
        # Register the fullscreen frame
        self.register_fullscreen_frame(fullscreen_frame)
        
        # Stop the player completely (VLC needs this for clean window switch)
        self._player.stop()
        
        # Schedule the reattachment after a delay to ensure window is ready
        QTimer.singleShot(100, lambda: self._complete_fullscreen_transition(saved_url))
        
        return True
    
    def _complete_fullscreen_transition(self, url: str):
        """Complete the fullscreen transition after delay."""
        if not self._fullscreen_frame:
            logger.error("Fullscreen frame not available")
            self._set_state(PlayerViewState.IDLE)
            return
        
        logger.info("Completing fullscreen transition...")
        
        # Attach to fullscreen frame
        if not self._attach_to_frame(self._fullscreen_frame):
            logger.error("Failed to attach to fullscreen frame")
            self._set_state(PlayerViewState.IDLE)
            return
        
        # Create new media and start playback
        if url:
            media = self._vlc_instance.media_new(url)
            self._player.set_media(media)
            
            if self._was_playing:
                self._player.play()
                # Restore position after a brief delay
                if self._saved_position > 0.01:
                    QTimer.singleShot(200, lambda: self._player.set_position(self._saved_position))
                logger.info("Fullscreen playback started")
        
        self._set_state(PlayerViewState.FULLSCREEN)
        logger.info("=== FULLSCREEN TRANSITION COMPLETE ===")
    
    def transition_to_embedded(self) -> bool:
        """
        Transition from fullscreen back to embedded view.
        
        Similar process to fullscreen transition but in reverse.
        """
        if self._state == PlayerViewState.EMBEDDED:
            logger.warning("Already in embedded state")
            return True
        
        if not self._embedded_frame:
            logger.error("Embedded frame not registered")
            return False
        
        logger.info("=== TRANSITION TO EMBEDDED ===")
        self._set_state(PlayerViewState.TRANSITIONING)
        
        # Save current state
        self._was_playing = self.is_playing
        self._saved_position = self._player.get_position() or 0.0
        saved_url = self._current_url
        
        logger.info(f"Saved state: playing={self._was_playing}, pos={self._saved_position}")
        
        # Stop the player completely
        self._player.stop()
        
        # Unregister fullscreen frame
        self.unregister_fullscreen_frame()
        
        # Schedule the reattachment
        QTimer.singleShot(100, lambda: self._complete_embedded_transition(saved_url))
        
        return True
    
    def _complete_embedded_transition(self, url: str):
        """Complete the embedded transition after delay."""
        if not self._embedded_frame:
            logger.error("Embedded frame not available")
            self._set_state(PlayerViewState.IDLE)
            return
        
        logger.info("Completing embedded transition...")
        
        # Attach to embedded frame
        if not self._attach_to_frame(self._embedded_frame):
            logger.error("Failed to attach to embedded frame")
            self._set_state(PlayerViewState.IDLE)
            return
        
        # Create new media and start playback
        if url:
            media = self._vlc_instance.media_new(url)
            self._player.set_media(media)
            
            if self._was_playing:
                self._player.play()
                # Restore position after a brief delay
                if self._saved_position > 0.01:
                    QTimer.singleShot(200, lambda: self._player.set_position(self._saved_position))
                logger.info("Embedded playback started")
        
        self._set_state(PlayerViewState.EMBEDDED)
        logger.info("=== EMBEDDED TRANSITION COMPLETE ===")
    
    # ========================= Cleanup =========================
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up SharedPlayerManager...")
        
        if self._player:
            self._player.stop()
            self._player.release()
            self._player = None
            
        if self._vlc_instance:
            self._vlc_instance.release()
            self._vlc_instance = None
        
        self._embedded_frame = None
        self._fullscreen_frame = None
        self._current_frame = None
        self._current_channel = None
        self._initialized = False
        
        logger.info("SharedPlayerManager cleaned up")


# Convenience function
def get_shared_player() -> SharedPlayerManager:
    """Get the shared player manager instance."""
    return SharedPlayerManager.get_instance()
