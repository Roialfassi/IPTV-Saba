"""
Retry Overlay - Visual indicator for stream retry attempts.

Shows a semi-transparent overlay with retry status and cancel option
when the player is attempting to reconnect to a failed stream.
"""
import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsOpacityEffect, QProgressBar
)
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class RetryOverlay(QWidget):
    """
    Semi-transparent overlay showing retry status.

    Displays:
    - "Reconnecting..." message
    - Current attempt count (e.g., "Attempt 2 of 3")
    - Progress indicator
    - Cancel button to abort retry sequence
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._current_attempt = 0
        self._max_attempts = 3

    def _setup_ui(self):
        """Setup the overlay UI."""
        # Make overlay transparent for positioning but visible for content
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Container widget with dark background
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 0.9);
                border-radius: 10px;
                border: 2px solid #E50914;
            }
        """)
        container.setFixedSize(300, 180)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)

        # Title label
        self.title_label = QLabel("Reconnecting...")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #FFFFFF;
            background: transparent;
            border: none;
        """)
        container_layout.addWidget(self.title_label)

        # Attempt counter label
        self.attempt_label = QLabel("Attempt 1 of 3")
        self.attempt_label.setAlignment(Qt.AlignCenter)
        self.attempt_label.setStyleSheet("""
            font-size: 14px;
            color: #AAAAAA;
            background: transparent;
            border: none;
        """)
        container_layout.addWidget(self.attempt_label)

        # Progress bar (indeterminate)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate mode
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #333;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #E50914;
                border-radius: 3px;
            }
        """)
        container_layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedWidth(100)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #E50914;
            }
            QPushButton:pressed {
                background-color: #BF0811;
            }
        """)
        container_layout.addWidget(self.cancel_button, alignment=Qt.AlignCenter)

        main_layout.addWidget(container)

        # Initially hidden
        self.hide()

    def show_retry(self, attempt: int, max_attempts: int):
        """
        Show the overlay with retry status.

        Args:
            attempt: Current attempt number (1-based)
            max_attempts: Maximum number of attempts
        """
        self._current_attempt = attempt
        self._max_attempts = max_attempts
        self.attempt_label.setText(f"Attempt {attempt} of {max_attempts}")
        self._fade_in()

    def _fade_in(self):
        """Animate the overlay appearing."""
        self.show()

        # Create fade-in effect
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(300)
        self.opacity_anim.setStartValue(0)
        self.opacity_anim.setEndValue(1)
        self.opacity_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.opacity_anim.start()

    def hide_overlay(self):
        """Hide the overlay with fade-out animation."""
        if not self.isVisible():
            return

        # Create fade-out effect
        if not hasattr(self, 'opacity_effect') or self.opacity_effect is None:
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)

        self.opacity_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.opacity_anim.setDuration(200)
        self.opacity_anim.setStartValue(1)
        self.opacity_anim.setEndValue(0)
        self.opacity_anim.setEasingCurve(QEasingCurve.InCubic)
        self.opacity_anim.finished.connect(self.hide)
        self.opacity_anim.start()

    def update_status(self, message: str):
        """Update the title label with a custom message."""
        self.title_label.setText(message)
