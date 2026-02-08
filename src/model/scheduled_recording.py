"""
Scheduled Recording Model - Data model for scheduled recordings.

Represents a scheduled recording with start/end times, channel info,
and status tracking.
"""
import uuid
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class RecordingStatus(Enum):
    """Status states for a scheduled recording."""
    PENDING = "pending"          # Waiting to start
    RECORDING = "recording"      # Currently recording
    COMPLETED = "completed"      # Successfully finished
    FAILED = "failed"            # Recording failed
    CANCELLED = "cancelled"      # User cancelled


@dataclass
class ScheduledRecording:
    """
    Represents a scheduled recording.

    Attributes:
        id: Unique identifier for the recording
        channel_name: Name of the channel to record
        stream_url: URL of the stream to record
        start_time: When to start recording (datetime)
        end_time: When to stop recording (datetime)
        status: Current status of the recording
        created_at: When this schedule was created
        output_path: Path where the recording will be saved (set when recording starts)
        error_message: Error message if recording failed
    """
    channel_name: str
    stream_url: str
    start_time: datetime
    end_time: datetime
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: RecordingStatus = RecordingStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    output_path: Optional[str] = None
    error_message: Optional[str] = None

    def __post_init__(self):
        """Validate the recording times."""
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")

    @property
    def duration_seconds(self) -> int:
        """Get the scheduled duration in seconds."""
        return int((self.end_time - self.start_time).total_seconds())

    @property
    def duration_minutes(self) -> int:
        """Get the scheduled duration in minutes."""
        return self.duration_seconds // 60

    @property
    def is_active(self) -> bool:
        """Check if recording is currently active."""
        return self.status == RecordingStatus.RECORDING

    @property
    def is_pending(self) -> bool:
        """Check if recording is waiting to start."""
        return self.status == RecordingStatus.PENDING

    @property
    def is_finished(self) -> bool:
        """Check if recording has ended (any terminal state)."""
        return self.status in (
            RecordingStatus.COMPLETED,
            RecordingStatus.FAILED,
            RecordingStatus.CANCELLED
        )

    @property
    def time_until_start(self) -> float:
        """Get seconds until recording should start (negative if past)."""
        return (self.start_time - datetime.now()).total_seconds()

    @property
    def time_until_end(self) -> float:
        """Get seconds until recording should end (negative if past)."""
        return (self.end_time - datetime.now()).total_seconds()

    @property
    def should_start_now(self) -> bool:
        """Check if recording should start now."""
        return self.is_pending and self.time_until_start <= 0

    @property
    def should_stop_now(self) -> bool:
        """Check if recording should stop now."""
        return self.is_active and self.time_until_end <= 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the recording to a dictionary.

        Returns:
            Dictionary representation for JSON storage.
        """
        return {
            "id": self.id,
            "channel_name": self.channel_name,
            "stream_url": self.stream_url,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "output_path": self.output_path,
            "error_message": self.error_message
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledRecording':
        """
        Create a ScheduledRecording from a dictionary.

        Args:
            data: Dictionary with recording data.

        Returns:
            ScheduledRecording instance.
        """
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            channel_name=data["channel_name"],
            stream_url=data["stream_url"],
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            status=RecordingStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            output_path=data.get("output_path"),
            error_message=data.get("error_message")
        )

    def __str__(self) -> str:
        """String representation."""
        return (
            f"ScheduledRecording({self.id}: {self.channel_name} "
            f"from {self.start_time.strftime('%H:%M')} to {self.end_time.strftime('%H:%M')} "
            f"[{self.status.value}])"
        )
