#!/usr/bin/env python3
"""
Download and Record Manager for IPTV-Saba

Handles:
- Downloading media files (.mp4, .mkv, .avi, etc.) with speed/ETA tracking
- Recording live streams with VLC health monitoring
- Concurrent download limit with queuing
- Pause/resume downloads with HTTP Range support
- Automatic retry with exponential backoff
- Progress tracking and completed items history
- Thread-safe access to all shared state
"""

import os
import sys
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

import requests
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import vlc

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# ========================== Data Classes ==========================

class DownloadState(Enum):
    """State of a download or recording."""
    ACTIVE = "active"
    PAUSED = "paused"
    QUEUED = "queued"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadInfo:
    """Tracks state for an active or queued download."""
    download_id: str
    channel_name: str
    url: str
    filepath: str
    state: DownloadState = DownloadState.ACTIVE
    bytes_downloaded: int = 0
    total_bytes: int = 0
    speed_bps: float = 0.0
    eta_seconds: float = 0.0
    thread: Optional[threading.Thread] = field(default=None, repr=False)
    retry_count: int = 0
    error_message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    _last_speed_time: float = 0.0
    _last_speed_bytes: int = 0


@dataclass
class RecordingInfo:
    """Tracks state for an active recording."""
    recording_id: str
    channel_name: str
    url: str
    filepath: str
    player: Any = field(default=None, repr=False)
    instance: Any = field(default=None, repr=False)
    start_time: Optional[datetime] = None
    error_message: str = ""
    health_check_timer: Optional[QTimer] = field(default=None, repr=False)


# ========================== Manager ==========================

