# VLC Overlay Fix Guide

## Problem: Overlays Disappear Behind VLC Video

When VLC video plays, Kivy overlay controls disappear behind the video frame.

---

## Why This Happens (Technical Explanation)

### Low-Level Cause

1. **Direct Native Rendering**:
   - `vlc_player.set_hwnd(handle)` gives VLC direct access to the native OS window
   - VLC renders video frames using hardware acceleration (DirectX/OpenGL/Metal)
   - VLC bypasses Kivy's rendering pipeline entirely

2. **Separate Rendering Contexts**:
   ```
   OS Window (Physical Layer)
   ├── VLC renders here ────────┐ (Native DirectX/OpenGL)
   │   [Video Frames]           │
   │                            │ Occludes ⬇
   └──────────────────────────────────────────
   Kivy OpenGL Context (Virtual Layer)
   ├── Overlays render here ────┐ (Kivy's canvas)
   │   [Control Buttons]        │ ← INVISIBLE
   └────────────────────────────┘
   ```

3. **Z-Order Problem**:
   - VLC's native window becomes a top-level rendering surface
   - OS compositing places VLC's surface above Kivy's canvas
   - Even though overlay is "logically" on top in widget tree, it's "physically" below VLC's native rendering

---

## Solutions (From Best to Workaround)

### ✅ Solution 1: Use VLC's Video Filter Overlays (RECOMMENDED)

**How it works**: VLC renders overlay directly into the video stream using video filters.

**Pros**:
- Guaranteed to work cross-platform
- No z-order issues
- Overlays are part of video output

**Cons**:
- Limited styling (text only, basic positioning)
- More complex to update dynamically

**Implementation**:

```python
import vlc

def setup_vlc_with_overlay():
    """Setup VLC with marquee filter for text overlay"""

    vlc_args = [
        '--no-xlib',
        '--sub-source=marq',  # Enable marquee (text overlay)
        '--marq-marquee=Channel Name',  # Initial text
        '--marq-position=8',  # Top center
        '--marq-size=24',  # Font size
        '--marq-color=0xFFFFFF',  # White text
        '--marq-opacity=255',  # Fully opaque
        '--marq-timeout=0',  # Always visible
    ]

    vlc_instance = vlc.Instance(vlc_args)
    vlc_player = vlc_instance.media_player_new()

    return vlc_instance, vlc_player

def update_overlay_text(vlc_player, text):
    """Update overlay text while video plays"""
    vlc_player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, text)

# Example usage:
vlc_instance, vlc_player = setup_vlc_with_overlay()
media = vlc_instance.media_new("http://stream.url")
vlc_player.set_media(media)
vlc_player.play()

# Update text
update_overlay_text(vlc_player, "Now Playing: ESPN HD")
```

**Marquee Options**:
```python
from vlc import VideoMarqueeOption

# Position
vlc_player.video_set_marquee_int(VideoMarqueeOption.Position, 8)  # 0-10
# 0=center, 1=left, 2=right, 4=top, 5=top-left, 6=top-right
# 8=bottom, 9=bottom-left, 10=bottom-right

# Color
vlc_player.video_set_marquee_int(VideoMarqueeOption.Color, 0xFF0000)  # Red

# Size
vlc_player.video_set_marquee_int(VideoMarqueeOption.Size, 32)  # Font size

# Opacity
vlc_player.video_set_marquee_int(VideoMarqueeOption.Opacity, 200)  # 0-255

# Timeout (0 = always visible)
vlc_player.video_set_marquee_int(VideoMarqueeOption.Timeout, 0)

# Text
vlc_player.video_set_marquee_string(VideoMarqueeOption.Text, "Overlay Text")
```

---

### ✅ Solution 2: Disable VLC Hardware Overlay (Windows)

**How it works**: Force VLC to use software rendering that doesn't occlude UI overlays.

**Pros**:
- Kivy overlays work normally
- Simple to implement

**Cons**:
- Higher CPU usage
- May have performance issues on weak hardware

