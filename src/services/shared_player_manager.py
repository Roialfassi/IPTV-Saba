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
from typing import Optional, Callable, List, Tuple
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QWidget
import vlc

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import StreamHealthTracker (lazy to avoid circular imports)
_health_tracker = None


def get_health_tracker():
    """Lazy import and get the health tracker instance."""
    global _health_tracker
    if _health_tracker is None:
        from src.services.stream_health_tracker import StreamHealthTracker
        _health_tracker = StreamHealthTracker.get_instance()
    return _health_tracker


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

    # Audio/Subtitle track signals
    audio_tracks_available = pyqtSignal(list)  # List of (id, name) tuples
    subtitles_available = pyqtSignal(list)  # List of (id, name) tuples

    # Retry signals
    retry_started = pyqtSignal(str, int, int)  # channel_name, attempt, max_attempts
    retry_exhausted = pyqtSignal(str)  # channel_name - all retries failed

    # Quality selection signals
    quality_variants_available = pyqtSignal(list)  # List of QualityVariant objects
    
    # Connection timeout in seconds
    CONNECTION_TIMEOUT = 15

    # Retry configuration
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAYS = [2000, 4000, 8000]  # Exponential backoff in ms
    
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

        # Retry state
        self._retry_timer: Optional[QTimer] = None
        self._retry_count: int = 0
        self._retry_enabled: bool = True

        # Quality selection state
        self._quality_variants: list = []
        self._current_quality_index: int = 0  # 0 = Auto (original URL)
        self._original_url: Optional[str] = None

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
        self._cancel_retry()  # Success - cancel any pending retries
        self._retry_count = 0  # Reset retry count

        # Record success in health tracker
        if self._current_channel:
            get_health_tracker().record_success(self._current_channel.name)

        # Emit available audio and subtitle tracks after a short delay
        # (allow media to be fully parsed)
        QTimer.singleShot(500, self._emit_audio_tracks)
        QTimer.singleShot(500, self._emit_subtitle_tracks)

        # Fetch quality variants for HLS streams
        QTimer.singleShot(1000, self._fetch_quality_variants)
    
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

        # Record failure in health tracker
        if self._current_channel:
            get_health_tracker().record_failure(channel_name)

        # Attempt retry if enabled and not exhausted
        if self._retry_enabled and self._retry_count < self.MAX_RETRY_ATTEMPTS:
            self._schedule_retry()
        else:
            # No more retries - emit error
            if self._retry_count >= self.MAX_RETRY_ATTEMPTS:
                self.retry_exhausted.emit(channel_name)
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

            # Record failure in health tracker
            if self._current_channel:
                get_health_tracker().record_failure(channel_name)

            # Stop the player after timeout
            try:
                self._player.stop()
            except Exception:
                pass

            # Attempt retry if enabled and not exhausted
            if self._retry_enabled and self._retry_count < self.MAX_RETRY_ATTEMPTS:
                self._schedule_retry()
            else:
                # No more retries - emit timeout
                if self._retry_count >= self.MAX_RETRY_ATTEMPTS:
                    self.retry_exhausted.emit(channel_name)
                timeout_msg = f"Connection timeout for '{channel_name}'. The stream may be offline or your connection is slow."
                self.connection_timeout.emit(timeout_msg)

    # ========================= Retry Logic =========================

    def _schedule_retry(self):
        """Schedule a retry attempt with exponential backoff."""
        if not self._current_channel or not self._current_url:
            logger.warning("Cannot retry - no channel/URL saved")
            return

        delay = self.RETRY_DELAYS[min(self._retry_count, len(self.RETRY_DELAYS) - 1)]
        self._retry_count += 1

        channel_name = self._current_channel.name
        logger.info(f"Scheduling retry {self._retry_count}/{self.MAX_RETRY_ATTEMPTS} for '{channel_name}' in {delay}ms")

        # Emit retry started signal
        self.retry_started.emit(channel_name, self._retry_count, self.MAX_RETRY_ATTEMPTS)

        # Schedule retry
        self._cancel_retry()
        self._retry_timer = QTimer()
        self._retry_timer.setSingleShot(True)
        self._retry_timer.timeout.connect(self._execute_retry)
        self._retry_timer.start(delay)

    def _execute_retry(self):
        """Execute the retry attempt."""
        if not self._current_channel or not self._current_url:
            logger.warning("Cannot execute retry - no channel/URL")
            return

        logger.info(f"Executing retry {self._retry_count}/{self.MAX_RETRY_ATTEMPTS}")

        try:
            # Stop current playback
            self._player.stop()

            # Re-create media and play
            media = self._vlc_instance.media_new(self._current_url)
            if media:
                self._player.set_media(media)
                self._player.play()
                logger.info("Retry playback started")
            else:
                logger.error("Failed to create media for retry")
        except Exception as e:
            logger.error(f"Error during retry: {e}")

    def _cancel_retry(self):
        """Cancel any pending retry timer."""
        if self._retry_timer:
            self._retry_timer.stop()
            self._retry_timer = None

    def cancel_retry(self):
        """
        Public method to cancel retry sequence.

        Call this when user manually stops playback or switches channels.
        """
        self._cancel_retry()
        self._retry_count = 0
        logger.info("Retry sequence cancelled")

    def set_retry_enabled(self, enabled: bool):
        """Enable or disable automatic retry on stream errors."""
        self._retry_enabled = enabled
        logger.info(f"Retry enabled: {enabled}")

    @property
    def is_retrying(self) -> bool:
        """Check if a retry is currently scheduled."""
        return self._retry_timer is not None and self._retry_timer.isActive()

    @property
    def retry_count(self) -> int:
        """Get the current retry attempt count."""
        return self._retry_count

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

        # Cancel any pending retry from previous channel
        self._cancel_retry()
        self._retry_count = 0

        # Reset quality variants for new channel
        self._quality_variants = []
        self._current_quality_index = 0
        self._original_url = None

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

        Uses pause-first approach to avoid VLC threading crashes on Windows.
        On Windows, we avoid calling stop() entirely since it can crash.
        """
        logger.info("Stopping playback")
        self._cancel_connection_timer()
        self._cancel_retry()
        self._is_connecting = False

        try:
            if self._player:
                is_playing = self._player.is_playing()
                if is_playing:
                    # Pause first to avoid VLC crashes
                    self._player.set_pause(1)

                # On Windows, avoid calling stop() as it can crash VLC
                # Instead, just set media to None which effectively stops playback
                if sys.platform == "win32":
                    try:
                        self._player.set_media(None)
                    except Exception:
                        pass
                elif self._state != PlayerViewState.TRANSITIONING:
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
    
    # ========================= Audio Track Selection =========================

    def get_audio_tracks(self) -> List[Tuple[int, str]]:
        """
        Get available audio tracks from the current media.

        Returns:
            List of tuples (track_id, track_name) for available audio tracks.
        """
        tracks = []
        if not self._player:
            return tracks

        try:
            track_description = self._player.audio_get_track_description()
            if track_description:
                for track in track_description:
                    # track is a tuple of (id, name_bytes)
                    track_id = track[0]
                    track_name = track[1].decode('utf-8') if isinstance(track[1], bytes) else str(track[1])
                    # Skip the "Disabled" track (usually id -1)
                    if track_id != -1:
                        tracks.append((track_id, track_name))
            logger.debug(f"Found {len(tracks)} audio tracks")
        except Exception as e:
            logger.error(f"Error getting audio tracks: {e}")

        return tracks

    def set_audio_track(self, track_id: int) -> bool:
        """
        Set the active audio track.

        Args:
            track_id: The ID of the audio track to activate.

        Returns:
            True if successful, False otherwise.
        """
        if not self._player:
            return False

        try:
            result = self._player.audio_set_track(track_id)
            if result == 0:
                logger.info(f"Audio track set to {track_id}")
                return True
            else:
                logger.warning(f"Failed to set audio track to {track_id}")
                return False
        except Exception as e:
            logger.error(f"Error setting audio track: {e}")
            return False

    def get_current_audio_track(self) -> int:
        """Get the currently active audio track ID."""
        if not self._player:
            return -1
        try:
            return self._player.audio_get_track()
        except Exception:
            return -1

    def _emit_audio_tracks(self):
        """Emit available audio tracks after a delay (for media to be parsed)."""
        tracks = self.get_audio_tracks()
        if tracks:
            self.audio_tracks_available.emit(tracks)

    # ========================= Subtitle Support =========================

    def get_subtitle_tracks(self) -> List[Tuple[int, str]]:
        """
        Get available subtitle tracks from the current media.

        Returns:
            List of tuples (track_id, track_name) for available subtitle tracks.
            Includes "Disabled" option as first entry with id -1.
        """
        tracks = [(-1, "Disabled")]  # Always include disabled option
        if not self._player:
            return tracks

        try:
            track_description = self._player.video_get_spu_description()
            if track_description:
                for track in track_description:
                    track_id = track[0]
                    track_name = track[1].decode('utf-8') if isinstance(track[1], bytes) else str(track[1])
                    # Skip the "Disabled" track if already present (usually id -1)
                    if track_id != -1:
                        tracks.append((track_id, track_name))
            logger.debug(f"Found {len(tracks) - 1} subtitle tracks")
        except Exception as e:
            logger.error(f"Error getting subtitle tracks: {e}")

        return tracks

    def set_subtitle_track(self, track_id: int) -> bool:
        """
        Set the active subtitle track.

        Args:
            track_id: The ID of the subtitle track to activate (-1 to disable).

        Returns:
            True if successful, False otherwise.
        """
        if not self._player:
            return False

        try:
            result = self._player.video_set_spu(track_id)
            if result == 0:
                logger.info(f"Subtitle track set to {track_id}")
                return True
            else:
                logger.warning(f"Failed to set subtitle track to {track_id}")
                return False
        except Exception as e:
            logger.error(f"Error setting subtitle track: {e}")
            return False

    def get_current_subtitle_track(self) -> int:
        """Get the currently active subtitle track ID."""
        if not self._player:
            return -1
        try:
            return self._player.video_get_spu()
        except Exception:
            return -1

    def load_external_subtitle(self, subtitle_path: str) -> bool:
        """
        Load an external subtitle file.

        Args:
            subtitle_path: Path to the subtitle file (.srt, .sub, .ass, etc.)

        Returns:
            True if successful, False otherwise.
        """
        if not self._player:
            return False

        try:
            result = self._player.video_set_subtitle_file(subtitle_path)
            if result:
                logger.info(f"External subtitle loaded: {subtitle_path}")
                # Emit updated subtitle tracks
                QTimer.singleShot(500, self._emit_subtitle_tracks)
                return True
            else:
                logger.warning(f"Failed to load subtitle file: {subtitle_path}")
                return False
        except Exception as e:
            logger.error(f"Error loading subtitle file: {e}")
            return False

    def _emit_subtitle_tracks(self):
        """Emit available subtitle tracks after a delay (for media to be parsed)."""
        tracks = self.get_subtitle_tracks()
        if tracks:
            self.subtitles_available.emit(tracks)

    # ========================= Quality Selection =========================

    def _fetch_quality_variants(self):
        """
        Fetch quality variants for the current stream if it's HLS.

        This runs in the main thread after playback starts. For production,
        consider moving to a background thread.
        """
        if not self._current_url:
            return

        from src.services.hls_parser import get_hls_parser, HLSParser

        parser = get_hls_parser()

        if not parser.is_hls_url(self._current_url):
            logger.debug(f"Not an HLS stream: {self._current_url}")
            return

        try:
            variants = parser.parse_master_playlist(self._current_url)
            if variants:
                self._quality_variants = variants
                self._original_url = self._current_url
                logger.info(f"Found {len(variants)} quality variants")
                self.quality_variants_available.emit(variants)
            else:
                logger.debug("No quality variants found in HLS stream")
        except Exception as e:
            logger.error(f"Error fetching quality variants: {e}")

    def get_quality_variants(self) -> list:
        """
        Get the available quality variants for the current stream.

        Returns:
            List of QualityVariant objects, or empty list if not available.
        """
        return self._quality_variants

    def set_quality(self, variant_index: int) -> bool:
        """
        Switch to a different quality variant.

        Args:
            variant_index: Index into the quality_variants list.
                          -1 or 0 means "Auto" (use original URL).

        Returns:
            True if the quality switch was initiated, False otherwise.
        """
        if variant_index <= 0:
            # Auto quality - use original URL
            if self._original_url and self._original_url != self._current_url:
                logger.info("Switching to Auto quality (original URL)")
                return self._switch_stream_url(self._original_url)
            return True

        if variant_index > len(self._quality_variants):
            logger.warning(f"Invalid quality index: {variant_index}")
            return False

        variant = self._quality_variants[variant_index - 1]  # -1 because 0 is Auto
        logger.info(f"Switching to quality: {variant.display_name}")
        return self._switch_stream_url(variant.url)

    def _switch_stream_url(self, new_url: str) -> bool:
        """
        Switch to a different stream URL while maintaining playback state.

        Args:
            new_url: The new URL to play.

        Returns:
            True if successful, False otherwise.
        """
        if not self._player or not new_url:
            return False

        try:
            # Save current position
            was_playing = self.is_playing
            position = self._player.get_position() or 0.0

            # Stop current playback
            self._player.stop()

            # Create new media and play
            media = self._vlc_instance.media_new(new_url)
            if not media:
                logger.error("Failed to create media for quality switch")
                return False

            self._player.set_media(media)
            self._current_url = new_url

            if was_playing:
                self._player.play()
                # Restore position after brief delay
                if position > 0.01:
                    QTimer.singleShot(500, lambda: self._player.set_position(position))

            return True

        except Exception as e:
            logger.error(f"Error switching stream URL: {e}")
            return False

    @property
    def current_quality_index(self) -> int:
        """Get the current quality variant index (0 = Auto)."""
        return self._current_quality_index

    # ========================= Cleanup =========================

    def cleanup(self):
        """
        Clean up resources safely.

        IMPORTANT: On Windows, VLC has threading issues that can cause crashes
        when calling stop() followed by release(). We use a gentler approach:
        1. Pause first (safe operation)
        2. Detach from window
        3. Set media to None to release internal resources
        4. Only then call release() with proper delays
        """
        logger.info("Cleaning up SharedPlayerManager...")

        # Cancel any pending timers first
        self._cancel_connection_timer()
        self._cancel_retry()

        if self._player:
            try:
                # First, pause if playing (safer than stop on Windows)
                if self._player.is_playing():
                    self._player.set_pause(1)
                    logger.info("Player paused")

                # Detach from window before any cleanup
                try:
                    if sys.platform == "win32":
                        self._player.set_hwnd(None)
                    elif sys.platform.startswith('linux'):
                        self._player.set_xwindow(0)
                    elif sys.platform == "darwin":
                        self._player.set_nsobject(0)
                    logger.info("Player detached from window")
                except Exception as e:
                    logger.warning(f"Could not detach player from window: {e}")

                # Set media to None to help release internal resources
                try:
                    self._player.set_media(None)
                except Exception:
                    pass

                # On Windows, we skip stop() as it can crash
                # The release() will handle cleanup
                if sys.platform != "win32":
                    try:
                        self._player.stop()
                    except Exception as e:
                        logger.warning(f"Error stopping player: {e}")

                # Release the player
                try:
                    self._player.release()
                    logger.info("Player released")
                except Exception as e:
                    logger.error(f"Error releasing player: {e}")
            except Exception as e:
                logger.error(f"Error during player cleanup: {e}")
            finally:
                self._player = None

        if self._vlc_instance:
            try:
                self._vlc_instance.release()
                logger.info("VLC instance released")
            except Exception as e:
                logger.error(f"Error releasing VLC instance: {e}")
            finally:
                self._vlc_instance = None

        self._embedded_frame = None
        self._fullscreen_frame = None
        self._current_frame = None
        self._current_channel = None
        self._current_url = None
        self._initialized = False

        logger.info("SharedPlayerManager cleaned up")


# Convenience function
def get_shared_player() -> SharedPlayerManager:
    """Get the shared player manager instance."""
    return SharedPlayerManager.get_instance()
