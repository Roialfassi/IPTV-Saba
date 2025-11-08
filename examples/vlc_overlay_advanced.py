"""
Advanced VLC Overlay Techniques

SOLUTION 4: Render overlay directly onto video frames using VLC callbacks.
This is the most advanced approach - modifies video frames before display.
"""

import sys
import vlc
import ctypes
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QFrame, QPushButton
from PyQt5.QtCore import QTimer


class VLCPlayerWithVideoCallback(QWidget):
    """
    Advanced: Render overlay by intercepting VLC video callbacks.

    This approach uses VLC's video output callbacks to:
    1. Intercept decoded video frames
    2. Draw overlay graphics directly onto the video buffer
    3. Let VLC render the modified frames

    PROS:
    - Overlay is baked into the video stream (always visible)
    - Works with any rendering backend
    - No z-index issues
    - Can be captured in screenshots/recordings

    CONS:
    - Complex implementation
    - Performance overhead (modifying every frame)
    - Harder to make interactive overlays
    - Requires video format knowledge (YUV, RGB, etc.)
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLC Player - Video Callback Overlay")
        self.resize(800, 600)

        # Video dimensions (will be set when video loads)
        self.video_width = 0
        self.video_height = 0

        # Initialize VLC
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()

        # Video buffer for modification
        self.buffer = None

        self.setup_ui()
        self.setup_video_callbacks()

    def setup_ui(self):
        """Create UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Video frame
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_frame)

        # Controls
        play_btn = QPushButton("▶ Play Sample with Baked Overlay")
        play_btn.clicked.connect(self.play_sample)
        layout.addWidget(play_btn)

    def setup_video_callbacks(self):
        """
        Configure VLC video callbacks to intercept and modify frames.

        VLC provides these callbacks:
        - set_format(): Called when video format is determined
        - set_callbacks(): Lock/unlock/display callbacks for frame access
        """

        # Define callback function types
        VideoLockCb = ctypes.CFUNCTYPE(
            ctypes.c_void_p,  # Return: pointer to buffer
            ctypes.c_void_p,  # opaque
            ctypes.POINTER(ctypes.c_void_p)  # planes
        )
        VideoUnlockCb = ctypes.CFUNCTYPE(
            None,  # Return: void
            ctypes.c_void_p,  # opaque
            ctypes.c_void_p,  # picture
            ctypes.POINTER(ctypes.c_void_p)  # planes
        )
        VideoDisplayCb = ctypes.CFUNCTYPE(
            None,  # Return: void
            ctypes.c_void_p,  # opaque
            ctypes.c_void_p  # picture
        )

        # Create callback instances
        @VideoLockCb
        def lock_callback(opaque, planes):
            """Called when VLC locks a video buffer for writing"""
            # planes is an array of pointers to each plane (Y, U, V for YUV)
            # For RGB, there's only one plane
            planes[0] = self.buffer_ptr
            return self.buffer_ptr

        @VideoUnlockCb
        def unlock_callback(opaque, picture, planes):
            """Called when VLC is done writing to the buffer"""
            # This is where we can modify the frame
            self.add_overlay_to_buffer()

        @VideoDisplayCb
        def display_callback(opaque, picture):
            """Called when frame should be displayed"""
            pass

        # Store callbacks to prevent garbage collection
        self.lock_cb = lock_callback
        self.unlock_cb = unlock_callback
        self.display_cb = display_callback

        # Set callbacks on player
        self.player.video_set_callbacks(
            self.lock_cb,
            self.unlock_cb,
            self.display_cb,
            None  # opaque data
        )

        # Set video format (RGB for easier manipulation)
        # Format: RV32 = RGB32 (RGBA)
        self.player.video_set_format(
            "RV32",  # chroma/codec
            800,  # width (will be overridden by actual video)
            600,  # height
            800 * 4  # pitch (bytes per line)
        )

    def add_overlay_to_buffer(self):
        """
        Modify the video buffer to add overlay graphics.

        The buffer contains raw pixel data (RGBA in our case).
        We can modify it directly or use PIL/numpy for easier manipulation.
        """
        if self.buffer is None:
            return

        try:
            # Convert buffer to numpy array for manipulation
            # Shape: (height, width, 4) for RGBA
            frame = np.frombuffer(
                self.buffer,
                dtype=np.uint8
            ).reshape((self.video_height, self.video_width, 4))

            # Convert to PIL Image for easier drawing
            img = Image.fromarray(frame, 'RGBA')

            # Create drawing context
            draw = ImageDraw.Draw(img)

            # Draw overlay elements
            # 1. Watermark in top-right corner
            draw.rectangle(
                [(self.video_width - 220, 10), (self.video_width - 10, 60)],
                fill=(229, 9, 20, 180)
            )
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()

            draw.text(
                (self.video_width - 210, 25),
                "🎬 IPTV Overlay",
                fill=(255, 255, 255, 255),
                font=font
            )

            # 2. Semi-transparent banner at bottom
            draw.rectangle(
                [(0, self.video_height - 80), (self.video_width, self.video_height)],
                fill=(0, 0, 0, 120)
            )

            # Convert back to bytes and copy to buffer
            modified = np.array(img)
            np.copyto(
                np.frombuffer(self.buffer, dtype=np.uint8).reshape(modified.shape),
                modified
            )

        except Exception as e:
            print(f"Error modifying frame: {e}")

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

    def play_sample(self):
        """Play sample video with overlay baked in"""
        # Create media
        media = self.vlc_instance.media_new(
            "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        )

        # Parse media to get video dimensions
        media.parse()

        # Wait for parsing to complete
        QTimer.singleShot(1000, lambda: self.start_playback_with_overlay(media))

    def start_playback_with_overlay(self, media):
        """Start playback after getting video info"""
        # Get video dimensions (try to get from track info)
        tracks = media.tracks_get()
        if tracks:
            for track in tracks:
                if track.type == vlc.TrackType.video:
                    self.video_width = track.video.width
                    self.video_height = track.video.height
                    break

        # Fallback dimensions
        if self.video_width == 0:
            self.video_width = 800
            self.video_height = 600

        print(f"Video dimensions: {self.video_width}x{self.video_height}")

        # Allocate buffer
        buffer_size = self.video_width * self.video_height * 4  # RGBA
        self.buffer = bytearray(buffer_size)
        self.buffer_ptr = ctypes.cast(
            (ctypes.c_ubyte * len(self.buffer)).from_buffer(self.buffer),
            ctypes.c_void_p
        )

        # Update video format with correct dimensions
        self.player.video_set_format(
            "RV32",
            self.video_width,
            self.video_height,
            self.video_width * 4
        )

        # Set media and play
        self.player.set_media(media)
        self.player.play()

        print("▶ Playing with overlay baked into video stream")


# ============================================================================
# SOLUTION 5: Using VLC's built-in marquee/logo filters
# ============================================================================

class VLCPlayerWithMarqueeFilter(QWidget):
    """
    Simple approach: Use VLC's built-in video filters.

    VLC has built-in filters for:
    - marquee: Text overlay
    - logo: Image overlay
    - mosaic: Multiple video overlay

    PROS:
    - Simple to implement
    - No custom rendering code
    - Built into VLC
    - Good performance

    CONS:
    - Limited customization
    - Static overlays (not interactive)
    - Filter configuration can be tricky
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("VLC Player - Marquee Filter")
        self.resize(800, 600)

        # Initialize VLC with video filter options
        vlc_args = [
            '--video-filter=marq',  # Enable marquee filter
            '--marq-marquee=🎬 IPTV Player - VLC Filter',
            '--marq-position=8',  # Top-right
            '--marq-size=16',
            '--marq-color=0xFFFFFF',
            '--marq-opacity=255'
        ]
        self.vlc_instance = vlc.Instance(vlc_args)
        self.player = self.vlc_instance.media_player_new()

        self.setup_ui()

    def setup_ui(self):
        """Create UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_frame)

        play_btn = QPushButton("▶ Play with Marquee Filter")
        play_btn.clicked.connect(self.play_sample)
        layout.addWidget(play_btn)

        update_text_btn = QPushButton("Update Overlay Text")
        update_text_btn.clicked.connect(self.update_marquee_text)
        layout.addWidget(update_text_btn)

    def showEvent(self, event):
        """Attach player"""
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

    def play_sample(self):
        """Play sample video"""
        media = self.vlc_instance.media_new(
            "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
        )

        # Can also set filter options per-media
        media.add_option(':marq-marquee=Playing Sample Video')

        self.player.set_media(media)
        self.player.play()

        print("▶ Playing with VLC marquee filter overlay")

    def update_marquee_text(self):
        """Update the marquee text dynamically"""
        from datetime import datetime
        new_text = f"Updated at {datetime.now().strftime('%H:%M:%S')}"

        # Note: Updating marquee text at runtime requires using
        # VLC's libvlc_video_set_marquee_string function
        # This is a bit complex with python-vlc binding

        print(f"⚠ Marquee update: {new_text}")
        print("   (Runtime updates require additional VLC API calls)")