**Implementation**:

```python
import vlc
import sys

def setup_vlc_no_overlay():
    """Setup VLC without hardware overlay"""

    vlc_args = ['--no-xlib']

    if sys.platform == 'win32':
        vlc_args.extend([
            '--no-directx-hw-yuv',  # Disable DirectX hardware YUV
            '--no-overlay',  # Disable video overlay
            '--vout=directdraw',  # Use DirectDraw (not Direct3D)
            '--video-on-top=0',  # Don't force video on top
        ])
    elif sys.platform.startswith('linux'):
        vlc_args.extend([
            '--no-overlay',
            '--vout=xcb_x11',
            '--no-video-on-top',
        ])

    vlc_instance = vlc.Instance(' '.join(vlc_args))
    vlc_player = vlc_instance.media_player_new()

    return vlc_instance, vlc_player
```

---

### ✅ Solution 3: Use canvas.after in Kivy (Partial Fix)

**How it works**: Draw overlay using Kivy's `canvas.after` instruction group.

**Pros**:
- Works within Kivy's rendering pipeline
- Simple to implement

**Cons**:
- May still have z-order issues depending on VLC settings
- Not guaranteed to work on all platforms

**Implementation**:

```python
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle

class OverlayWidget(FloatLayout):
    """Overlay that draws AFTER other content"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # CRITICAL: Use canvas.after, not canvas.before
        with self.canvas.after:
            Color(0, 0, 0, 0.5)  # Semi-transparent black
            self.bg = Rectangle(size=self.size, pos=self.pos)

        self.bind(size=self._update_bg, pos=self._update_bg)

    def _update_bg(self, *args):
        self.bg.size = self.size
        self.bg.pos = self.pos

# Usage in screen:
overlay = OverlayWidget()
overlay.add_widget(Button(text="Control"))
main_layout.add_widget(overlay)  # Add AFTER video widget
```

---

### ✅ Solution 4: Don't Embed VLC - Use External Window

**How it works**: Let VLC open in its own window, don't set window handle.

**Pros**:
- No z-order issues
- VLC has full native controls

**Cons**:
- Less integrated experience
- Separate window to manage

**Implementation**:

```python
import vlc

def play_in_external_vlc(stream_url):
    """Play video in external VLC window"""

    # Don't call set_hwnd() - VLC creates its own window
    vlc_instance = vlc.Instance()
    vlc_player = vlc_instance.media_player_new()

    media = vlc_instance.media_new(stream_url)
    vlc_player.set_media(media)
    vlc_player.play()

    # VLC opens in separate window with built-in controls

    return vlc_instance, vlc_player
```

---

### ✅ Solution 5: Use Logo Filter for Image Overlays

**How it works**: VLC's logo filter composites images onto video.

**Pros**:
- Can display custom images/icons
- Guaranteed to appear on video

**Cons**:
- Static images only (not dynamic UI)
- Must prepare image files

**Implementation**:

```python
import vlc

def setup_vlc_with_logo():
    """Setup VLC with logo overlay"""

    vlc_args = [
        '--no-xlib',
        '--sub-source=logo',  # Enable logo filter
        '--logo-file=/path/to/overlay.png',  # Image file
        '--logo-position=6',  # Top-right
        '--logo-opacity=200',  # Semi-transparent
        '--logo-x=10',  # X offset
        '--logo-y=10',  # Y offset
    ]

    vlc_instance = vlc.Instance(vlc_args)
    vlc_player = vlc_instance.media_player_new()

    return vlc_instance, vlc_player

def change_logo(vlc_player, image_path):
    """Change logo image while playing"""
    from vlc import VideoLogoOption

    vlc_player.video_set_logo_string(VideoLogoOption.logo_file, image_path)
```

---

### ✅ Solution 6: Use Different Video Backend (Alternative)

**How it works**: Replace VLC with GStreamer or FFmpeg backend that integrates better with Kivy.