class DownloadRecordManager(QObject):
    """
    Manager for downloading media files and recording live streams.

    Thread-safe with RLock protecting all shared state.
    Supports concurrent download limit, queuing, pause/resume, retry,
    speed/ETA tracking, and VLC recording health monitoring.
    """

    # --- Original signals (preserved for backward compatibility) ---
    download_progress = pyqtSignal(str, int, int)    # (id, bytes_downloaded, total_bytes)
    download_complete = pyqtSignal(str, str)          # (id, file_path)
    download_error = pyqtSignal(str, str)             # (id, error_message)
    recording_started = pyqtSignal(str)               # (id)
    recording_stopped = pyqtSignal(str, str)          # (id, file_path)

    # --- New signals ---
    download_speed = pyqtSignal(str, float, float)    # (id, speed_mbps, eta_seconds)
    recording_elapsed = pyqtSignal(str, int)          # (id, elapsed_seconds)
    recording_error = pyqtSignal(str, str)            # (id, error_message)
    download_paused = pyqtSignal(str)                 # (id)
    download_resumed = pyqtSignal(str)                # (id)
    download_queued = pyqtSignal(str, str, int)       # (id, channel_name, queue_position)

    # Constants
    MEDIA_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg', '.ts'}
    MAX_CONCURRENT_DOWNLOADS = 3
    MAX_RETRY_ATTEMPTS = 3
    RETRY_DELAYS = [2, 4, 8]  # seconds
    COMPLETED_ITEMS_CAP = 50
    RECORDING_HEALTH_CHECK_INTERVAL_MS = 10000  # 10 seconds
    RECORDING_ELAPSED_INTERVAL_MS = 1000  # 1 second

    def __init__(self, downloads_dir: str = "downloads"):
        super().__init__()
        self.downloads_dir = downloads_dir
        self._lock = threading.RLock()

        # Core state (all access must be under self._lock)
        self._downloads: Dict[str, DownloadInfo] = {}
        self._recordings: Dict[str, RecordingInfo] = {}
        self._download_queue: deque = deque()  # deque of DownloadInfo
        self._completed_items: List[dict] = []
        self._cancelled_downloads: set = set()

        # Elapsed time timer for recordings
        self._elapsed_timer = QTimer(self)
        self._elapsed_timer.timeout.connect(self._emit_recording_elapsed)
        self._elapsed_timer.start(self.RECORDING_ELAPSED_INTERVAL_MS)

        # Create downloads directory
        os.makedirs(self.downloads_dir, exist_ok=True)
        logger.info(f"Download directory: {os.path.abspath(self.downloads_dir)}")

    # ========================== Backward-compat properties ==========================

    @property
    def active_downloads(self) -> dict:
        """Legacy dict: {id: thread}. Use get_all_download_info() for full data."""
        with self._lock:
            return {did: info.thread for did, info in self._downloads.items()
                    if info.state in (DownloadState.ACTIVE, DownloadState.PAUSED)}

    @property
    def active_recordings(self) -> dict:
        """Legacy dict: {id: {player, instance, filepath, start_time}}."""
        with self._lock:
            result = {}
            for rid, info in self._recordings.items():
                result[rid] = {
                    'player': info.player,
                    'instance': info.instance,
                    'filepath': info.filepath,
                    'start_time': info.start_time,
                }
            return result

    @property
    def cancelled_downloads(self) -> set:
        """Legacy set access."""
        with self._lock:
            return set(self._cancelled_downloads)

    # ========================== URL / Filename helpers ==========================

    def is_media_file(self, url: str) -> bool:
        """
        Check if URL points to a downloadable media file.

        Uses proper URL parsing instead of substring matching.

        Args:
            url: The stream URL

        Returns:
            True if it's a media file, False if it's a livestream
        """
        try:
            parsed = urlparse(url)
            path = parsed.path
            _, ext = os.path.splitext(path)
            return ext.lower() in self.MEDIA_EXTENSIONS
        except Exception:
            return False

    def generate_filename(self, channel_name: str, url: str, is_recording: bool = False) -> str:
        """
        Generate a safe filename for download/recording.

        Args:
            channel_name: Name of the channel
            url: The stream URL
            is_recording: True if recording a livestream

        Returns:
            Generated filename
        """
        safe_name = "".join(c for c in channel_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')

        extension = '.mp4'  # default
        if not is_recording:
            try:
                parsed = urlparse(url)
                _, ext = os.path.splitext(parsed.path)
                if ext.lower() in self.MEDIA_EXTENSIONS:
                    extension = ext.lower()
            except Exception:
                pass

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if is_recording:
            return f"{safe_name}_recording_{timestamp}{extension}"
        else:
            return f"{safe_name}_download_{timestamp}{extension}"

    # ========================== Download operations ==========================

    def start_download(self, download_id: str, channel_name: str, url: str) -> bool:
        """
        Start downloading a media file. Queues if at concurrent limit.

        Args:
            download_id: Unique identifier for this download
            channel_name: Name of the channel
            url: URL to download from

        Returns:
            True if download started or queued successfully
        """
        with self._lock:
            if download_id in self._downloads:
                logger.warning(f"Download {download_id} is already active")
                return False
            # Also check queue
            for queued in self._download_queue:
                if queued.download_id == download_id:
                    logger.warning(f"Download {download_id} is already queued")
                    return False

        filename = self.generate_filename(channel_name, url, is_recording=False)
        filepath = os.path.join(self.downloads_dir, filename)

        info = DownloadInfo(
            download_id=download_id,
            channel_name=channel_name,
            url=url,
            filepath=filepath,
            started_at=datetime.now(),
        )

        with self._lock:
            active_count = sum(
                1 for d in self._downloads.values()
                if d.state == DownloadState.ACTIVE
            )

            if active_count >= self.MAX_CONCURRENT_DOWNLOADS:
                # Queue it
                info.state = DownloadState.QUEUED
                self._download_queue.append(info)
                position = len(self._download_queue)
                logger.info(f"Download {download_id} queued (position {position})")
                self.download_queued.emit(download_id, channel_name, position)
                return True

            # Start immediately
            info.state = DownloadState.ACTIVE
            download_thread = threading.Thread(
                target=self._download_worker,
                args=(info,),
                daemon=True
            )
            info.thread = download_thread
            self._downloads[download_id] = info

        download_thread.start()
        logger.info(f"Started download {download_id}: {channel_name} -> {filepath}")
        return True

    def _download_worker(self, info: DownloadInfo):
        """
        Worker thread for downloading a file with retry and speed tracking.

        Args:
            info: DownloadInfo for this download
        """
        download_id = info.download_id

        for attempt in range(self.MAX_RETRY_ATTEMPTS):
            if attempt > 0:
                delay = self.RETRY_DELAYS[min(attempt - 1, len(self.RETRY_DELAYS) - 1)]
                logger.info(f"Download {download_id} retry {attempt + 1}/{self.MAX_RETRY_ATTEMPTS} after {delay}s")
                time.sleep(delay)
                with self._lock:
                    info.retry_count = attempt

            try:
                headers = {}
                resume_offset = 0

                # Support HTTP Range resume on retry
                if attempt > 0 and info.bytes_downloaded > 0 and os.path.exists(info.filepath):
                    resume_offset = info.bytes_downloaded
                    headers['Range'] = f'bytes={resume_offset}-'
                    logger.info(f"Resuming download from byte {resume_offset}")

                response = requests.get(info.url, stream=True, timeout=30, headers=headers)

                # If server doesn't support Range, restart from scratch
                if attempt > 0 and resume_offset > 0 and response.status_code == 200:
                    resume_offset = 0
                    info.bytes_downloaded = 0

                response.raise_for_status()

                content_length = response.headers.get('content-length')
                if content_length:
                    if response.status_code == 206:
                        # Partial content - total is offset + remaining
                        info.total_bytes = resume_offset + int(content_length)
                    else:
                        info.total_bytes = int(content_length)

                chunk_size = 65536  # 64KB
                file_mode = 'ab' if resume_offset > 0 and response.status_code == 206 else 'wb'
                if file_mode == 'wb':
                    info.bytes_downloaded = 0

                info._last_speed_time = time.monotonic()
                info._last_speed_bytes = info.bytes_downloaded

                with open(info.filepath, file_mode) as f:
                    for chunk in response.iter_content(chunk_size):
                        # Check cancelled
                        with self._lock:
                            if download_id in self._cancelled_downloads:
                                self._cancelled_downloads.discard(download_id)
                                info.state = DownloadState.CANCELLED
                                logger.info(f"Download {download_id} cancelled")
                                self._cleanup_partial_file(info.filepath)
                                self._finalize_download(info)
                                return

                        # Check paused - wait loop
                        while True:
                            with self._lock:
                                if info.state != DownloadState.PAUSED:
                                    break
                            time.sleep(0.5)

                        if chunk:
                            f.write(chunk)
                            info.bytes_downloaded += len(chunk)

                            # Speed/ETA calculation (every ~1s worth of data)
                            now = time.monotonic()
                            elapsed = now - info._last_speed_time
                            if elapsed >= 1.0:
                                bytes_delta = info.bytes_downloaded - info._last_speed_bytes
                                info.speed_bps = bytes_delta / elapsed
                                if info.speed_bps > 0 and info.total_bytes > 0:
                                    remaining = info.total_bytes - info.bytes_downloaded
                                    info.eta_seconds = remaining / info.speed_bps
                                else:
                                    info.eta_seconds = 0.0
                                info._last_speed_time = now
                                info._last_speed_bytes = info.bytes_downloaded

                                speed_mbps = info.speed_bps / (1024 * 1024)
                                self.download_speed.emit(download_id, speed_mbps, info.eta_seconds)

                            self.download_progress.emit(download_id, info.bytes_downloaded, info.total_bytes)

                # Download complete
                info.state = DownloadState.COMPLETED
                info.completed_at = datetime.now()
                logger.info(f"Download complete: {info.filepath}")
                self.download_complete.emit(download_id, info.filepath)
                self._finalize_download(info)
                return

            except Exception as e:
                error_msg = f"Download error (attempt {attempt + 1}): {str(e)}"
                logger.error(error_msg)
                info.error_message = str(e)

                if attempt == self.MAX_RETRY_ATTEMPTS - 1:
                    # Final attempt failed
                    info.state = DownloadState.FAILED
                    info.completed_at = datetime.now()
                    self.download_error.emit(download_id, f"Download failed after {self.MAX_RETRY_ATTEMPTS} attempts: {str(e)}")
                    self._cleanup_partial_file(info.filepath)
                    self._finalize_download(info)
                    return

    def _finalize_download(self, info: DownloadInfo):
        """Remove download from active set, add to completed, process queue."""
        with self._lock:
            self._downloads.pop(info.download_id, None)
            self._add_completed_item(
                item_id=info.download_id,
                channel_name=info.channel_name,
                filepath=info.filepath,
                item_type="download",
                state=info.state.value,
                bytes_total=info.total_bytes,
                error_message=info.error_message,
                started_at=info.started_at,
                completed_at=info.completed_at or datetime.now(),
            )
        self._process_download_queue()

    def _process_download_queue(self):
        """Start queued downloads if slots are available."""
        with self._lock:
            while self._download_queue:
                active_count = sum(
                    1 for d in self._downloads.values()
                    if d.state == DownloadState.ACTIVE
                )
                if active_count >= self.MAX_CONCURRENT_DOWNLOADS:
                    break

                info = self._download_queue.popleft()
                info.state = DownloadState.ACTIVE
                info.started_at = datetime.now()
                download_thread = threading.Thread(
                    target=self._download_worker,
                    args=(info,),
                    daemon=True
                )
                info.thread = download_thread
                self._downloads[info.download_id] = info
                download_thread.start()
                logger.info(f"Dequeued and started download: {info.download_id}")

    def _cleanup_partial_file(self, filepath: str):
        """Safely remove a partial download file."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except OSError as e:
            logger.warning(f"Could not remove partial file {filepath}: {e}")

    # ========================== Pause / Resume ==========================

    def pause_download(self, download_id: str) -> bool:
        """
        Pause an active download.

        Args:
            download_id: ID of the download to pause

        Returns:
            True if paused successfully
        """
        with self._lock:
            info = self._downloads.get(download_id)
            if not info or info.state != DownloadState.ACTIVE:
                return False
            info.state = DownloadState.PAUSED

        self.download_paused.emit(download_id)
        logger.info(f"Download paused: {download_id}")
        return True

    def resume_download(self, download_id: str) -> bool:
        """
        Resume a paused download.

        Args:
            download_id: ID of the download to resume

        Returns:
            True if resumed successfully
        """
        with self._lock:
            info = self._downloads.get(download_id)
            if not info or info.state != DownloadState.PAUSED:
                return False
            info.state = DownloadState.ACTIVE

        self.download_resumed.emit(download_id)
        logger.info(f"Download resumed: {download_id}")
        return True

    # ========================== Cancel ==========================

    def cancel_download(self, download_id: str) -> bool:
        """
        Cancel an active or queued download.

        Args:
            download_id: Unique identifier for the download

        Returns:
            True if download was cancelled
        """
        with self._lock:
            # Check if it's in the queue
            for i, queued in enumerate(self._download_queue):
                if queued.download_id == download_id:
                    self._download_queue.remove(queued)
                    logger.info(f"Removed queued download: {download_id}")
                    return True

            # Check active downloads
            if download_id not in self._downloads:
                logger.warning(f"Download {download_id} not found")
                return False
            self._cancelled_downloads.add(download_id)

        logger.info(f"Cancelling download {download_id}")
        return True

    # ========================== Recording operations ==========================

    def start_recording(self, recording_id: str, channel_name: str, url: str) -> bool:
        """
        Start recording a livestream.

        Args:
            recording_id: Unique identifier for this recording
            channel_name: Name of the channel
            url: Stream URL to record

        Returns:
            True if recording started successfully
        """
        with self._lock:
            if recording_id in self._recordings:
                logger.warning(f"Recording {recording_id} is already active")
                return False

        filename = self.generate_filename(channel_name, url, is_recording=True)
        filepath = os.path.join(self.downloads_dir, filename)

        try:
            vlc_instance = vlc.Instance('--sout-file-overwrite')
            player = vlc_instance.media_player_new()

            sout_options = f":sout=#duplicate{{dst=file{{dst={filepath}}}}}"
            media = vlc_instance.media_new(url, sout_options)
            player.set_media(media)
            player.play()

            info = RecordingInfo(
                recording_id=recording_id,
                channel_name=channel_name,
                url=url,
                filepath=filepath,
                player=player,
                instance=vlc_instance,
                start_time=datetime.now(),
            )

            # Set up VLC event callbacks for health monitoring
            event_manager = player.event_manager()
            event_manager.event_attach(
                vlc.EventType.MediaPlayerEncounteredError,
                lambda event, rid=recording_id: self._on_vlc_recording_error(rid)
            )
            event_manager.event_attach(
                vlc.EventType.MediaPlayerEndReached,
                lambda event, rid=recording_id: self._on_vlc_recording_ended(rid)
            )

            # Set up periodic health check timer
            health_timer = QTimer()
            health_timer.timeout.connect(lambda rid=recording_id: self._check_recording_health(rid))
            health_timer.start(self.RECORDING_HEALTH_CHECK_INTERVAL_MS)
            info.health_check_timer = health_timer

            with self._lock:
                self._recordings[recording_id] = info

            logger.info(f"Started recording {recording_id}: {channel_name} -> {filepath}")
            self.recording_started.emit(recording_id)
            return True

        except Exception as e:
            error_msg = f"Recording error: {str(e)}"
            logger.error(error_msg)
            # Emit both signals for backward compat
            self.recording_error.emit(recording_id, error_msg)
            self.download_error.emit(recording_id, error_msg)
            return False

    def _on_vlc_recording_error(self, recording_id: str):
        """Handle VLC error event for a recording."""
        logger.error(f"VLC error for recording {recording_id}")
        with self._lock:
            info = self._recordings.get(recording_id)
            if info:
                info.error_message = "VLC encountered an error during recording"
        self.recording_error.emit(recording_id, "VLC encountered an error during recording")
        self.download_error.emit(recording_id, "VLC encountered an error during recording")

    def _on_vlc_recording_ended(self, recording_id: str):
        """Handle VLC end-reached event for a recording."""
        logger.warning(f"VLC stream ended for recording {recording_id}")
        with self._lock:
            info = self._recordings.get(recording_id)
            if info:
                info.error_message = "Stream ended unexpectedly"
        self.recording_error.emit(recording_id, "Stream ended unexpectedly")
        self.download_error.emit(recording_id, "Stream ended unexpectedly")

    def _check_recording_health(self, recording_id: str):
        """Periodic health check for an active recording."""
        with self._lock:
            info = self._recordings.get(recording_id)
            if not info or not info.player:
                return

        try:
            state = info.player.get_state()
            if state in (vlc.State.Error, vlc.State.Stopped, vlc.State.Ended):
                error_msg = f"Recording unhealthy: VLC state is {state}"
                logger.error(f"{error_msg} for {recording_id}")
                self.recording_error.emit(recording_id, error_msg)
                self.download_error.emit(recording_id, error_msg)
        except Exception as e:
            logger.warning(f"Health check error for {recording_id}: {e}")

    def _emit_recording_elapsed(self):
        """Emit elapsed time for all active recordings."""
        with self._lock:
            recordings_copy = list(self._recordings.items())

        for recording_id, info in recordings_copy:
            if info.start_time:
                elapsed = int((datetime.now() - info.start_time).total_seconds())
                self.recording_elapsed.emit(recording_id, elapsed)

    def stop_recording(self, recording_id: str, blocking: bool = False) -> bool:
        """
        Stop an active recording.

        Args:
            recording_id: Unique identifier for the recording
            blocking: If True, waits synchronously for finalization

        Returns:
            True if recording was stopped successfully
        """
        with self._lock:
            info = self._recordings.pop(recording_id, None)
            if not info:
                logger.warning(f"Recording {recording_id} is not active")
                return False

        # Stop health check timer first
        if info.health_check_timer:
            info.health_check_timer.stop()
            info.health_check_timer = None

        try:
            player = info.player
            vlc_instance = info.instance
            filepath = info.filepath

            # Windows-safe stop: pause first, then clear media
            if sys.platform == "win32":
                player.set_pause(1)
                player.set_media(None)
            else:
                player.stop()

            def finalize_recording():
                try:
                    if sys.platform == "win32":
                        player.set_hwnd(None)
                    player.release()
                    if vlc_instance:
                        vlc_instance.release()
                    logger.info(f"Stopped recording {recording_id}: {filepath}")
                    self.recording_stopped.emit(recording_id, filepath)

                    # Add to completed
                    with self._lock:
                        self._add_completed_item(
                            item_id=recording_id,
                            channel_name=info.channel_name,
                            filepath=filepath,
                            item_type="recording",
                            state="completed",
                            started_at=info.start_time,
                            completed_at=datetime.now(),
                            duration_seconds=int((datetime.now() - info.start_time).total_seconds()) if info.start_time else 0,
                        )
                except Exception as e:
                    logger.error(f"Error finalizing recording {recording_id}: {e}")

            if blocking:
                time.sleep(0.5)
                finalize_recording()
            else:
                QTimer.singleShot(500, finalize_recording)

            return True

        except Exception as e:
            logger.error(f"Error stopping recording {recording_id}: {e}")
            return False

    # ========================== Query methods ==========================

    def is_download_active(self, download_id: str) -> bool:
        """Check if a download is currently active."""
        with self._lock:
            info = self._downloads.get(download_id)
            return info is not None and info.state in (DownloadState.ACTIVE, DownloadState.PAUSED)

    def is_recording_active(self, recording_id: str) -> bool:
        """Check if a recording is currently active."""
        with self._lock:
            return recording_id in self._recordings

    def get_active_downloads(self) -> list:
        """Get list of active download IDs."""
        with self._lock:
            return [did for did, info in self._downloads.items()
                    if info.state in (DownloadState.ACTIVE, DownloadState.PAUSED)]

    def get_active_recordings(self) -> list:
        """Get list of active recording IDs."""
        with self._lock:
            return list(self._recordings.keys())

    def get_all_download_info(self) -> List[dict]:
        """Get info for all active/paused downloads."""
        with self._lock:
            result = []
            for info in self._downloads.values():
                result.append({
                    'id': info.download_id,
                    'channel_name': info.channel_name,
                    'url': info.url,
                    'filepath': info.filepath,
                    'state': info.state.value,
                    'bytes_downloaded': info.bytes_downloaded,
                    'total_bytes': info.total_bytes,
                    'speed_bps': info.speed_bps,
                    'eta_seconds': info.eta_seconds,
                    'retry_count': info.retry_count,
                })
            return result

    def get_all_recording_info(self) -> List[dict]:
        """Get info for all active recordings."""
        with self._lock:
            result = []
            for info in self._recordings.values():
                elapsed = 0
                if info.start_time:
                    elapsed = int((datetime.now() - info.start_time).total_seconds())
                result.append({
                    'id': info.recording_id,
                    'channel_name': info.channel_name,
                    'url': info.url,
                    'filepath': info.filepath,
                    'elapsed_seconds': elapsed,
                })
            return result

    def get_queued_downloads(self) -> List[dict]:
        """Get info for all queued downloads."""
        with self._lock:
            result = []
            for i, info in enumerate(self._download_queue):
                result.append({
                    'id': info.download_id,
                    'channel_name': info.channel_name,
                    'position': i + 1,
                })
            return result

    def get_queue_position(self, download_id: str) -> int:
        """Get queue position for a download (0 if not queued)."""
        with self._lock:
            for i, info in enumerate(self._download_queue):
                if info.download_id == download_id:
                    return i + 1
            return 0

    def get_completed_items(self) -> List[dict]:
        """Get completed/failed/cancelled items history."""
        with self._lock:
            return list(self._completed_items)

    def get_active_download_count(self) -> int:
        """Get count of active (non-queued) downloads."""
        with self._lock:
            return sum(1 for d in self._downloads.values()
                       if d.state in (DownloadState.ACTIVE, DownloadState.PAUSED))

    def get_queued_download_count(self) -> int:
        """Get count of queued downloads."""
        with self._lock:
            return len(self._download_queue)

    def get_active_recording_count(self) -> int:
        """Get count of active recordings."""
        with self._lock:
            return len(self._recordings)

    # ========================== Completed items ==========================

    def _add_completed_item(self, **kwargs):
        """Add item to completed history. Must be called under lock."""
        self._completed_items.insert(0, kwargs)
        if len(self._completed_items) > self.COMPLETED_ITEMS_CAP:
            self._completed_items = self._completed_items[:self.COMPLETED_ITEMS_CAP]

    # ========================== Cleanup ==========================

    def cleanup_all(self, blocking: bool = True):
        """
        Stop all active downloads and recordings.

        Args:
            blocking: If True, waits for finalization (use during app shutdown)
        """
        logger.info(f"Cleaning up all downloads and recordings (blocking={blocking})")

        # Stop elapsed timer
        self._elapsed_timer.stop()

        # Cancel all downloads
        with self._lock:
            active_ids = list(self._downloads.keys())
            queued_ids = [info.download_id for info in self._download_queue]
            self._download_queue.clear()

        for download_id in active_ids:
            try:
                self.cancel_download(download_id)
            except Exception as e:
                logger.error(f"Error cancelling download {download_id}: {e}")

        # Stop all recordings
        with self._lock:
            recording_ids = list(self._recordings.keys())

        for recording_id in recording_ids:
            try:
                self.stop_recording(recording_id, blocking=blocking)
            except Exception as e:
                logger.error(f"Error stopping recording {recording_id}: {e}")

        logger.info(f"Cleaned up {len(active_ids)} downloads, {len(queued_ids)} queued, and {len(recording_ids)} recordings")


if __name__ == "__main__":
    manager = DownloadRecordManager()

    print("Testing media file detection:")
    print(f"  .mp4 URL: {manager.is_media_file('http://example.com/video.mp4')}")
    print(f"  .mkv URL: {manager.is_media_file('http://example.com/video.mkv')}")
    print(f"  .mp4 in query: {manager.is_media_file('http://example.com/stream?file=video.mp4&token=abc')}")
    print(f"  Stream URL: {manager.is_media_file('http://example.com/live/stream.m3u8')}")
    print(f"  No ext URL: {manager.is_media_file('http://example.com/live/stream')}")

    print("\nTesting filename generation:")
    print(f"  Download: {manager.generate_filename('Test Channel', 'http://example.com/video.mp4', False)}")
    print(f"  Recording: {manager.generate_filename('Live Channel', 'http://example.com/stream', True)}")
