# VLC Video Overlay Solutions Guide

## Problem Overview

When VLC starts playing video, overlays (watermarks, controls, text) disappear behind the video. This happens because VLC uses **hardware-accelerated direct rendering** that bypasses Qt's widget stacking system.

---

## Why This Happens (Technical Deep Dive)

### Root Cause: Direct Hardware Rendering

When you attach VLC to a Qt widget using:
```python
self.player.set_xwindow(win_id)  # Linux
self.player.set_hwnd(win_id)     # Windows
self.player.set_nsobject(win_id) # macOS
```

VLC takes **complete control** of that native window handle and:

1. **Bypasses Qt's Rendering Pipeline**
   - VLC writes directly to the GPU framebuffer
   - Qt widgets are rendered in a separate software layer
   - The OS compositor stacks hardware video planes ABOVE software UI

2. **Uses Hardware Video Overlays**
   - GPU allocates dedicated video overlay planes
   - Video acceleration APIs (VAAPI, VDPAU, DXVA2, VideoToolbox) render to these planes
   - These planes have higher z-order priority than normal windows

3. **Direct Memory Access**
   - Video frames go directly from decoder → GPU memory → display
   - Never passes through Qt's paint events
   - Qt's `raise_()`, `setWindowFlag()`, and layout stacking have no effect

### Why Qt Methods Don't Work

```python
# ❌ THESE WON'T WORK:
overlay.raise_()                    # Qt z-order, not OS compositor
overlay.setWindowFlags(Qt.WindowStaysOnTopHint)  # Only for Qt windows
layout.addWidget(overlay)           # Layout order doesn't affect hardware planes
```

---

## Solutions Comparison

| Solution | Reliability | Interactive | Complexity | Performance | Cross-Platform |
|----------|-------------|-------------|------------|-------------|----------------|
| **1. Floating Window** | ✅ Excellent | ✅ Yes | ⭐ Easy | ⭐⭐ Good | ✅ Yes |
| **2. Stacked Widgets** | ⚠️ Poor | ✅ Yes | ⭐ Easy | ⭐⭐⭐ Excellent | ⚠️ Platform-dependent |
| **3. Paint Events** | ❌ Fails | ✅ Yes | ⭐ Easy | ⭐⭐ Good | ❌ No |
| **4. Video Callbacks** | ✅ Excellent | ⚠️ Limited | ⭐⭐⭐ Hard | ⭐ Heavy | ✅ Yes |
| **5. VLC Filters** | ✅ Excellent | ❌ No | ⭐ Easy | ⭐⭐⭐ Excellent | ✅ Yes |

---

## Solution 1: Floating Window (RECOMMENDED)

### How It Works
Create a **separate transparent window** that:
- Floats above the video player window
- Stays positioned over the video using geometry tracking
- Has `WindowStaysOnTopHint` flag to stay above VLC's rendering

### Implementation

The overlay is already implemented in `src/widgets/video_overlay.py`. Here's how to integrate it:

#### Option A: Interactive Overlay with Controls

```python
from src.widgets.video_overlay import VideoOverlay

class YourVideoPlayer(QWidget):
    def __init__(self):
        # ... your existing setup ...

        # Create overlay
        self.overlay = None

    def start_video(self):
        """Called when video starts playing"""
        # ... your existing playback code ...

        # Show overlay
        if not self.overlay:
            self.overlay = VideoOverlay(
                parent_widget=self.video_frame,  # The QFrame with VLC
                show_watermark=True,
                show_controls=True
            )
            # Connect signals
            self.overlay.close_clicked.connect(self.stop_playback)
            self.overlay.fullscreen_toggled.connect(self.toggle_fullscreen)
            self.overlay.play_pause_btn.clicked.connect(self.toggle_play_pause)

        self.overlay.show()

    def cleanup(self):
        """Called when closing player"""
        if self.overlay:
            self.overlay.cleanup()
            self.overlay.close()
```

#### Option B: Simple Watermark Only

```python
from src.widgets.video_overlay import SimpleVideoOverlay

class YourVideoPlayer(QWidget):
    def __init__(self):
        # ... your existing setup ...

    def start_video(self):
        # ... your existing playback code ...

        # Add simple watermark
        self.watermark = SimpleVideoOverlay(
            parent_widget=self.video_frame,
            watermark_text="🎬 IPTV Player"
        )
        self.watermark.show()
```

### Customizing the Overlay

```python
# Change watermark text
overlay.set_watermark_text("📺 Channel Name")

# Change button text
overlay.play_pause_btn.setText("▶ Resume")

# Customize appearance
overlay.watermark_label.setStyleSheet("""
    QLabel {
        color: white;
        background-color: rgba(0, 100, 200, 150);
        padding: 15px;
        border-radius: 10px;
    }
""")
```

---

## Solution 2: VLC Built-in Filters (For Static Overlays)

### Best For
- Static watermarks
- Channel names/logos
- Timestamp displays
- Non-interactive overlays

### Implementation

