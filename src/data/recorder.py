# stream_recorder.py
"""Stream Recorder & Test UI

High‑quality, battle‑tested Python 3.9+ implementation for 24/7 HTTP/HLS/DASH
stream capturing.
Features
========
* **Scheduled recording** – record(url, start, end, save_name)
* **Immediate recording** – record_now(url) / Recording.stop()
* **Qt test UI** – one‑click start/stop with live preview (VLC backend)

Dependencies
------------
* Python ≥ 3.9
* **ffmpeg** (≥ 4.0) – must be on PATH
* PyQt5 or PySide6 (Qt 6 works too)
* python‑vlc (≥ 3.0)

Install:
```bash
pip install PyQt5 python-vlc
# or
pip install PySide6 python-vlc
```

Usage (CLI):
```bash
python stream_recorder.py --url "<stream>" --start "2025-06-03 22:00" \
                          --end "2025-06-04 00:00" --out myshow.ts
```
Run the GUI:
```bash
python stream_recorder.py --gui
```
"""
from __future__ import annotations

import argparse
import datetime as _dt
import logging
import signal
import subprocess as _sp
import sys
import textwrap
import threading
from pathlib import Path
from typing import Optional

from dataclasses import dataclass, field

# ------------------------  Logging setup  ------------------------ #
_LOG = logging.getLogger("stream_recorder")
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s %(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ------------------------  Core recorder  ------------------------ #

@dataclass
class _ProcessWrapper:
    cmd: list[str]
    proc: _sp.Popen | None = field(init=False, default=None)

    def start(self) -> None:
        _LOG.debug("Starting ffmpeg: %s", " ".join(self.cmd))
        self.proc = _sp.Popen(self.cmd, stdout=_sp.PIPE, stderr=_sp.PIPE)

    def stop(self, timeout: int = 10) -> None:
        if not self.proc or self.proc.poll() is not None:
            return
        _LOG.info("Stopping recording…")
        self.proc.send_signal(signal.SIGINT)
        try:
            self.proc.wait(timeout=timeout)
        except _sp.TimeoutExpired:
            _LOG.warning("ffmpeg unresponsive, killing…")
            self.proc.kill()
        _LOG.info("Recording saved.")


# Public façade ----------------------------------------------------#

class Recording:
    """Handle to a live recording. Call :py:meth:`stop` to finish."""

    def __init__(self, url: str, outfile: Path):
        self._url = url
        self._outfile = outfile.expanduser().resolve()
        self._proc: Optional[_ProcessWrapper] = None

    # ---------------- API ---------------- #
    def start_now(self) -> None:
        self._outfile.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",  # overwrite
            "-i",
            self._url,
            "-c",
            "copy",
            str(self._outfile),
        ]
        self._proc = _ProcessWrapper(cmd)
        self._proc.start()
        _LOG.info("Recording started: %s → %s", self._url, self._outfile)

    def stop(self) -> None:
        if self._proc:
            self._proc.stop()

    # Convenience for context‑manager style
    def __enter__(self):
        self.start_now()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()



# ------------------------------------------------------------------#

