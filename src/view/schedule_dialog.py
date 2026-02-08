"""
Schedule Recording Dialog - UI for creating scheduled recordings.

Provides a dialog for users to set up scheduled recordings with
start/end time selection and validation.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QDateTimeEdit, QMessageBox, QGroupBox,
    QFormLayout
)
from PyQt5.QtCore import Qt, QDateTime

from src.model.channel_model import Channel
from src.model.scheduled_recording import ScheduledRecording

logger = logging.getLogger(__name__)


class ScheduleRecordingDialog(QDialog):
    """
    Dialog for scheduling a recording.

    Allows users to select start and end times for recording a channel.
    """

    def __init__(self, channel: Channel, parent=None):
        """
        Initialize the schedule dialog.

        Args:
            channel: The channel to schedule recording for.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._channel = channel
        self._result: Optional[ScheduledRecording] = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("Schedule Recording")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: white;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QDateTimeEdit {
                background-color: #2c2c2c;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
                min-height: 30px;
            }
            QDateTimeEdit:focus {
                border: 1px solid #E50914;
            }
            QPushButton {
                background-color: #E50914;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #F6121D;
            }
            QPushButton:pressed {
                background-color: #BF0811;
            }
            QPushButton#cancelButton {
                background-color: #444;
            }
            QPushButton#cancelButton:hover {
                background-color: #555;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Channel info
        channel_label = QLabel(f"Channel: {self._channel.name}")
        channel_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #E50914;")
        layout.addWidget(channel_label)

        # Time selection group
        time_group = QGroupBox("Recording Time")
        time_layout = QFormLayout(time_group)
        time_layout.setSpacing(10)

        # Start time
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(60))  # Default: 1 min from now
        self.start_time_edit.setMinimumDateTime(QDateTime.currentDateTime())
        self.start_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.start_time_edit.setCalendarPopup(True)
        time_layout.addRow("Start Time:", self.start_time_edit)

        # End time
        self.end_time_edit = QDateTimeEdit()
        self.end_time_edit.setDateTime(QDateTime.currentDateTime().addSecs(3660))  # Default: 1 hour from now
        self.end_time_edit.setMinimumDateTime(QDateTime.currentDateTime().addSecs(60))
        self.end_time_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.end_time_edit.setCalendarPopup(True)
        time_layout.addRow("End Time:", self.end_time_edit)

        layout.addWidget(time_group)

        # Duration info
        self.duration_label = QLabel()
        self.duration_label.setStyleSheet("color: #888;")
        self._update_duration()
        layout.addWidget(self.duration_label)

        # Connect time changes to update duration
        self.start_time_edit.dateTimeChanged.connect(self._update_duration)
        self.end_time_edit.dateTimeChanged.connect(self._update_duration)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()

        self.schedule_button = QPushButton("Schedule")
        self.schedule_button.clicked.connect(self._on_schedule_clicked)
        button_layout.addWidget(self.schedule_button)

        layout.addLayout(button_layout)

    def _update_duration(self):
        """Update the duration label based on selected times."""
        start = self.start_time_edit.dateTime().toPyDateTime()
        end = self.end_time_edit.dateTime().toPyDateTime()

        if end > start:
            duration = end - start
            hours = duration.seconds // 3600
            minutes = (duration.seconds % 3600) // 60
            if hours > 0:
                self.duration_label.setText(f"Duration: {hours}h {minutes}m")
            else:
                self.duration_label.setText(f"Duration: {minutes} minutes")
            self.duration_label.setStyleSheet("color: #888;")
        else:
            self.duration_label.setText("Invalid: End time must be after start time")
            self.duration_label.setStyleSheet("color: #E50914;")

    def _validate(self) -> bool:
        """
        Validate the input.

        Returns:
            True if valid, False otherwise.
        """
        start = self.start_time_edit.dateTime().toPyDateTime()
        end = self.end_time_edit.dateTime().toPyDateTime()
        now = datetime.now()

        # Check start time is in the future
        if start < now:
            QMessageBox.warning(
                self,
                "Invalid Time",
                "Start time must be in the future."
            )
            return False

        # Check end time is after start time
        if end <= start:
            QMessageBox.warning(
                self,
                "Invalid Time",
                "End time must be after start time."
            )
            return False

        # Check minimum duration (1 minute)
        duration = (end - start).total_seconds()
        if duration < 60:
            QMessageBox.warning(
                self,
                "Invalid Duration",
                "Recording must be at least 1 minute long."
            )
            return False

        # Check maximum duration (24 hours)
        if duration > 86400:
            QMessageBox.warning(
                self,
                "Invalid Duration",
                "Recording cannot exceed 24 hours."
            )
            return False

        return True

    def _on_schedule_clicked(self):
        """Handle schedule button click."""
        if not self._validate():
            return

        start = self.start_time_edit.dateTime().toPyDateTime()
        end = self.end_time_edit.dateTime().toPyDateTime()

        try:
            self._result = ScheduledRecording(
                channel_name=self._channel.name,
                stream_url=self._channel.stream_url,
                start_time=start,
                end_time=end
            )
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def get_result(self) -> Optional[ScheduledRecording]:
        """
        Get the created schedule.

        Returns:
            The ScheduledRecording if user clicked Schedule, None if cancelled.
        """
        return self._result

    @staticmethod
    def create_schedule(channel: Channel, parent=None) -> Optional[ScheduledRecording]:
        """
        Static convenience method to show the dialog and get a schedule.

        Args:
            channel: The channel to schedule.
            parent: Parent widget.

        Returns:
            ScheduledRecording if created, None if cancelled.
        """
        dialog = ScheduleRecordingDialog(channel, parent)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_result()
        return None