**Pros**:
- Better integration with UI frameworks
- Overlays work natively

**Cons**:
- Requires different dependencies
- May have codec support issues

**Implementation**:

```python
from kivy.uix.video import Video  # Uses GStreamer or FFmpeg

# Desktop video using Kivy's Video widget
video = Video(
    source='http://stream.url',
    state='play',
    options={'eos': 'loop'}
)

# Overlays work normally with this approach
overlay = Button(text="Control")
layout.add_widget(video)
layout.add_widget(overlay)  # Will appear on top
```

---

## Recommended Solution for IPTV-Saba

For the IPTV-Saba app, I recommend **Solution 1 (VLC Marquee)** combined with **Solution 2 (Disable Hardware Overlay)**:

### Why This Combo?

1. **Marquee for channel name**: Always visible, no z-order issues
2. **Disable hardware overlay**: Kivy controls work
3. **Cross-platform**: Works on Windows and Linux

### Implementation for IPTV-Saba:

```python
# In fullscreen_screen.py

def _setup_vlc_with_working_overlay(self):
    """Setup VLC with working overlays"""

    vlc_args = [
        '--no-xlib',
        '--no-video-title-show',
        '--no-overlay',  # Disable hardware overlay
        '--video-on-top=0',  # Don't force on top
        '--sub-source=marq',  # Enable text overlay
        '--marq-position=8',  # Bottom
        '--marq-size=20',
        '--marq-color=0xFFFFFF',
        '--marq-opacity=200',
    ]

    if sys.platform == 'win32':
        vlc_args.extend([
            '--vout=directdraw',
            '--no-directx-hw-yuv',
        ])

    self.vlc_instance = vlc.Instance(' '.join(vlc_args))
    self.vlc_player = self.vlc_instance.media_player_new()

def play_channel(self, channel):
    """Play channel with working overlay"""

    # Play video
    media = self.vlc_instance.media_new(channel.stream_url)
    self.vlc_player.set_media(media)
    self.vlc_player.play()

    # Set channel name in VLC marquee
    self.vlc_player.video_set_marquee_string(
        vlc.VideoMarqueeOption.Text,
        f"📺 {channel.name}"
    )

    # Kivy overlay controls should now work
    # (because we disabled hardware overlay)
```

---

## Testing the Fix

### Test 1: Verify Overlay Visibility

```python
def test_overlay():
    # Start video
    vlc_player.play()

    # Wait 2 seconds
    time.sleep(2)

    # Check if overlay widget is visible
    print(f"Overlay opacity: {overlay_widget.opacity}")
    print(f"Overlay z-index: {overlay_widget.parent.children.index(overlay_widget)}")

    # Try clicking overlay buttons
    # If buttons work, overlay is on top
```

### Test 2: Marquee Text Visibility

```python
# Set marquee text
vlc_player.video_set_marquee_string(vlc.VideoMarqueeOption.Text, "TEST OVERLAY")

# You should see "TEST OVERLAY" on the video
# If visible, marquee is working
```

---

## Performance Impact

| Solution | CPU Usage | GPU Usage | Compatibility |
|----------|-----------|-----------|---------------|
| Marquee Filter | Low | Low | ✅ Excellent |
| Disable HW Overlay | +10-20% | Low | ✅ Good |
| Logo Filter | Low | Low | ✅ Excellent |
| External Window | Low | Medium | ⚠️ Poor UX |
| Different Backend | Medium | Medium | ⚠️ Codec issues |

---

## Summary

**Best Approach**: Combine multiple solutions:

1. ✅ **Channel name**: Use VLC marquee filter (always visible)
2. ✅ **Control buttons**: Disable hardware overlay + use Kivy widgets
3. ✅ **Watermark**: Use VLC logo filter (if needed)

This gives you:
- Channel name always visible on video
- Working Kivy control buttons
- Cross-platform compatibility
- Low performance overhead

Would you like me to update the actual `fullscreen_screen.py` file with this working solution?
