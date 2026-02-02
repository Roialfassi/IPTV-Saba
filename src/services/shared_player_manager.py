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
    stream_error = pyqtSignal(str)  # Emitted on VLC stream errors
    connection_timeout = pyqtSignal(str)  # Emitted when stream fails to connect
    buffering = pyqtSignal(int)  # Emitted during buffering with percentage
    
    # Connection timeout in seconds
    CONNECTION_TIMEOUT = 15
    
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
        
        # Connection timeout tracking
        self._connection_timer: Optional[QTimer] = None
        self._is_connecting: bool = False
        
        # Setup VLC event callbacks
        self._setup_vlc_events()
        
        self._initialized = True
        logger.info("SharedPlayerManager initialized with state machine and event callbacks")
    
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
    
    # ========================= VLC Event Callbacks =========================
    
    def _setup_vlc_events(self):
        """
        Setup VLC event callbacks for error handling and state monitoring.
        
        These callbacks help detect:
        - Stream errors (network issues, invalid streams)
        - Buffering status
        - Playback state changes
        """
        event_manager = self._player.event_manager()
        
        # Playback events
        event_manager.event_attach(vlc.EventType.MediaPlayerPlaying, self._on_playing)
        event_manager.event_attach(vlc.EventType.MediaPlayerPaused, self._on_paused)
        event_manager.event_attach(vlc.EventType.MediaPlayerStopped, self._on_stopped)
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)
        
        # Error events
        event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_error)
        
        # Buffering events
        event_manager.event_attach(vlc.EventType.MediaPlayerBuffering, self._on_buffering)
        
        # Opening event (for connection tracking)
        event_manager.event_attach(vlc.EventType.MediaPlayerOpening, self._on_opening)
        
        logger.info("VLC event callbacks registered")
    
    def _on_playing(self, event):
        """Called when playback starts."""
        logger.info("VLC Event: Playing")
        self._is_connecting = False
        self._cancel_connection_timer()
    
    def _on_paused(self, event):
        """Called when playback is paused."""
        logger.debug("VLC Event: Paused")
    
    def _on_stopped(self, event):
        """Called when playback is stopped."""
        logger.debug("VLC Event: Stopped")
        self._is_connecting = False
        self._cancel_connection_timer()
    
    def _on_end_reached(self, event):
        """Called when stream ends."""
        logger.info("VLC Event: End reached")
        self._is_connecting = False
        self._cancel_connection_timer()
    
    def _on_error(self, event):
        """Called when VLC encounters an error."""
        logger.error("VLC Event: Error encountered")
        self._is_connecting = False
        self._cancel_connection_timer()
        
        channel_name = self._current_channel.name if self._current_channel else "Unknown"
        error_msg = f"Stream error for '{channel_name}'. The stream may be offline or unavailable."
        self.stream_error.emit(error_msg)
    
    def _on_buffering(self, event):
        """Called during buffering with percentage."""
        # event.u.new_cache is the buffering percentage (0-100)
        try:
            percentage = int(event.u.new_cache)
            if percentage < 100:
                logger.debug(f"VLC Event: Buffering {percentage}%")
            self.buffering.emit(percentage)
        except Exception:
            pass
    
    def _on_opening(self, event):
        """Called when VLC starts opening a stream."""
        logger.info("VLC Event: Opening stream")
        self._is_connecting = True
        self._start_connection_timer()
    
    def _start_connection_timer(self):
        """Start a timer to detect connection timeouts."""
        self._cancel_connection_timer()
        
        self._connection_timer = QTimer()
        self._connection_timer.setSingleShot(True)
        self._connection_timer.timeout.connect(self._on_connection_timeout)
        self._connection_timer.start(self.CONNECTION_TIMEOUT * 1000)
        logger.debug(f"Connection timer started ({self.CONNECTION_TIMEOUT}s)")
    
    def _cancel_connection_timer(self):
        """Cancel the connection timeout timer."""
        if self._connection_timer:
            self._connection_timer.stop()
            self._connection_timer = None
    
    def _on_connection_timeout(self):
        """Called when connection times out."""
        if self._is_connecting:
            logger.warning("Connection timeout - stream failed to connect")
            self._is_connecting = False
            
            channel_name = self._current_channel.name if self._current_channel else "Unknown"
            timeout_msg = f"Connection timeout for '{channel_name}'. The stream may be offline or your connection is slow."
            self.connection_timeout.emit(timeout_msg)
            
            # Stop the player after timeout
            try:
                self._player.stop()
            except Exception:
                pass
    
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
        """
        Stop playback safely.
        
        Uses pause-first approach to avoid VLC threading crashes.
        """
        logger.info("Stopping playback")
        self._cancel_connection_timer()
        self._is_connecting = False
        
        try:
            if self._player and self._player.is_playing():
                # Pause first to avoid VLC crashes
                self._player.set_pause(1)
            
            # Small delay then stop (if not transitioning)
            if self._state != PlayerViewState.TRANSITIONING:
                if self._player:
                    self._player.stop()
        except Exception as e:
            logger.error(f"Error stopping player: {e}")
        
        self._set_state(PlayerViewState.IDLE)
        self.playback_stopped.emit()
    
    def safe_stop_for_cleanup(self):
        """
        Safely prepare the player for logout/cleanup scenarios.
        
        IMPORTANT: We do NOT call player.stop() here because it crashes VLC on Windows
        due to internal threading conflicts. Instead we:
        1. Pause the player (safe operation)
        2. Reset our state tracking
        
        The player will be properly cleaned up when the app closes via aboutToQuit signal.
        """
        logger.info("Performing safe stop for cleanup")
        
        if not self._player:
            logger.info("No player to stop")
            self._set_state(PlayerViewState.IDLE)
            return
        
        try:
            # Check if actually playing
            is_playing = self._player.is_playing()
            logger.info(f"Player is_playing: {is_playing}")
            
            if is_playing:
                # Just pause - don't stop! stop() crashes VLC on Windows
                logger.info("Pausing player (not stopping - stops crash VLC)...")
                self._player.set_pause(1)
                logger.info("Player paused successfully")
            
            # We deliberately do NOT call stop() here - it crashes!
            # The player will be cleaned up when the app closes.
            
        except Exception as e:
            logger.error(f"Error during safe stop: {e}")
        
        # Reset frame references and channel tracking
        self._current_frame = None
        self._current_channel = None
        self._current_url = None
        
        logger.info("Safe stop completed (player paused, not stopped)")
        
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
            try:
                # Stop playback first
                self._player.stop()
                
                # Detach from window before releasing to prevent crashes
                try:
                    if sys.platform == "win32":
                        self._player.set_hwnd(None)
                    elif sys.platform.startswith('linux'):
                        self._player.set_xwindow(0)
                    elif sys.platform == "darwin":
                        self._player.set_nsobject(0)
                except Exception as e:
                    logger.warning(f"Could not detach player from window: {e}")
                
                # Now release the player
                self._player.release()
            except Exception as e:
                logger.error(f"Error during player cleanup: {e}")
            finally:
                self._player = None
            
        if self._vlc_instance:
            try:
                self._vlc_instance.release()
            except Exception as e:
                logger.error(f"Error releasing VLC instance: {e}")
            finally:
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
