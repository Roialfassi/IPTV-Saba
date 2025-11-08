"""
Example: VLC Video Player with Overlay

Demonstrates multiple approaches to add overlays on top of VLC video player.
"""

import sys
import vlc
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QFrame,
                             QPushButton, QLabel, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer
from pathlib import Path

# Add parent directory to path to import overlay
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.widgets.video_overlay import VideoOverlay, SimpleVideoOverlay


class VLCPlayerWithOverlay(QWidget):
    """
    VLC Player with floating overlay window.

    This is the RECOMMENDED approach - uses a separate window that floats
    above the VLC video player.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLC Player with Overlay - Solution 1")
        self.resize(800, 600)

        # Initialize VLC
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()

        self.setup_ui()
        self.overlay = None

    def setup_ui(self):
        """Create UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Video frame - VLC will render here
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_frame)

        # Control panel below video
        controls_layout = QHBoxLayout()

        play_btn = QPushButton("▶ Play Sample")
        play_btn.clicked.connect(self.play_sample)
        controls_layout.addWidget(play_btn)

        toggle_overlay_btn = QPushButton("Toggle Overlay")
        toggle_overlay_btn.clicked.connect(self.toggle_overlay)
        controls_layout.addWidget(toggle_overlay_btn)

        simple_overlay_btn = QPushButton("Simple Overlay")
        simple_overlay_btn.clicked.connect(self.add_simple_overlay)
        controls_layout.addWidget(simple_overlay_btn)

        layout.addLayout(controls_layout)

    def showEvent(self, event):
        """Attach VLC player when widget is shown"""
        super().showEvent(event)
        # Delay to ensure window is ready
        QTimer.singleShot(100, self.attach_player)

    def attach_player(self):
        """Attach VLC player to video frame"""
        win_id = int(self.video_frame.winId())

        if sys.platform.startswith('linux'):
            self.player.set_xwindow(win_id)
        elif sys.platform == "win32":
            self.player.set_hwnd(win_id)
        elif sys.platform == "darwin":
            self.player.set_nsobject(win_id)

        print(f"✓ Player attached to window ID: {win_id}")

    def play_sample(self):
        """Play a sample video (use a test URL or file)"""
        # Example: Big Buck Bunny sample video
        media = self.vlc_instance.media_new(
            "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        )
        self.player.set_media(media)
        self.player.play()
        print("▶ Playing sample video")

        # Auto-show overlay when video starts
        QTimer.singleShot(1000, self.show_overlay)

    def show_overlay(self):
        """Show the interactive overlay"""
        if not self.overlay:
            self.overlay = VideoOverlay(
                parent_widget=self.video_frame,
                show_watermark=True,
                show_controls=True
            )
            self.overlay.close_clicked.connect(self.close)
            self.overlay.play_pause_btn.clicked.connect(self.toggle_playback)

        self.overlay.show()
        print("✓ Overlay shown - should appear ABOVE video")

    def toggle_overlay(self):
        """Toggle overlay visibility"""
        if self.overlay:
            if self.overlay.isVisible():
                self.overlay.hide()
            else:
                self.overlay.show()

    def add_simple_overlay(self):
        """Add a simple non-interactive watermark overlay"""
        simple = SimpleVideoOverlay(
            parent_widget=self.video_frame,
            watermark_text="🎬 Demo Watermark"
        )
        simple.show()
        print("✓ Simple overlay shown (non-interactive)")

    def toggle_playback(self):
        """Toggle play/pause"""
        if self.player.is_playing():
            self.player.pause()
            if self.overlay:
                self.overlay.play_pause_btn.setText("▶ Play")
        else:
            self.player.play()
            if self.overlay:
                self.overlay.play_pause_btn.setText("⏸ Pause")

    def closeEvent(self, event):
        """Cleanup when closing"""
        if self.overlay:
            self.overlay.cleanup()
            self.overlay.close()
        self.player.stop()
        super().closeEvent(event)


# ============================================================================
# SOLUTION 2: QWidget Stack with Raise
# ============================================================================

class VLCPlayerWithStackedOverlay(QWidget):
    """
    Alternative approach using stacked widgets with raise_().

    WARNING: This approach is LESS RELIABLE because VLC's hardware rendering
    may still bypass Qt's widget stacking order. Use Solution 1 instead.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLC Player - Solution 2 (Less Reliable)")
        self.resize(800, 600)

        # Initialize VLC
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()

        self.setup_ui()

    def setup_ui(self):
        """Create UI with stacked layout"""
        # Use absolute positioning (no layout manager)
        # This allows us to manually control z-order

        # Video frame at bottom
        self.video_frame = QFrame(self)
        self.video_frame.setStyleSheet("background-color: black;")

        # Overlay widget on top
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.overlay_widget.setStyleSheet("background-color: transparent;")

        overlay_layout = QVBoxLayout(self.overlay_widget)
        overlay_layout.setContentsMargins(20, 20, 20, 20)

        watermark = QLabel("🎬 Overlay (Method 2)")
        watermark.setStyleSheet("""
            background-color: rgba(229, 9, 20, 180);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
        """)
        overlay_layout.addWidget(watermark, 0, Qt.AlignTop | Qt.AlignLeft)
        overlay_layout.addStretch()

        # Control buttons at bottom
        button_layout = QHBoxLayout()

        play_btn = QPushButton("▶ Play Sample")
        play_btn.clicked.connect(self.play_sample)
        button_layout.addWidget(play_btn)

        self.overlay_widget.layout().addLayout(button_layout)

    def resizeEvent(self, event):
        """Update widget positions on resize"""
        super().resizeEvent(event)
        # Make both widgets fill the entire window
        self.video_frame.setGeometry(0, 0, self.width(), self.height())
        self.overlay_widget.setGeometry(0, 0, self.width(), self.height())

        # CRITICAL: Raise overlay to top of stack
        self.overlay_widget.raise_()

    def showEvent(self, event):
        """Attach VLC player when shown"""
        super().showEvent(event)
        QTimer.singleShot(100, self.attach_player)

    def attach_player(self):
        """Attach VLC to video frame"""
        win_id = int(self.video_frame.winId())

        if sys.platform.startswith('linux'):
            self.player.set_xwindow(win_id)
        elif sys.platform == "win32":
            self.player.set_hwnd(win_id)
        elif sys.platform == "darwin":
            self.player.set_nsobject(win_id)

        # Force overlay to top
        self.overlay_widget.raise_()
        print(f"✓ Player attached, overlay raised")

    def play_sample(self):
        """Play sample video"""
        media = self.vlc_instance.media_new(
            "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        )
        self.player.set_media(media)
        self.player.play()

        # Try to force overlay to stay on top
        QTimer.singleShot(500, lambda: self.overlay_widget.raise_())
        QTimer.singleShot(1000, lambda: self.overlay_widget.raise_())


# ============================================================================
# SOLUTION 3: Custom Paint Events (Advanced)
# ============================================================================

class VLCPlayerWithPaintOverlay(QFrame):
    """
    Advanced approach: Override paintEvent to draw overlay directly.

    WARNING: This may not work reliably with VLC's hardware rendering.
    VLC bypasses Qt's paint events entirely.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLC Player - Solution 3 (Paint Overlay)")
        self.resize(800, 600)
        self.setStyleSheet("background-color: black;")

        # Initialize VLC
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()

        # Overlay text
        self.overlay_text = "🎬 Paint Overlay"

        # Update timer to trigger repaints
        self.paint_timer = QTimer(self)
        self.paint_timer.timeout.connect(self.update)
        self.paint_timer.start(33)  # ~30 FPS

    def showEvent(self, event):
        """Attach VLC player"""
        super().showEvent(event)
        QTimer.singleShot(100, self.attach_player)

    def attach_player(self):
        """Attach VLC to this widget"""
        win_id = int(self.winId())

        if sys.platform.startswith('linux'):
            self.player.set_xwindow(win_id)
        elif sys.platform == "win32":
            self.player.set_hwnd(win_id)
        elif sys.platform == "darwin":
            self.player.set_nsobject(win_id)

        print(f"✓ Player attached - attempting paint overlay")

        # Play sample
        media = self.vlc_instance.media_new(
            "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        )
        self.player.set_media(media)
        self.player.play()

    def paintEvent(self, event):
        """
        Custom paint - draw overlay on top.

        NOTE: This will likely NOT work because VLC renders directly to
        the window handle, bypassing Qt's paint events.
        """
        super().paintEvent(event)

        from PyQt5.QtGui import QPainter, QColor, QFont

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw semi-transparent overlay box
        painter.fillRect(20, 20, 200, 60, QColor(229, 9, 20, 180))

        # Draw text
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(30, 50, self.overlay_text)

        print("⚠ Paint event called (may not be visible over VLC)")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run the example"""
    app = QApplication(sys.argv)

    print("\n" + "="*60)
    print("VLC Overlay Solutions Demo")
    print("="*60)
    print("\nSOLUTION 1: Separate Floating Window (RECOMMENDED)")
    print("  - Most reliable, works on all platforms")
    print("  - Overlay is a separate window that floats above video")
    print("\nSOLUTION 2: Stacked Widgets with raise_()")
    print("  - Less reliable due to VLC hardware rendering")
    print("  - May work on some platforms/configurations")
    print("\nSOLUTION 3: Custom Paint Events")
    print("  - Generally does NOT work with VLC")
    print("  - Included for educational purposes")
    print("="*60 + "\n")

    # Launch Solution 1 (recommended)
    window = VLCPlayerWithOverlay()
    window.show()

    # Uncomment to try alternative solutions:
    # window = VLCPlayerWithStackedOverlay()
    # window.show()

    # window = VLCPlayerWithPaintOverlay()
    # window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
