"""
Video Overlay Widget - Transparent overlay that floats above VLC player

This overlay stays on top of VLC's hardware-rendered video by using a separate
window with transparent background and always-on-top flags.
"""

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSlider
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QPalette, QFont
import logging

logger = logging.getLogger(__name__)


class VideoOverlay(QWidget):
    """
    Transparent overlay window that floats above VLC video player.

    This window is frameless, transparent, and stays on top of other windows.
    It automatically repositions itself to match the video player's geometry.
    """

    # Signals
    close_clicked = pyqtSignal()
    fullscreen_toggled = pyqtSignal()

    def __init__(self, parent_widget, show_watermark=True, show_controls=True):
        """
        Initialize the video overlay.

        Args:
            parent_widget: The widget containing the video player (used for positioning)
            show_watermark: Whether to show watermark text
            show_controls: Whether to show playback controls
        """
        # Create as a separate top-level window, but track the parent for positioning
        super().__init__(parent=None)
        self.parent_widget = parent_widget
        self.show_watermark = show_watermark
        self.show_controls = show_controls

        # Configure window to float above video
        self.setup_window_flags()

        # Create UI elements
        self.setup_ui()

        # Auto-hide timer for controls
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.timeout.connect(self.hide_controls)
        self.auto_hide_timer.setInterval(3000)  # Hide after 3 seconds

        # Timer to track parent widget geometry
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.update_geometry_from_parent)
        self.position_timer.start(100)  # Update every 100ms

        logger.info("VideoOverlay initialized")

    def setup_window_flags(self):
        """Configure window to be transparent and always on top"""
        # Make this a frameless, transparent window that stays on top
        self.setWindowFlags(
            Qt.FramelessWindowHint |  # No title bar or borders
            Qt.WindowStaysOnTopHint |  # Always on top
            Qt.Tool |  # Tool window (doesn't show in taskbar)
            Qt.WindowTransparentForInput  # Allow clicks to pass through to video
        )

        # Remove the WindowTransparentForInput for interactive controls
        # We'll apply it selectively to specific areas
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )

        # Enable transparency
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # Make sure overlay can receive mouse events for controls
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def setup_ui(self):
        """Create overlay UI elements"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Top area - Watermark
        if self.show_watermark:
            self.watermark_label = QLabel("🎬 IPTV Player")
            self.watermark_label.setStyleSheet("""
                QLabel {
                    color: rgba(255, 255, 255, 200);
                    background-color: rgba(0, 0, 0, 100);
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 16px;
                    font-weight: bold;
                }
            """)
            self.watermark_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            main_layout.addWidget(self.watermark_label, 0, Qt.AlignTop | Qt.AlignLeft)

        # Spacer to push controls to bottom
        main_layout.addStretch()

        # Bottom area - Playback controls
        if self.show_controls:
            self.controls_widget = QWidget()
            self.controls_widget.setStyleSheet("""
                QWidget {
                    background-color: rgba(0, 0, 0, 180);
                    border-radius: 10px;
                }
                QPushButton {
                    background-color: rgba(229, 9, 20, 200);
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(229, 9, 20, 255);
                }
                QPushButton:pressed {
                    background-color: rgba(180, 7, 16, 255);
                }
            """)

            controls_layout = QHBoxLayout(self.controls_widget)
            controls_layout.setContentsMargins(15, 15, 15, 15)

            # Play/Pause button
            self.play_pause_btn = QPushButton("⏸ Pause")
            self.play_pause_btn.setFixedWidth(120)
            controls_layout.addWidget(self.play_pause_btn)

            # Fullscreen toggle
            self.fullscreen_btn = QPushButton("⛶ Fullscreen")
            self.fullscreen_btn.setFixedWidth(140)
            self.fullscreen_btn.clicked.connect(self.fullscreen_toggled.emit)
            controls_layout.addWidget(self.fullscreen_btn)

            controls_layout.addStretch()

            # Close button
            self.close_btn = QPushButton("✕ Close")
            self.close_btn.setFixedWidth(100)
            self.close_btn.clicked.connect(self.close_clicked.emit)
            controls_layout.addWidget(self.close_btn)

            main_layout.addWidget(self.controls_widget, 0, Qt.AlignBottom)

            # Start with controls visible, will auto-hide
            self.controls_widget.show()
            self.auto_hide_timer.start()

    def update_geometry_from_parent(self):
        """
        Update overlay geometry to match parent widget.
        This keeps the overlay positioned correctly over the video.
        """
        if self.parent_widget and self.parent_widget.isVisible():
            # Get parent's global position and size
            parent_rect = self.parent_widget.geometry()
            parent_global_pos = self.parent_widget.mapToGlobal(parent_rect.topLeft())

            # Set overlay to match parent's geometry
            self.setGeometry(
                parent_global_pos.x(),
                parent_global_pos.y(),
                parent_rect.width(),
                parent_rect.height()
            )

    def show_controls(self):
        """Show the controls overlay"""
        if self.show_controls:
            self.controls_widget.show()
            self.auto_hide_timer.start()

    def hide_controls(self):
        """Hide the controls overlay"""
        if self.show_controls:
            self.controls_widget.hide()

    def mouseMoveEvent(self, event):
        """Show controls when mouse moves over overlay"""
        self.show_controls()
        super().mouseMoveEvent(event)

    def set_watermark_text(self, text):
        """Update watermark text"""
        if self.show_watermark:
            self.watermark_label.setText(text)

    def cleanup(self):
        """Stop timers and cleanup resources"""
        self.position_timer.stop()
        self.auto_hide_timer.stop()
        logger.info("VideoOverlay cleaned up")


class SimpleVideoOverlay(QWidget):
    """
    Simplified overlay - just a watermark with no interactive controls.
    Clicks pass through to the video player underneath.
    """

    def __init__(self, parent_widget, watermark_text="🎬 IPTV"):
        super().__init__(parent=None)
        self.parent_widget = parent_widget

        # Configure as transparent, non-interactive overlay
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowTransparentForInput  # Pass clicks through
        )

        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Create watermark
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.watermark = QLabel(watermark_text)
        self.watermark.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 150);
                background-color: rgba(0, 0, 0, 80);
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.watermark, 0, Qt.AlignTop | Qt.AlignRight)
        layout.addStretch()

        # Position tracking timer
        self.position_timer = QTimer(self)
        self.position_timer.timeout.connect(self.update_geometry_from_parent)
        self.position_timer.start(100)

    def update_geometry_from_parent(self):
        """Match parent widget geometry"""
        if self.parent_widget and self.parent_widget.isVisible():
            parent_rect = self.parent_widget.geometry()
            parent_global_pos = self.parent_widget.mapToGlobal(parent_rect.topLeft())

            self.setGeometry(
                parent_global_pos.x(),
                parent_global_pos.y(),
                parent_rect.width(),
                parent_rect.height()
            )

    def set_text(self, text):
        """Update watermark text"""
        self.watermark.setText(text)

    def cleanup(self):
        """Cleanup resources"""
        self.position_timer.stop()