```python
# Initialize VLC with filter options
vlc_args = [
    '--video-filter=marq',  # Enable text overlay
    '--marq-marquee=🎬 Your Channel Name',
    '--marq-position=9',  # Position: 0=center, 1=left, 2=right, 4=top, 8=bottom
    '--marq-size=20',  # Font size
    '--marq-color=0xFFFFFF',  # White
    '--marq-opacity=200'  # 0-255
]
self.vlc_instance = vlc.Instance(vlc_args)
self.player = self.vlc_instance.media_player_new()
```

### Position Values
```python
POSITIONS = {
    'center': 0,
    'left': 1,
    'right': 2,
    'top': 4,
    'bottom': 8,
    'top-left': 5,      # 1 + 4
    'top-right': 6,     # 2 + 4
    'bottom-left': 9,   # 1 + 8
    'bottom-right': 10  # 2 + 8
}
```

### Adding Logo Overlay

```python
vlc_args = [
    '--video-filter=logo',
    '--logo-file=/path/to/logo.png',
    '--logo-position=6',  # Top-right
    '--logo-opacity=200',
    '--logo-x=10',  # X offset
    '--logo-y=10'   # Y offset
]
```

---

## Integration Examples for Your Codebase

### For `FullScreenView` (full_screen_view.py)

```python
# Add to FullScreenView.__init__() after line 79

from src.widgets.video_overlay import VideoOverlay

class FullScreenView(QWidget):
    def __init__(self, channel: Channel, existing_player=None, existing_instance=None):
        # ... existing code ...

        # ADD THIS: Create overlay
        self.video_overlay = None

    def showEvent(self, event):
        """Called when widget is shown"""
        super().showEvent(event)
        logger.info("FullScreenView showEvent triggered - attaching player now")
        QTimer.singleShot(100, self.attach_player_to_window)

        # ADD THIS: Show overlay after player is attached
        QTimer.singleShot(500, self.show_overlay)

    # ADD THIS METHOD:
    def show_overlay(self):
        """Show floating overlay above video"""
        if not self.video_overlay:
            self.video_overlay = VideoOverlay(
                parent_widget=self.video_frame,
                show_watermark=True,
                show_controls=True
            )

            # Update watermark with channel name
            self.video_overlay.set_watermark_text(f"📺 {self.channel.name}")

            # Connect close button to exit fullscreen
            self.video_overlay.close_clicked.connect(self.on_exit_fullscreen)

            # Connect play/pause button
            self.video_overlay.play_pause_btn.clicked.connect(self.toggle_playback)

        self.video_overlay.show()
        logger.info("Video overlay shown")

    # ADD THIS METHOD:
    def toggle_playback(self):
        """Toggle play/pause"""
        if self.player.is_playing():
            self.player.pause()
            self.video_overlay.play_pause_btn.setText("▶ Play")
        else:
            self.player.play()
            self.video_overlay.play_pause_btn.setText("⏸ Pause")

    def closeEvent(self, event):
        """Cleanup when closing"""
        # ADD THIS: Cleanup overlay
        if self.video_overlay:
            self.video_overlay.cleanup()
            self.video_overlay.close()

        # ... existing cleanup code ...
```

### For `EasyModeScreen` (easy_mode_screen.py)

```python
# Add to EasyModeScreen.__init__() after line 169

from src.widgets.video_overlay import SimpleVideoOverlay

class EasyModeScreen(QWidget):
    def __init__(self, channels, logout_callback):
        # ... existing code ...

        # ADD THIS: Create simple watermark overlay
        self.watermark_overlay = None

    def play_channel(self, channel: Channel):
        """Play selected channel"""
        # ... existing playback code ...

        # ADD THIS: Show watermark overlay
        if not self.watermark_overlay:
            self.watermark_overlay = SimpleVideoOverlay(
                parent_widget=self.video_frame,
                watermark_text=f"📺 {channel.name}"
            )
            self.watermark_overlay.show()
        else:
            # Update watermark text for new channel
            self.watermark_overlay.set_text(f"📺 {channel.name}")

    def closeEvent(self, event):
        """Cleanup"""
        # ADD THIS: Cleanup overlay
        if self.watermark_overlay:
            self.watermark_overlay.cleanup()
            self.watermark_overlay.close()

        # ... existing cleanup code ...
```

---

## Advanced: Video Callback Overlay (For Special Cases)

Use this when you need:
- Overlay to be captured in screenshots/recordings
- Overlay embedded in the video stream
- Maximum compatibility with all VLC backends

**Warning**: This is complex and has performance overhead.

### Basic Example