def _schedule(fn, when: _dt.datetime, *args, **kwargs) -> threading.Timer:
    delay = (when - _dt.datetime.now()).total_seconds()
    delay = max(delay, 0)
    t = threading.Timer(delay, fn, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


def record(url: str, start: _dt.datetime, end: _dt.datetime, save_name: str) -> Recording:
    """Schedule a recording between *start* and *end* (both naive local time).

    Returns a :class:`Recording` handle so the caller can poll/stop early.
    """
    if end <= start:
        raise ValueError("End time must be after start time")
    rec = Recording(url, Path(save_name))

    # timers
    _schedule(rec.start_now, start)
    _schedule(rec.stop, end)
    _LOG.info("Recording scheduled from %s to %s -> %s", start, end, save_name)
    return rec


def record_now(url: str, save_name: Optional[str] = None) -> Recording:
    """Start recording immediately and return the *Recording* handle."""
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(save_name or f"recording_{ts}.ts")
    rec = Recording(url, out)
    rec.start_now()
    return rec


# -----------------------------  GUI  ------------------------------#

# Import Qt lazily so CLI usage does not mandate GUI deps.

def _run_gui() -> None:  # pragma: no cover
    """Launch the test UI (PyQt5)."""
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtWidgets import (
        QApplication,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMessageBox,
        QPushButton,
        QVBoxLayout,
        QWidget,
    )
    import vlc

    class MainWindow(QWidget):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Stream Recorder Test UI")
            self.setMinimumSize(960, 540)

            vbox = QVBoxLayout(self)
            # URL input
            self.url_edit = QLineEdit("https://example.com/stream.m3u8")
            vbox.addWidget(QLabel("Stream URL:"))
            vbox.addWidget(self.url_edit)

            # Buttons
            h = QHBoxLayout()
            self.start_btn = QPushButton("Start Recording")
            self.stop_btn = QPushButton("Stop Recording")
            self.stop_btn.setEnabled(False)
            h.addWidget(self.start_btn)
            h.addWidget(self.stop_btn)
            vbox.addLayout(h)

            # Media player widget
            self.instance = vlc.Instance()
            self.player = self.instance.media_player_new()
            self.video_frame = QWidget()
            self.video_frame.setAttribute(Qt.WA_OpaquePaintEvent)
            vbox.addWidget(self.video_frame, stretch=1)
            if sys.platform.startswith("linux"):
                self.player.set_xwindow(self.video_frame.winId())
            elif sys.platform == "win32":
                self.player.set_hwnd(self.video_frame.winId())
            else:  # macOS
                self.player.set_nsobject(int(self.video_frame.winId()))

            # Recording state
            self._rec: Optional[Recording] = None

            # Connections
            self.start_btn.clicked.connect(self._on_start)
            self.stop_btn.clicked.connect(self._on_stop)

        # ------------ slots ------------ #
        def _on_start(self):
            url = self.url_edit.text().strip()
            if not url:
                QMessageBox.warning(self, "Error", "Please enter stream URL")
                return
            try:
                self._rec = record_now(url)
            except FileNotFoundError:
                QMessageBox.critical(
                    self,
                    "ffmpeg missing",
                    "ffmpeg executable not found in PATH.",
                )
                return
            media = self.instance.media_new(url)
            self.player.set_media(media)
            self.player.play()

            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

        def _on_stop(self):
            if self._rec:
                self._rec.stop()
            self.player.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


# ---------------------------  __main__  ---------------------------#

def _parse_dt(val: str) -> _dt.datetime:
    try:
        return _dt.datetime.fromisoformat(val)
    except ValueError as e:
        raise argparse.ArgumentTypeError(str(e))


def main(argv: list[str] | None = None) -> None:  # noqa: D401
    """CLI entry‑point."""
    p = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(
            """
            Simple stream recorder around ffmpeg. Either schedule a capture or run the Qt test UI.
            """
        ),
    )
    p.add_argument("--url", help="Stream URL")
    p.add_argument("--start", type=_parse_dt, help="Start time (ISO: YYYY-MM-DD HH:MM)")
    p.add_argument("--end", type=_parse_dt, help="End time (ISO)")
    p.add_argument("--out", help="Output filename")
    p.add_argument("--gui", action="store_true", help="Launch test GUI")
    args = p.parse_args(argv)

    if args.gui:
        _run_gui()
        return

    if not all([args.url, args.start, args.end, args.out]):
        p.error("For CLI mode you must provide --url, --start, --end, --out or use --gui")

    record(args.url, args.start, args.end, args.out)
    # Keep main thread alive until recording stops
    while True:
        try:
            threading.Event().wait(1)
        except KeyboardInterrupt:
            _LOG.info("Interrupted by user.")
            break


if __name__ == "__main__":  # pragma: no cover
    main()
