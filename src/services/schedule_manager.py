"""
Schedule Manager - Persistence layer for scheduled recordings.

Handles saving and loading scheduled recordings to/from JSON,
and provides conflict detection for overlapping schedules.
"""
import json
import os
import logging
from datetime import datetime
from typing import List, Optional
from threading import RLock

from src.model.scheduled_recording import ScheduledRecording, RecordingStatus

logger = logging.getLogger(__name__)


class ScheduleManager:
    """
    Manages persistence and retrieval of scheduled recordings.

    Thread-safe implementation with JSON file storage.
    """

    def __init__(self, config_dir: str):
        """
        Initialize the schedule manager.

        Args:
            config_dir: Directory to store the schedules.json file.
        """
        self._config_dir = config_dir
        self._file_path = os.path.join(config_dir, "schedules.json")
        self._schedules: List[ScheduledRecording] = []
        self._lock = RLock()

        # Ensure directory exists
        os.makedirs(config_dir, exist_ok=True)

        # Load existing schedules
        self._load()

    def _load(self):
        """Load schedules from JSON file."""
        with self._lock:
            if not os.path.exists(self._file_path):
                self._schedules = []
                return

            try:
                with open(self._file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._schedules = [
                        ScheduledRecording.from_dict(item)
                        for item in data
                    ]
                logger.info(f"Loaded {len(self._schedules)} scheduled recordings")
            except Exception as e:
                logger.error(f"Error loading schedules: {e}")
                self._schedules = []

    def _save(self):
        """Save schedules to JSON file."""
        with self._lock:
            try:
                data = [schedule.to_dict() for schedule in self._schedules]
                with open(self._file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                logger.debug(f"Saved {len(self._schedules)} scheduled recordings")
            except Exception as e:
                logger.error(f"Error saving schedules: {e}")

    def add_schedule(self, schedule: ScheduledRecording) -> bool:
        """
        Add a new scheduled recording.

        Args:
            schedule: The ScheduledRecording to add.

        Returns:
            True if added successfully, False if conflicts exist.
        """
        with self._lock:
            # Check for conflicts
            conflicts = self.get_conflicts(schedule)
            if conflicts:
                logger.warning(f"Schedule conflicts with {len(conflicts)} existing recordings")
                return False

            self._schedules.append(schedule)
            self._save()
            logger.info(f"Added schedule: {schedule}")
            return True

    def remove_schedule(self, schedule_id: str) -> bool:
        """
        Remove a scheduled recording.

        Args:
            schedule_id: ID of the schedule to remove.

        Returns:
            True if removed, False if not found.
        """
        with self._lock:
            for i, schedule in enumerate(self._schedules):
                if schedule.id == schedule_id:
                    del self._schedules[i]
                    self._save()
                    logger.info(f"Removed schedule: {schedule_id}")
                    return True
            return False

    def update_status(
        self,
        schedule_id: str,
        status: RecordingStatus,
        output_path: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update the status of a scheduled recording.

        Args:
            schedule_id: ID of the schedule to update.
            status: New status.
            output_path: Path to output file (for completed recordings).
            error_message: Error message (for failed recordings).

        Returns:
            True if updated, False if not found.
        """
        with self._lock:
            for schedule in self._schedules:
                if schedule.id == schedule_id:
                    schedule.status = status
                    if output_path:
                        schedule.output_path = output_path
                    if error_message:
                        schedule.error_message = error_message
                    self._save()
                    logger.info(f"Updated schedule {schedule_id} status to {status.value}")
                    return True
            return False

    def get_schedule(self, schedule_id: str) -> Optional[ScheduledRecording]:
        """
        Get a specific schedule by ID.

        Args:
            schedule_id: ID of the schedule.

        Returns:
            The ScheduledRecording or None if not found.
        """
        with self._lock:
            for schedule in self._schedules:
                if schedule.id == schedule_id:
                    return schedule
            return None

    def get_all_schedules(self) -> List[ScheduledRecording]:
        """
        Get all scheduled recordings.

        Returns:
            List of all ScheduledRecording objects.
        """
        with self._lock:
            return list(self._schedules)

    def get_pending_schedules(self) -> List[ScheduledRecording]:
        """
        Get all pending (not yet started) schedules.

        Returns:
            List of pending ScheduledRecording objects, sorted by start time.
        """
        with self._lock:
            pending = [s for s in self._schedules if s.is_pending]
            return sorted(pending, key=lambda s: s.start_time)

    def get_active_schedules(self) -> List[ScheduledRecording]:
        """
        Get all currently recording schedules.

        Returns:
            List of active ScheduledRecording objects.
        """
        with self._lock:
            return [s for s in self._schedules if s.is_active]

    def get_conflicts(self, new_schedule: ScheduledRecording) -> List[ScheduledRecording]:
        """
        Find schedules that conflict with a proposed new schedule.

        Conflicts occur when recordings overlap in time. This is a simple
        implementation that doesn't consider multiple recording capabilities.

        Args:
            new_schedule: The proposed new schedule.

        Returns:
            List of conflicting ScheduledRecording objects.
        """
        conflicts = []
        with self._lock:
            for existing in self._schedules:
                # Skip finished recordings
                if existing.is_finished:
                    continue
                # Skip self
                if existing.id == new_schedule.id:
                    continue
                # Check for overlap
                if self._times_overlap(
                    new_schedule.start_time, new_schedule.end_time,
                    existing.start_time, existing.end_time
                ):
                    conflicts.append(existing)
        return conflicts

    @staticmethod
    def _times_overlap(
        start1: datetime, end1: datetime,
        start2: datetime, end2: datetime
    ) -> bool:
        """Check if two time ranges overlap."""
        return start1 < end2 and start2 < end1

    def cleanup_old_schedules(self, days: int = 7):
        """
        Remove finished schedules older than specified days.

        Args:
            days: Number of days to keep finished schedules.
        """
        with self._lock:
            cutoff = datetime.now()
            original_count = len(self._schedules)
            self._schedules = [
                s for s in self._schedules
                if not s.is_finished or (cutoff - s.end_time).days < days
            ]
            removed = original_count - len(self._schedules)
            if removed > 0:
                self._save()
                logger.info(f"Cleaned up {removed} old schedules")