```python
import ctypes
import numpy as np
from PIL import Image, ImageDraw, ImageFont

class VideoPlayerWithBakedOverlay(QWidget):
    def __init__(self):
        super().__init__()

        # Video buffer
        self.buffer = None
        self.video_width = 1280
        self.video_height = 720

        # VLC setup
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()

        self.setup_video_callbacks()

    def setup_video_callbacks(self):
        """Configure VLC to intercept video frames"""

        # Allocate buffer
        buffer_size = self.video_width * self.video_height * 4  # RGBA
        self.buffer = bytearray(buffer_size)
        self.buffer_ptr = ctypes.cast(
            (ctypes.c_ubyte * len(self.buffer)).from_buffer(self.buffer),
            ctypes.c_void_p
        )

        # Define callbacks
        @ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
        def lock(opaque, planes):
            planes[0] = self.buffer_ptr
            return self.buffer_ptr

        @ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
        def unlock(opaque, picture, planes):
            # Draw overlay onto buffer
            self.draw_overlay()

        @ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)
        def display(opaque, picture):
            pass

        # Store to prevent GC
        self.lock_cb = lock
        self.unlock_cb = unlock
        self.display_cb = display

        # Set callbacks
        self.player.video_set_callbacks(lock, unlock, display, None)
        self.player.video_set_format("RV32", self.video_width, self.video_height, self.video_width * 4)

    def draw_overlay(self):
        """Draw overlay graphics onto video buffer"""
        try:
            # Convert buffer to numpy array
            frame = np.frombuffer(self.buffer, dtype=np.uint8).reshape(
                (self.video_height, self.video_width, 4)
            )

            # Convert to PIL Image
            img = Image.fromarray(frame, 'RGBA')
            draw = ImageDraw.Draw(img)

            # Draw watermark
            draw.rectangle(
                [(self.video_width - 200, 10), (self.video_width - 10, 50)],
                fill=(229, 9, 20, 180)
            )
            draw.text((self.video_width - 190, 20), "🎬 IPTV", fill=(255, 255, 255, 255))

            # Copy back to buffer
            modified = np.array(img)
            np.copyto(
                np.frombuffer(self.buffer, dtype=np.uint8).reshape(modified.shape),
                modified
            )
        except Exception as e:
            print(f"Error drawing overlay: {e}")
```

---

## Troubleshooting

### Overlay Not Visible

**Solution 1 (Floating Window):**
```python
# Ensure parent_widget is the actual video frame, not the main window
overlay = VideoOverlay(parent_widget=self.video_frame)  # ✅ Correct
# Not:
overlay = VideoOverlay(parent_widget=self)  # ❌ Wrong

# Check if overlay is actually shown
print(f"Overlay visible: {overlay.isVisible()}")
print(f"Overlay geometry: {overlay.geometry()}")
```

**Solution 5 (VLC Filters):**
```python
# Ensure filters are enabled BEFORE creating media
vlc_instance = vlc.Instance(['--video-filter=marq'])

# Verify filter is active
print(self.player.video_get_spu_count())  # Should show subtitle/overlay tracks
```

### Overlay Positioning Wrong

```python
# Add debug logging to update_geometry_from_parent
def update_geometry_from_parent(self):
    if self.parent_widget and self.parent_widget.isVisible():
        rect = self.parent_widget.geometry()
        pos = self.parent_widget.mapToGlobal(rect.topLeft())
        print(f"Parent geometry: {rect}, Global pos: {pos}")
        self.setGeometry(pos.x(), pos.y(), rect.width(), rect.height())
```

### Performance Issues

```python
# Reduce update frequency
self.position_timer.setInterval(200)  # Update every 200ms instead of 100ms

# Or only update on resize events instead of timer
def resizeEvent(self, event):
    super().resizeEvent(event)
    if self.overlay:
        self.overlay.update_geometry_from_parent()
```

---

## Best Practices

1. **Always cleanup overlays**
   ```python
   def closeEvent(self, event):
       if hasattr(self, 'overlay') and self.overlay:
           self.overlay.cleanup()
           self.overlay.close()
   ```

2. **Use appropriate solution for use case**
   - Interactive controls → Floating Window
   - Static watermark → VLC Filters or Simple Overlay
   - Video recording → Video Callbacks

3. **Test on target platforms**
   - Linux (X11 vs Wayland)
   - Windows (7, 10, 11)
   - macOS

4. **Consider accessibility**
   ```python
   # Allow users to toggle overlays
   settings = {
       'show_watermark': True,
       'show_controls': True,
       'auto_hide_controls': True
   }
   ```

---

## Summary

**For Your IPTV Application:**

✅ **Use Solution 1 (Floating Window)** for:
- Fullscreen mode with controls
- Interactive channel info overlay
- Play/pause/exit buttons

✅ **Use Solution 5 (VLC Filters)** for:
- Simple channel name watermark
- Static logo overlay
- Minimal code changes

❌ **Avoid Solutions 2 & 3**:
- Unreliable across platforms
- Will frustrate users when it randomly fails

🔧 **Consider Solution 4 (Video Callbacks)** if:
- You need to record videos with overlays
- You're implementing picture-in-picture
- You need frame-accurate overlay timing

---

## Additional Resources

- VLC Python Bindings: https://www.olivieraubert.net/vlc/python-ctypes/
- Qt Window Flags: https://doc.qt.io/qt-5/qt.html#WindowType-enum
- Video Filters Guide: https://wiki.videolan.org/Documentation:Modules/marq/

---

*For questions or issues, see `/examples/vlc_overlay_example.py` for working code.*