# ============================================================================
# COMPARISON TABLE
# ============================================================================

def print_comparison():
    """Print comparison of all overlay approaches"""
    print("\n" + "="*80)
    print("VLC OVERLAY SOLUTIONS COMPARISON")
    print("="*80)
    print("""
╔════════════════════════╦═══════════╦═════════════╦═══════════╦════════════╗
║ Solution               ║ Reliable  ║ Interactive ║ Complex   ║ Performant ║
╠════════════════════════╬═══════════╬═════════════╬═══════════╬════════════╣
║ 1. Floating Window     ║    ✓✓✓    ║     ✓✓✓     ║     ✓     ║     ✓✓     ║
║    (RECOMMENDED)       ║           ║             ║           ║            ║
╠════════════════════════╬═══════════╬═════════════╬═══════════╬════════════╣
║ 2. Stacked Widgets     ║     ✓     ║     ✓✓✓     ║     ✓     ║    ✓✓✓     ║
║    (Platform-dependent)║           ║             ║           ║            ║
╠════════════════════════╬═══════════╬═════════════╬═══════════╬════════════╣
║ 3. Paint Events        ║     ✗     ║     ✓✓      ║     ✓     ║     ✓✓     ║
║    (Doesn't work)      ║           ║             ║           ║            ║
╠════════════════════════╬═══════════╬═════════════╬═══════════╬════════════╣
║ 4. Video Callbacks     ║    ✓✓✓    ║      ✓      ║    ✓✓✓    ║     ✓      ║
║    (Advanced)          ║           ║             ║           ║            ║
╠════════════════════════╬═══════════╬═════════════╬═══════════╬════════════╣
║ 5. VLC Filters         ║    ✓✓✓    ║      ✗      ║     ✓     ║    ✓✓✓     ║
║    (Built-in)          ║           ║             ║           ║            ║
╚════════════════════════╩═══════════╩═════════════╩═══════════╩════════════╝

RECOMMENDATIONS:

🏆 BEST FOR MOST CASES: Solution 1 - Floating Window
   - Always works, cross-platform
   - Supports interactive controls
   - Easy to implement

🎯 FOR SIMPLE WATERMARKS: Solution 5 - VLC Filters
   - Built-in, no custom code
   - Excellent performance
   - But not interactive

🔧 FOR ADVANCED NEEDS: Solution 4 - Video Callbacks
   - Overlay baked into video (capturable)
   - Works with any VLC backend
   - But complex and performance-heavy

⚠️  AVOID: Solutions 2 & 3
   - Unreliable due to VLC's hardware rendering
   - May work on some systems but fail on others
""")
    print("="*80 + "\n")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run advanced examples"""
    app = QApplication(sys.argv)

    print_comparison()

    # Choose which example to run:

    # Example 1: Video callbacks (advanced)
    # window = VLCPlayerWithVideoCallback()
    # window.show()

    # Example 2: Marquee filter (simple)
    window = VLCPlayerWithMarqueeFilter()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
