"""
Recording Scheduler - QTimer-based scheduler for automatic recordings.

Monitors scheduled recordings and triggers start/stop at appropriate times.
Integrates with DownloadRecordManager for actual recording operations.
"""
import logging
from datetime import datetime
from typing import Optional, Dict

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from src.model.scheduled_recording import ScheduledRecording, RecordingStatus
from src.services.schedule_manager import ScheduleManager
from src.services.download_record_manager import DownloadRecordManager

logger = logging.getLogger(__name__)


class RecordingScheduler(QObject):
    """
    QTimer-based scheduler for automatic recordings.

    Monitors pending schedules and triggers recordings at the scheduled times.
    Uses QTimer for precise timing within the Qt event loop.
    """

    # Signals
    schedule_started = pyqtSignal(str, str)  # schedule_id, channel_name
    schedule_completed = pyqtSignal(str, str, str)  # schedule_id, channel_name, output_path
    schedule_failed = pyqtSignal(str, str, str)  # schedule_id, channel_name, error_message
    schedule_cancelled = pyqtSignal(str, str)  # schedule_id, channel_name

    # Check interval in milliseconds (check every 30 seconds)
    CHECK_INTERVAL_MS = 30000

    def __init__(
        self,
        schedule_manager: ScheduleManager,
        download_manager: DownloadRecordManager,
        parent=None
    ):
        """
        Initialize the recording scheduler.

        Args:
            schedule_manager: Manager for schedule persistence.
            download_manager: Manager for actual recording operations.
            parent: Optional Qt parent.
        """
        super().__init__(parent)
        self._schedule_manager = schedule_manager
        self._download_manager = download_manager

        # Active recording timers (schedule_id -> QTimer for stop)
        self._stop_timers: Dict[str, QTimer] = {}

        # Active recording IDs (schedule_id -> download_manager recording_id)
        self._active_recordings: Dict[str, str] = {}

        # Main check timer
        self._check_timer = QTimer(self)
        self._check_timer.timeout.connect(self._check_schedules)

        # Connect download manager signals
        self._download_manager.recording_stopped.connect(self._on_recording_stopped)
        self._download_manager.download_error.connect(self._on_recording_error)

        logger.info("RecordingScheduler initialized")

    def start(self):
        """Start the scheduler."""
        # Do an immediate check
        self._check_schedules()
        # Start periodic checking
        self._check_timer.start(self.CHECK_INTERVAL_MS)
        logger.info("RecordingScheduler started")

    def stop(self):
        """Stop the scheduler and all active recordings."""
        self._check_timer.stop()

        # Stop all active recordings
        for schedule_id in list(self._active_recordings.keys()):
            self._stop_recording(schedule_id, cancelled=True)

        # Cancel all stop timers
        for timer in self._stop_timers.values():
            timer.stop()
        self._stop_timers.clear()

        logger.info("RecordingScheduler stopped")

    def _check_schedules(self):
        """Check for schedules that need to start or stop."""
        now = datetime.now()

        # Check pending schedules
        for schedule in self._schedule_manager.get_pending_schedules():
            if schedule.should_start_now:
                self._start_recording(schedule)

        # Check active schedules for stop time
        for schedule in self._schedule_manager.get_active_schedules():
            if schedule.should_stop_now:
                self._stop_recording(schedule.id)

    def _start_recording(self, schedule: ScheduledRecording):
        """
        Start a scheduled recording.

        Args:
            schedule: The schedule to start recording.
        """
        logger.info(f"Starting scheduled recording: {schedule.channel_name}")

        # Generate recording ID
        recording_id = f"scheduled_{schedule.id}"

        try:
            # Start recording via download manager
            success = self._download_manager.start_recording(
                recording_id,
                schedule.channel_name,
                schedule.stream_url
            )

            if success:
                # Update status
                self._schedule_manager.update_status(schedule.id, RecordingStatus.RECORDING)
                self._active_recordings[schedule.id] = recording_id

                # Set up stop timer
                self._setup_stop_timer(schedule)

                self.schedule_started.emit(schedule.id, schedule.channel_name)
                logger.info(f"Scheduled recording started: {schedule.channel_name}")
            else:
                # Recording failed to start
                self._schedule_manager.update_status(
                    schedule.id,
                    RecordingStatus.FAILED,
                    error_message="Failed to start recording"
                )
                self.schedule_failed.emit(
                    schedule.id,
                    schedule.channel_name,
                    "Failed to start recording"
                )
                logger.error(f"Failed to start scheduled recording: {schedule.channel_name}")

        except Exception as e:
            logger.error(f"Error starting scheduled recording: {e}")
            self._schedule_manager.update_status(
                schedule.id,
                RecordingStatus.FAILED,
                error_message=str(e)
            )
            self.schedule_failed.emit(schedule.id, schedule.channel_name, str(e))

    def _setup_stop_timer(self, schedule: ScheduledRecording):
        """
        Set up a timer to stop the recording at the scheduled end time.

        Args:
            schedule: The active schedule.
        """
        # Calculate milliseconds until end
        ms_until_end = max(0, int(schedule.time_until_end * 1000))

        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._stop_recording(schedule.id))
        timer.start(ms_until_end)

        self._stop_timers[schedule.id] = timer
        logger.debug(f"Stop timer set for {schedule.id}: {ms_until_end}ms")

    def _stop_recording(self, schedule_id: str, cancelled: bool = False):
        """
        Stop a scheduled recording.

        Args:
            schedule_id: ID of the schedule to stop.
            cancelled: True if cancelled by user, False if normal completion.
        """
        schedule = self._schedule_manager.get_schedule(schedule_id)
        if not schedule:
            return

        recording_id = self._active_recordings.get(schedule_id)
        if not recording_id:
            return

        logger.info(f"Stopping scheduled recording: {schedule.channel_name}")

        try:
            # Stop recording via download manager
            self._download_manager.stop_recording(recording_id)

            # Clean up
            del self._active_recordings[schedule_id]
            if schedule_id in self._stop_timers:
                self._stop_timers[schedule_id].stop()
                del self._stop_timers[schedule_id]

            if cancelled:
                self._schedule_manager.update_status(schedule_id, RecordingStatus.CANCELLED)
                self.schedule_cancelled.emit(schedule_id, schedule.channel_name)
            # Note: completion status is updated in _on_recording_stopped

        except Exception as e:
            logger.error(f"Error stopping scheduled recording: {e}")

    def _on_recording_stopped(self, recording_id: str, output_path: str):
        """
        Handle recording stopped signal from download manager.

        Args:
            recording_id: The recording ID.
            output_path: Path to the output file.
        """
        # Find the corresponding schedule
        for schedule_id, rec_id in list(self._active_recordings.items()):
            if rec_id == recording_id:
                schedule = self._schedule_manager.get_schedule(schedule_id)
                if schedule and schedule.status == RecordingStatus.RECORDING:
                    self._schedule_manager.update_status(
                        schedule_id,
                        RecordingStatus.COMPLETED,
                        output_path=output_path
                    )
                    self.schedule_completed.emit(
                        schedule_id,
                        schedule.channel_name,
                        output_path
                    )
                    logger.info(f"Scheduled recording completed: {schedule.channel_name}")

                # Clean up
                if schedule_id in self._active_recordings:
                    del self._active_recordings[schedule_id]
                break

    def _on_recording_error(self, recording_id: str, error_message: str):
        """
        Handle recording error signal from download manager.

        Args:
            recording_id: The recording ID.
            error_message: Error description.
        """
        # Find the corresponding schedule
        for schedule_id, rec_id in list(self._active_recordings.items()):
            if rec_id == recording_id:
                schedule = self._schedule_manager.get_schedule(schedule_id)
                if schedule:
                    self._schedule_manager.update_status(
                        schedule_id,
                        RecordingStatus.FAILED,
                        error_message=error_message
                    )
                    self.schedule_failed.emit(
                        schedule_id,
                        schedule.channel_name,
                        error_message
                    )
                    logger.error(f"Scheduled recording failed: {schedule.channel_name} - {error_message}")

                # Clean up
                if schedule_id in self._active_recordings:
                    del self._active_recordings[schedule_id]
                if schedule_id in self._stop_timers:
                    self._stop_timers[schedule_id].stop()
                    del self._stop_timers[schedule_id]
                break

    def cancel_schedule(self, schedule_id: str) -> bool:
        """
        Cancel a scheduled or active recording.

        Args:
            schedule_id: ID of the schedule to cancel.

        Returns:
            True if cancelled successfully.
        """
        schedule = self._schedule_manager.get_schedule(schedule_id)
        if not schedule:
            return False

        if schedule.is_active:
            # Stop active recording
            self._stop_recording(schedule_id, cancelled=True)
        elif schedule.is_pending:
            # Just update status
            self._schedule_manager.update_status(schedule_id, RecordingStatus.CANCELLED)
            self.schedule_cancelled.emit(schedule_id, schedule.channel_name)

        return True

    def get_upcoming_schedules(self, hours: int = 24) -> list:
        """
        Get schedules starting within the specified hours.

        Args:
            hours: Number of hours to look ahead.

        Returns:
            List of upcoming ScheduledRecording objects.
        """
        pending = self._schedule_manager.get_pending_schedules()
        return [
            s for s in pending
            if s.time_until_start <= hours * 3600
        ]
