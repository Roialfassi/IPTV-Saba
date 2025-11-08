# VLC Overlay Quick Start

## The Problem
Overlays (controls, watermarks) disappear behind VLC video because VLC uses hardware rendering that bypasses Qt's widget system.

## The Solution (2 Minutes)

### Option 1: Interactive Overlay with Controls ⭐ RECOMMENDED

```python
from src.widgets.video_overlay import VideoOverlay

# In your video player class __init__:
self.overlay = None

# When starting video:
def start_playback(self):
    # ... your existing VLC playback code ...

    # Add overlay
    if not self.overlay:
        self.overlay = VideoOverlay(
            parent_widget=self.video_frame,  # Your QFrame with VLC
            show_watermark=True,
            show_controls=True
        )
        self.overlay.close_clicked.connect(self.close)

    self.overlay.show()

# When closing:
def closeEvent(self, event):
    if self.overlay:
        self.overlay.cleanup()
        self.overlay.close()
```

### Option 2: Simple Watermark Only

```python
from src.widgets.video_overlay import SimpleVideoOverlay

# When starting video:
watermark = SimpleVideoOverlay(
    parent_widget=self.video_frame,
    watermark_text="🎬 Your Channel"
)
watermark.show()
```

### Option 3: VLC Built-in Filter (Static Text)

```python
# When creating VLC instance:
vlc_args = [
    '--video-filter=marq',
    '--marq-marquee=🎬 Your Channel',
    '--marq-position=10',  # Bottom-right
    '--marq-opacity=200'
]
self.vlc_instance = vlc.Instance(vlc_args)
```

## Examples

Run working examples:
```bash
python examples/vlc_overlay_example.py
python examples/vlc_overlay_advanced.py
```

## Full Documentation

See `docs/VLC_OVERLAY_GUIDE.md` for:
- Technical explanation of why this happens
- All 5 solution approaches
- Integration examples for your codebase
- Troubleshooting guide

## Quick Customization

```python
# Change watermark text
overlay.set_watermark_text("📺 New Channel")

# Change button text
overlay.play_pause_btn.setText("▶ Resume")

# Update colors
overlay.watermark_label.setStyleSheet("""
    background-color: rgba(0, 100, 200, 180);
    color: white;
""")
```

---

**That's it!** Your overlay will now stay visible above the VLC video player.
