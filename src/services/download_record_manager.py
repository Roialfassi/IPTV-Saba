#!/usr/bin/env python3
"""
Download and Record Manager for IPTV-Saba

Handles:
- Downloading media files (.mp4, .mkv, .avi, etc.)
- Recording live streams
- Progress tracking
- Concurrent downloads/recordings
"""

import os
import logging
import threading
from typing import Optional, Callable
from datetime import datetime
import requests
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import vlc

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DownloadRecordManager(QObject):
    """
    Manager for downloading media files and recording live streams.
    """

    # Signals for progress updates
    download_progress = pyqtSignal(str, int, int)  # (id, bytes_downloaded, total_bytes)
    download_complete = pyqtSignal(str, str)  # (id, file_path)
    download_error = pyqtSignal(str, str)  # (id, error_message)
    recording_started = pyqtSignal(str)  # (id)
    recording_stopped = pyqtSignal(str, str)  # (id, file_path)

    # Media file extensions
    MEDIA_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg', '.ts'}

    def __init__(self, downloads_dir: str = "downloads"):
        super().__init__()
        self.downloads_dir = downloads_dir
        self.active_downloads = {}  # {id: thread}
        self.active_recordings = {}  # {id: (vlc_recorder, thread)}
        self.cancelled_downloads = set()

        # Create downloads directory
        os.makedirs(self.downloads_dir, exist_ok=True)
        logger.info(f"Download directory: {os.path.abspath(self.downloads_dir)}")

    def is_media_file(self, url: str) -> bool:
        """
        Check if URL points to a downloadable media file.

        Args:
            url: The stream URL

        Returns:
            True if it's a media file, False if it's a livestream
        """
        # Check file extension
        url_lower = url.lower()
        for ext in self.MEDIA_EXTENSIONS:
            if ext in url_lower:
                return True
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
        # Sanitize channel name
        safe_name = "".join(c for c in channel_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')

        # Get extension from URL or use default
        extension = '.mp4'  # default
        if not is_recording:
            for ext in self.MEDIA_EXTENSIONS:
                if ext in url.lower():
                    extension = ext
                    break

        # Add timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if is_recording:
            filename = f"{safe_name}_recording_{timestamp}{extension}"
        else:
            filename = f"{safe_name}_download_{timestamp}{extension}"

        return filename

    def start_download(self, download_id: str, channel_name: str, url: str) -> bool:
        """
        Start downloading a media file.

        Args:
            download_id: Unique identifier for this download
            channel_name: Name of the channel
            url: URL to download from

        Returns:
            True if download started successfully
        """
        if download_id in self.active_downloads:
            logger.warning(f"Download {download_id} is already active")
            return False

        filename = self.generate_filename(channel_name, url, is_recording=False)
        filepath = os.path.join(self.downloads_dir, filename)

        # Create download thread
        download_thread = threading.Thread(
            target=self._download_worker,
            args=(download_id, url, filepath),
            daemon=True
        )

        self.active_downloads[download_id] = download_thread
        download_thread.start()

        logger.info(f"Started download {download_id}: {channel_name} -> {filepath}")
        return True

    def _download_worker(self, download_id: str, url: str, filepath: str):
        """
        Worker thread for downloading a file.

        Args:
            download_id: Unique identifier
            url: URL to download
            filepath: Destination file path
        """
        try:
            logger.info(f"Downloading from {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0
            chunk_size = 65536  # 64KB chunks

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size):
                    # Check if cancelled
                    if download_id in self.cancelled_downloads:
                        logger.info(f"Download {download_id} cancelled")
                        self.cancelled_downloads.remove(download_id)
                        try:
                            os.remove(filepath)
                        except:
                            pass
                        return

                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)

                        # Emit progress
                        self.download_progress.emit(download_id, bytes_downloaded, total_size)

            # Download complete
            logger.info(f"Download complete: {filepath}")
            self.download_complete.emit(download_id, filepath)

        except Exception as e:
            error_msg = f"Download error: {str(e)}"
            logger.error(error_msg)
            self.download_error.emit(download_id, error_msg)

            # Clean up partial file
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass

        finally:
            # Remove from active downloads
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]

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
        if recording_id in self.active_recordings:
            logger.warning(f"Recording {recording_id} is already active")
            return False

        filename = self.generate_filename(channel_name, url, is_recording=True)
        filepath = os.path.join(self.downloads_dir, filename)

        try:
            # Create VLC instance for recording
            vlc_instance = vlc.Instance('--sout-file-overwrite')
            player = vlc_instance.media_player_new()

            # Set up recording output
            sout_options = f":sout=#duplicate{{dst=file{{dst={filepath}}}}}"
            media = vlc_instance.media_new(url, sout_options)
            player.set_media(media)
            player.play()

            # Store recording info
            self.active_recordings[recording_id] = {
                'player': player,
                'instance': vlc_instance,
                'filepath': filepath,
                'start_time': datetime.now()
            }

            logger.info(f"Started recording {recording_id}: {channel_name} -> {filepath}")
            self.recording_started.emit(recording_id)
            return True

        except Exception as e:
            error_msg = f"Recording error: {str(e)}"
            logger.error(error_msg)
            self.download_error.emit(recording_id, error_msg)
            return False

    def stop_recording(self, recording_id: str, blocking: bool = False) -> bool:
        """
        Stop an active recording.

        Args:
            recording_id: Unique identifier for the recording
            blocking: If True, waits synchronously for finalization (for app cleanup)

        Returns:
            True if recording was stopped successfully
        """
        if recording_id not in self.active_recordings:
            logger.warning(f"Recording {recording_id} is not active")
            return False

        try:
            recording_info = self.active_recordings[recording_id]
            player = recording_info['player']
            vlc_instance = recording_info.get('instance')
            filepath = recording_info['filepath']

            # Stop the player
            player.stop()

            # Remove from active recordings immediately
            del self.active_recordings[recording_id]

            def finalize_recording():
                """Finalize the recording after VLC has finished writing."""
                try:
                    # Release VLC resources
                    player.release()
                    if vlc_instance:
                        vlc_instance.release()
                    logger.info(f"Stopped recording {recording_id}: {filepath}")
                    self.recording_stopped.emit(recording_id, filepath)
                except Exception as e:
                    logger.error(f"Error finalizing recording {recording_id}: {e}")

            if blocking:
                # Blocking mode for cleanup during app shutdown
                import time
                time.sleep(0.5)
                finalize_recording()
            else:
                # Non-blocking mode - use QTimer for UI-friendly finalization
                QTimer.singleShot(500, finalize_recording)

            return True

        except Exception as e:
            logger.error(f"Error stopping recording {recording_id}: {e}")
            return False

    def cancel_download(self, download_id: str) -> bool:
        """
        Cancel an active download.

        Args:
            download_id: Unique identifier for the download

        Returns:
            True if download was cancelled
        """
        if download_id not in self.active_downloads:
            logger.warning(f"Download {download_id} is not active")
            return False

        self.cancelled_downloads.add(download_id)
        logger.info(f"Cancelling download {download_id}")
        return True

    def is_download_active(self, download_id: str) -> bool:
        """Check if a download is currently active."""
        return download_id in self.active_downloads

    def is_recording_active(self, recording_id: str) -> bool:
        """Check if a recording is currently active."""
        return recording_id in self.active_recordings

    def get_active_downloads(self):
        """Get list of active download IDs."""
        return list(self.active_downloads.keys())

    def get_active_recordings(self):
        """Get list of active recording IDs."""
        return list(self.active_recordings.keys())

    def cleanup_all(self, blocking: bool = True):
        """
        Stop all active downloads and recordings.
        
        Args:
            blocking: If True, waits for finalization (use during app shutdown)
        """
        logger.info(f"Cleaning up all downloads and recordings (blocking={blocking})")
        
        # Cancel all downloads
        active_download_ids = list(self.active_downloads.keys())
        for download_id in active_download_ids:
            try:
                self.cancel_download(download_id)
            except Exception as e:
                logger.error(f"Error cancelling download {download_id}: {e}")

        # Stop all recordings (use blocking mode if specified)
        active_recording_ids = list(self.active_recordings.keys())
        for recording_id in active_recording_ids:
            try:
                self.stop_recording(recording_id, blocking=blocking)
            except Exception as e:
                logger.error(f"Error stopping recording {recording_id}: {e}")

        logger.info(f"Cleaned up {len(active_download_ids)} downloads and {len(active_recording_ids)} recordings")


if __name__ == "__main__":
    # Test the download/record manager
    manager = DownloadRecordManager()

    # Test media file detection
    print("Testing media file detection:")
    print(f"  .mp4 URL: {manager.is_media_file('http://example.com/video.mp4')}")
    print(f"  .mkv URL: {manager.is_media_file('http://example.com/video.mkv')}")
    print(f"  Stream URL: {manager.is_media_file('http://example.com/live/stream.m3u8')}")

    # Test filename generation
    print("\nTesting filename generation:")
    print(f"  Download: {manager.generate_filename('Test Channel', 'http://example.com/video.mp4', False)}")
    print(f"  Recording: {manager.generate_filename('Live Channel', 'http://example.com/stream', True)}")
