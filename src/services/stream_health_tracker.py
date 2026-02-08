"""
Stream Health Tracker - Tracks problematic channels and failure patterns.

This module helps identify channels that consistently fail, enabling
smarter retry decisions and user warnings about unreliable streams.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from threading import RLock

logger = logging.getLogger(__name__)


@dataclass
class ChannelHealth:
    """Health metrics for a single channel."""
    channel_name: str
    failure_count: int = 0
    consecutive_failures: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0
    total_play_attempts: int = 0

    def record_failure(self):
        """Record a playback failure."""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure_time = time.time()
        self.total_play_attempts += 1

    def record_success(self):
        """Record a successful playback."""
        self.consecutive_failures = 0
        self.last_success_time = time.time()
        self.total_play_attempts += 1

    @property
    def failure_rate(self) -> float:
        """Calculate the failure rate (0.0 to 1.0)."""
        if self.total_play_attempts == 0:
            return 0.0
        return self.failure_count / self.total_play_attempts

    @property
    def is_problematic(self) -> bool:
        """
        Determine if this channel is considered problematic.

        A channel is problematic if:
        - It has 3+ consecutive failures, OR
        - It has a failure rate > 50% with at least 5 attempts
        """
        if self.consecutive_failures >= 3:
            return True
        if self.total_play_attempts >= 5 and self.failure_rate > 0.5:
            return True
        return False

    @property
    def time_since_last_failure(self) -> float:
        """Get seconds since last failure."""
        if self.last_failure_time == 0:
            return float('inf')
        return time.time() - self.last_failure_time


class StreamHealthTracker:
    """
    Singleton tracker for stream health across all channels.

    Thread-safe implementation for tracking channel failures and successes
    across the application.
    """

    _instance: Optional['StreamHealthTracker'] = None
    _lock = RLock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._channel_health: Dict[str, ChannelHealth] = {}
        self._data_lock = RLock()
        self._initialized = True
        logger.info("StreamHealthTracker initialized")

    @classmethod
    def get_instance(cls) -> 'StreamHealthTracker':
        """Get the singleton instance."""
        return cls()

    def record_failure(self, channel_name: str):
        """
        Record a playback failure for a channel.

        Args:
            channel_name: Name of the channel that failed.
        """
        with self._data_lock:
            if channel_name not in self._channel_health:
                self._channel_health[channel_name] = ChannelHealth(channel_name)
            self._channel_health[channel_name].record_failure()
            health = self._channel_health[channel_name]
            logger.info(
                f"Channel '{channel_name}' failure recorded: "
                f"consecutive={health.consecutive_failures}, total={health.failure_count}"
            )

    def record_success(self, channel_name: str):
        """
        Record a successful playback for a channel.

        Args:
            channel_name: Name of the channel that played successfully.
        """
        with self._data_lock:
            if channel_name not in self._channel_health:
                self._channel_health[channel_name] = ChannelHealth(channel_name)
            self._channel_health[channel_name].record_success()
            logger.debug(f"Channel '{channel_name}' success recorded")

    def get_health(self, channel_name: str) -> Optional[ChannelHealth]:
        """
        Get health metrics for a channel.

        Args:
            channel_name: Name of the channel.

        Returns:
            ChannelHealth object or None if no data exists.
        """
        with self._data_lock:
            return self._channel_health.get(channel_name)

    def is_problematic(self, channel_name: str) -> bool:
        """
        Check if a channel is considered problematic.

        Args:
            channel_name: Name of the channel.

        Returns:
            True if the channel has reliability issues.
        """
        with self._data_lock:
            health = self._channel_health.get(channel_name)
            if health is None:
                return False
            return health.is_problematic

    def get_consecutive_failures(self, channel_name: str) -> int:
        """
        Get the number of consecutive failures for a channel.

        Args:
            channel_name: Name of the channel.

        Returns:
            Number of consecutive failures.
        """
        with self._data_lock:
            health = self._channel_health.get(channel_name)
            if health is None:
                return 0
            return health.consecutive_failures

    def reset_channel(self, channel_name: str):
        """
        Reset health metrics for a channel.

        Args:
            channel_name: Name of the channel to reset.
        """
        with self._data_lock:
            if channel_name in self._channel_health:
                del self._channel_health[channel_name]
                logger.info(f"Reset health metrics for channel '{channel_name}'")

    def get_problematic_channels(self) -> list:
        """
        Get a list of all problematic channels.

        Returns:
            List of channel names that are considered problematic.
        """
        with self._data_lock:
            return [
                name for name, health in self._channel_health.items()
                if health.is_problematic
            ]

    def clear_all(self):
        """Clear all health tracking data."""
        with self._data_lock:
            self._channel_health.clear()
            logger.info("Cleared all stream health data")


# Convenience function
def get_health_tracker() -> StreamHealthTracker:
    """Get the stream health tracker instance."""
    return StreamHealthTracker.get_instance()
