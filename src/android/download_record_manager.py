"""
Android Download and Record Manager for IPTV-Saba

Handles:
- Downloading media files (.mp4, .mkv, .avi, etc.) to Android storage
- Recording live streams
- Progress tracking with Kivy events
- Background downloads using Android DownloadManager
- Notification support
"""

import os
import logging
import threading
from typing import Optional, Callable, Dict
from datetime import datetime
import requests
from pathlib import Path

# Kivy imports
from kivy.event import EventDispatcher
from kivy.properties import DictProperty, NumericProperty, StringProperty
from kivy.clock import Clock, mainthread
from kivy.utils import platform

# Android imports (only on Android)
if platform == 'android':
    from android import mActivity
    from jnius import autoclass, cast
    from android.permissions import request_permissions, Permission, check_permission

    # Android Java classes
    Environment = autoclass('android.os.Environment')
    DownloadManager = autoclass('android.app.DownloadManager')
    Uri = autoclass('android.net.Uri')
    Context = autoclass('android.content.Context')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DownloadRecordManager(EventDispatcher):
    """
    Manager for downloading media files and recording live streams on Android.
    """

    # Properties for tracking downloads
    active_downloads = DictProperty({})  # {download_id: {'filename': str, 'progress': int, 'status': str}}
    active_recordings = DictProperty({})  # {recording_id: {'filename': str, 'start_time': float}}

    # Media file extensions
    MEDIA_EXTENSIONS = {'.mp4', '.mkv', '.avi', '.mov', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg', '.ts'}

    def __init__(self, downloads_dir: str = "IPTV-Saba/Downloads", **kwargs):
        super().__init__(**kwargs)

        # Register events
        self.register_event_type('on_download_progress')
        self.register_event_type('on_download_complete')
        self.register_event_type('on_download_error')
        self.register_event_type('on_recording_started')
        self.register_event_type('on_recording_stopped')
        self.register_event_type('on_recording_error')

        # Set up downloads directory
        if platform == 'android':
            # Use Android external storage
            try:
                from android.storage import primary_external_storage_path
                storage_path = primary_external_storage_path()
                self.downloads_dir = os.path.join(storage_path, downloads_dir)
            except Exception as e:
                logger.error(f"Failed to get Android storage path: {e}")
                self.downloads_dir = os.path.join('/sdcard', downloads_dir)
        else:
            # Desktop testing
            self.downloads_dir = os.path.join(os.path.expanduser('~'), downloads_dir)

        # Create downloads directory
        os.makedirs(self.downloads_dir, exist_ok=True)
        logger.info(f"Download directory: {os.path.abspath(self.downloads_dir)}")

        # Active operations tracking
        self._download_threads = {}
        self._recording_threads = {}
        self._cancelled = set()

    # Event handlers (must be defined for registered events)
    def on_download_progress(self, download_id, bytes_downloaded, total_bytes):
        """Called when download progress updates"""
        pass

    def on_download_complete(self, download_id, file_path):
        """Called when download completes"""
        pass

    def on_download_error(self, download_id, error_message):
        """Called when download fails"""
        pass

    def on_recording_started(self, recording_id):
        """Called when recording starts"""
        pass

    def on_recording_stopped(self, recording_id, file_path):
        """Called when recording stops"""
        pass

    def on_recording_error(self, recording_id, error_message):
        """Called when recording fails"""
        pass

    def is_media_file(self, url: str) -> bool:
        """
        Check if URL points to a downloadable media file.

        Args:
            url: The stream URL

        Returns:
            True if it's a media file, False if it's a livestream
        """
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

    def download_media(self, url: str, channel_name: str, download_id: Optional[str] = None) -> str:
        """
        Download a media file using Android DownloadManager or requests.

        Args:
            url: URL of the media file
            channel_name: Name of the channel
            download_id: Optional custom download ID

        Returns:
            Download ID for tracking
        """
        if download_id is None:
            download_id = f"dl_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Generate filename
        filename = self.generate_filename(channel_name, url, is_recording=False)
        file_path = os.path.join(self.downloads_dir, filename)

        # Add to active downloads
        self.active_downloads[download_id] = {
            'filename': filename,
            'progress': 0,
            'status': 'starting',
            'file_path': file_path
        }

        # Use Android DownloadManager if on Android
        if platform == 'android':
            try:
                self._download_with_android_manager(url, file_path, download_id, channel_name)
            except Exception as e:
                logger.error(f"Android DownloadManager failed, falling back to requests: {e}")
                self._download_with_requests(url, file_path, download_id)
        else:
            # Desktop fallback
            self._download_with_requests(url, file_path, download_id)

        return download_id

    def _download_with_android_manager(self, url: str, file_path: str, download_id: str, title: str):
        """Download using Android DownloadManager"""
        try:
            # Get DownloadManager service
            context = mActivity.getApplicationContext()
            download_manager = context.getSystemService(Context.DOWNLOAD_SERVICE)

            # Create download request
            uri = Uri.parse(url)
            request = DownloadManager.Request(uri)

            # Set destination
            request.setDestinationUri(Uri.fromFile(autoclass('java.io.File')(file_path)))

            # Set title and description
            request.setTitle(f"Downloading {title}")
            request.setDescription(url)

            # Allow in metered networks
            request.setAllowedNetworkTypes(
                DownloadManager.Request.NETWORK_WIFI | DownloadManager.Request.NETWORK_MOBILE
            )

            # Show notification
            request.setNotificationVisibility(
                DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED
            )

            # Enqueue download
            android_dl_id = download_manager.enqueue(request)

            # Start monitoring thread
            thread = threading.Thread(
                target=self._monitor_android_download,
                args=(download_manager, android_dl_id, download_id, file_path),
                daemon=True
            )
            thread.start()
            self._download_threads[download_id] = thread

            logger.info(f"Started Android download: {download_id}")

        except Exception as e:
            logger.error(f"Android DownloadManager error: {e}")
            self._dispatch_error(download_id, str(e))
            raise

    def _monitor_android_download(self, download_manager, android_dl_id, download_id, file_path):
        """Monitor Android download progress"""
        query = autoclass('android.app.DownloadManager$Query')()
        query.setFilterById(android_dl_id)

        while download_id not in self._cancelled:
            try:
                cursor = download_manager.query(query)
                if cursor.moveToFirst():
                    status = cursor.getInt(cursor.getColumnIndex(DownloadManager.COLUMN_STATUS))

                    if status == DownloadManager.STATUS_SUCCESSFUL:
                        self._dispatch_complete(download_id, file_path)
                        break
                    elif status == DownloadManager.STATUS_FAILED:
                        reason = cursor.getInt(cursor.getColumnIndex(DownloadManager.COLUMN_REASON))
                        self._dispatch_error(download_id, f"Download failed with reason: {reason}")
                        break
                    elif status == DownloadManager.STATUS_RUNNING:
                        bytes_downloaded = cursor.getLong(
                            cursor.getColumnIndex(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR)
                        )
                        total_bytes = cursor.getLong(
                            cursor.getColumnIndex(DownloadManager.COLUMN_TOTAL_SIZE_BYTES)
                        )

                        if total_bytes > 0:
                            progress = int((bytes_downloaded / total_bytes) * 100)
                            self._dispatch_progress(download_id, bytes_downloaded, total_bytes, progress)

                cursor.close()
                threading.Event().wait(0.5)  # Check every 0.5 seconds

            except Exception as e:
                logger.error(f"Error monitoring download: {e}")
                break

    def _download_with_requests(self, url: str, file_path: str, download_id: str):
        """Download using requests library (fallback)"""
        thread = threading.Thread(
            target=self._download_thread,
            args=(url, file_path, download_id),
            daemon=True
        )
        thread.start()
        self._download_threads[download_id] = thread

    def _download_thread(self, url: str, file_path: str, download_id: str):
        """Background download thread using requests"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_bytes = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if download_id in self._cancelled:
                        logger.info(f"Download cancelled: {download_id}")
                        return

                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)

                        # Update progress
                        if total_bytes > 0:
                            progress = int((bytes_downloaded / total_bytes) * 100)
                            self._dispatch_progress(download_id, bytes_downloaded, total_bytes, progress)

            # Download complete
            self._dispatch_complete(download_id, file_path)

        except Exception as e:
            logger.error(f"Download error: {e}")
            self._dispatch_error(download_id, str(e))

    def start_recording(self, url: str, channel_name: str, recording_id: Optional[str] = None) -> str:
        """
        Start recording a live stream.

        Args:
            url: Stream URL
            channel_name: Name of the channel
            recording_id: Optional custom recording ID

        Returns:
            Recording ID for tracking
        """
        if recording_id is None:
            recording_id = f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Generate filename
        filename = self.generate_filename(channel_name, url, is_recording=True)
        file_path = os.path.join(self.downloads_dir, filename)

        # Add to active recordings
        self.active_recordings[recording_id] = {
            'filename': filename,
            'start_time': datetime.now().timestamp(),
            'file_path': file_path,
            'status': 'recording'
        }

        # Start recording thread
        thread = threading.Thread(
            target=self._recording_thread,
            args=(url, file_path, recording_id),
            daemon=True
        )
        thread.start()
        self._recording_threads[recording_id] = thread

        # Dispatch started event
        Clock.schedule_once(lambda dt: self.dispatch('on_recording_started', recording_id), 0)

        logger.info(f"Started recording: {recording_id}")
        return recording_id

    def _recording_thread(self, url: str, file_path: str, recording_id: str):
        """Background recording thread using requests stream"""
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if recording_id in self._cancelled:
                        logger.info(f"Recording stopped: {recording_id}")
                        break

                    if chunk:
                        f.write(chunk)

            # Recording complete
            Clock.schedule_once(
                lambda dt: self.dispatch('on_recording_stopped', recording_id, file_path),
                0
            )

        except Exception as e:
            logger.error(f"Recording error: {e}")
            Clock.schedule_once(
                lambda dt: self.dispatch('on_recording_error', recording_id, str(e)),
                0
            )

    def stop_recording(self, recording_id: str):
        """Stop an active recording"""
        if recording_id in self.active_recordings:
            self._cancelled.add(recording_id)
            logger.info(f"Stopping recording: {recording_id}")

    def cancel_download(self, download_id: str):
        """Cancel an active download"""
        if download_id in self.active_downloads:
            self._cancelled.add(download_id)
            logger.info(f"Cancelling download: {download_id}")

    @mainthread
    def _dispatch_progress(self, download_id, bytes_downloaded, total_bytes, progress):
        """Dispatch progress event on main thread"""
        if download_id in self.active_downloads:
            self.active_downloads[download_id]['progress'] = progress
            self.active_downloads[download_id]['status'] = 'downloading'
        self.dispatch('on_download_progress', download_id, bytes_downloaded, total_bytes)

    @mainthread
    def _dispatch_complete(self, download_id, file_path):
        """Dispatch complete event on main thread"""
        if download_id in self.active_downloads:
            self.active_downloads[download_id]['status'] = 'completed'
        self.dispatch('on_download_complete', download_id, file_path)

    @mainthread
    def _dispatch_error(self, download_id, error_message):
        """Dispatch error event on main thread"""
        if download_id in self.active_downloads:
            self.active_downloads[download_id]['status'] = 'error'
        self.dispatch('on_download_error', download_id, error_message)

    def get_download_status(self, download_id: str) -> Optional[Dict]:
        """Get status of a download"""
        return self.active_downloads.get(download_id)

    def get_recording_status(self, recording_id: str) -> Optional[Dict]:
        """Get status of a recording"""
        return self.active_recordings.get(recording_id)

    def list_downloaded_files(self):
        """List all downloaded files"""
        try:
            files = []
            for filename in os.listdir(self.downloads_dir):
                file_path = os.path.join(self.downloads_dir, filename)
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    files.append({
                        'filename': filename,
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': stat.st_mtime
                    })
            return files
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            return []
