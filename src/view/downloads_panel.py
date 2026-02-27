"""
Downloads & Recordings Panel for IPTV-Saba

Collapsible panel showing all download/recording activity with
per-item progress bars, speed/ETA, pause/resume/cancel controls,
and completed items history.
"""

import logging
import os
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QScrollArea, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal

logger = logging.getLogger(__name__)


def _format_size(bytes_val: int) -> str:
    """Format bytes to human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 * 1024 * 1024:
        return f"{bytes_val / (1024 * 1024):.1f} MB"
    else:
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"


def _format_eta(seconds: float) -> str:
    """Format seconds to human-readable ETA string."""
    if seconds <= 0:
        return ""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"


def _format_elapsed(seconds: int) -> str:
    """Format seconds to HH:MM:SS."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# ========================== Item Widgets ==========================

ITEM_STYLE = """
    QWidget#itemWidget {
        background-color: #222;
        border-radius: 6px;
        padding: 4px;
    }
"""

SMALL_BUTTON_STYLE = """
    QPushButton {
        background-color: #444;
        color: #ccc;
        border: none;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #555;
        color: #fff;
    }
    QPushButton:pressed {
        background-color: #333;
    }
"""

STOP_BUTTON_STYLE = """
    QPushButton {
        background-color: #8B0000;
        color: #fff;
        border: none;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
    QPushButton:hover {
        background-color: #A00000;
    }
"""


class DownloadItemWidget(QWidget):
    """Widget showing an active download with progress, speed, and controls."""

    pause_clicked = pyqtSignal(str)
    resume_clicked = pyqtSignal(str)
    cancel_clicked = pyqtSignal(str)

    def __init__(self, download_id: str, channel_name: str, parent=None):
        super().__init__(parent)
        self.download_id = download_id
        self._paused = False
        self.setObjectName("itemWidget")
        self.setStyleSheet(ITEM_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Row 1: name + buttons
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        self.name_label = QLabel(channel_name)
        self.name_label.setStyleSheet("color: #fff; font-size: 12px; font-weight: 600; background: transparent;")
        row1.addWidget(self.name_label, 1)

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setStyleSheet(SMALL_BUTTON_STYLE)
        self.pause_btn.setFixedWidth(55)
        self.pause_btn.clicked.connect(self._on_pause_resume)
        row1.addWidget(self.pause_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(SMALL_BUTTON_STYLE)
        self.cancel_btn.setFixedWidth(55)
        self.cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self.download_id))
        row1.addWidget(self.cancel_btn)

        layout.addLayout(row1)

        # Row 2: progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #333;
            }
            QProgressBar::chunk {
                background-color: #E50914;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Row 3: status text (size, speed, ETA)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 11px; background: transparent;")
        layout.addWidget(self.status_label)

    def _on_pause_resume(self):
        if self._paused:
            self.resume_clicked.emit(self.download_id)
        else:
            self.pause_clicked.emit(self.download_id)

    def update_progress(self, bytes_downloaded: int, total_bytes: int):
        if total_bytes > 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(int(bytes_downloaded / total_bytes * 100))
        else:
            self.progress_bar.setRange(0, 0)  # indeterminate

        size_text = _format_size(bytes_downloaded)
        if total_bytes > 0:
            size_text += f" / {_format_size(total_bytes)}"
        self.status_label.setText(size_text)

    def update_speed(self, speed_mbps: float, eta_seconds: float):
        current = self.status_label.text()
        # Keep size info, append speed and ETA
        parts = current.split(" | ") if current else [""]
        size_part = parts[0]
        speed_text = f"{speed_mbps:.1f} MB/s" if speed_mbps > 0 else ""
        eta_text = _format_eta(eta_seconds) if eta_seconds > 0 else ""

        info_parts = [size_part]
        if speed_text:
            info_parts.append(speed_text)
        if eta_text:
            info_parts.append(f"ETA {eta_text}")
        self.status_label.setText(" | ".join(info_parts))

    def mark_paused(self):
        self._paused = True
        self.pause_btn.setText("Resume")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #333;
            }
            QProgressBar::chunk {
                background-color: #886600;
                border-radius: 3px;
            }
        """)

    def mark_resumed(self):
        self._paused = False
        self.pause_btn.setText("Pause")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #333;
            }
            QProgressBar::chunk {
                background-color: #E50914;
                border-radius: 3px;
            }
        """)


class RecordingItemWidget(QWidget):
    """Widget showing an active recording with elapsed time and stop button."""

    stop_clicked = pyqtSignal(str)

    def __init__(self, recording_id: str, channel_name: str, parent=None):
        super().__init__(parent)
        self.recording_id = recording_id
        self.setObjectName("itemWidget")
        self.setStyleSheet(ITEM_STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Recording indicator
        self.indicator = QLabel("\u23FA")
        self.indicator.setStyleSheet("color: #E50914; font-size: 16px; background: transparent;")
        self.indicator.setFixedWidth(20)
        layout.addWidget(self.indicator)

        # Name
        self.name_label = QLabel(channel_name)
        self.name_label.setStyleSheet("color: #fff; font-size: 12px; font-weight: 600; background: transparent;")
        layout.addWidget(self.name_label, 1)

        # Elapsed time
        self.elapsed_label = QLabel("00:00")
        self.elapsed_label.setStyleSheet("color: #E50914; font-size: 12px; font-weight: 600; background: transparent;")
        layout.addWidget(self.elapsed_label)

        # Stop button
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setStyleSheet(STOP_BUTTON_STYLE)
        self.stop_btn.setFixedWidth(50)
        self.stop_btn.clicked.connect(lambda: self.stop_clicked.emit(self.recording_id))
        layout.addWidget(self.stop_btn)

    def update_elapsed(self, seconds: int):
        self.elapsed_label.setText(_format_elapsed(seconds))


class QueuedItemWidget(QWidget):
    """Widget showing a queued download."""

    cancel_clicked = pyqtSignal(str)

    def __init__(self, download_id: str, channel_name: str, position: int, parent=None):
        super().__init__(parent)
        self.download_id = download_id
        self.setObjectName("itemWidget")
        self.setStyleSheet(ITEM_STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        self.name_label = QLabel(channel_name)
        self.name_label.setStyleSheet("color: #aaa; font-size: 12px; background: transparent;")
        layout.addWidget(self.name_label, 1)

        self.position_label = QLabel(f"#{position} in queue")
        self.position_label.setStyleSheet("color: #666; font-size: 11px; background: transparent;")
        layout.addWidget(self.position_label)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(SMALL_BUTTON_STYLE)
        cancel_btn.setFixedWidth(55)
        cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self.download_id))
        layout.addWidget(cancel_btn)


class CompletedItemWidget(QWidget):
    """Widget showing a completed/failed download or recording."""

    open_folder_clicked = pyqtSignal(str)   # filepath
    retry_clicked = pyqtSignal(str, str, str)  # id, channel_name, url

    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        self._data = item_data
        self.setObjectName("itemWidget")
        self.setStyleSheet(ITEM_STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # State icon
        state = item_data.get('state', 'completed')
        if state == 'completed':
            icon_text = "\u2714"
            icon_color = "#4CAF50"
        elif state == 'failed':
            icon_text = "\u2716"
            icon_color = "#E50914"
        elif state == 'cancelled':
            icon_text = "\u2013"
            icon_color = "#888"
        else:
            icon_text = "\u2022"
            icon_color = "#888"

        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet(f"color: {icon_color}; font-size: 14px; background: transparent;")
        icon_label.setFixedWidth(16)
        layout.addWidget(icon_label)

        # Name + info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(1)
        info_layout.setContentsMargins(0, 0, 0, 0)

        name_label = QLabel(item_data.get('channel_name', 'Unknown'))
        name_label.setStyleSheet("color: #ccc; font-size: 11px; background: transparent;")
        info_layout.addWidget(name_label)

        detail_parts = []
        item_type = item_data.get('item_type', 'download')
        detail_parts.append(item_type.capitalize())

        if item_data.get('bytes_total', 0) > 0:
            detail_parts.append(_format_size(item_data['bytes_total']))
        if item_data.get('duration_seconds', 0) > 0:
            detail_parts.append(_format_elapsed(item_data['duration_seconds']))

        completed_at = item_data.get('completed_at')
        if completed_at and isinstance(completed_at, datetime):
            detail_parts.append(completed_at.strftime("%H:%M"))

        if item_data.get('error_message'):
            detail_parts.append(item_data['error_message'][:40])

        detail_label = QLabel(" | ".join(detail_parts))
        detail_label.setStyleSheet("color: #666; font-size: 10px; background: transparent;")
        info_layout.addWidget(detail_label)

        layout.addLayout(info_layout, 1)

        # Action button
        filepath = item_data.get('filepath', '')
        if state == 'completed' and filepath and os.path.exists(filepath):
            open_btn = QPushButton("Open")
            open_btn.setStyleSheet(SMALL_BUTTON_STYLE)
            open_btn.setFixedWidth(48)
            open_btn.clicked.connect(lambda: self.open_folder_clicked.emit(filepath))
            layout.addWidget(open_btn)
        elif state == 'failed':
            retry_btn = QPushButton("Retry")
            retry_btn.setStyleSheet(SMALL_BUTTON_STYLE)
            retry_btn.setFixedWidth(48)
            retry_btn.clicked.connect(lambda: self.retry_clicked.emit(
                item_data.get('item_id', ''),
                item_data.get('channel_name', ''),
                item_data.get('url', ''),
            ))
            layout.addWidget(retry_btn)


# ========================== Section Widget ==========================

class SectionWidget(QWidget):
    """A labeled section in the panel that auto-hides when empty."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(2)

        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            "color: #666; font-size: 10px; font-weight: bold; "
            "text-transform: uppercase; background: transparent; padding-left: 4px;"
        )
        layout.addWidget(self._title_label)

        self._items_layout = QVBoxLayout()
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(3)
        layout.addLayout(self._items_layout)

        self._item_count = 0
        self.setVisible(False)

    def add_item(self, widget: QWidget):
        self._items_layout.addWidget(widget)
        self._item_count += 1
        self.setVisible(True)

    def remove_item(self, widget: QWidget):
        self._items_layout.removeWidget(widget)
        widget.deleteLater()
        self._item_count -= 1
        if self._item_count <= 0:
            self._item_count = 0
            self.setVisible(False)

    def clear(self):
        while self._items_layout.count():
            item = self._items_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._item_count = 0
        self.setVisible(False)

    @property
    def count(self):
        return self._item_count


# ========================== Main Panel ==========================

class DownloadsPanel(QWidget):
    """
    Collapsible panel showing all download and recording activity.

    Emits signals for user actions that the parent screen connects
    to the DownloadRecordManager.
    """

    # Action signals
    pause_download_requested = pyqtSignal(str)
    resume_download_requested = pyqtSignal(str)
    cancel_download_requested = pyqtSignal(str)
    stop_recording_requested = pyqtSignal(str)
    open_folder_requested = pyqtSignal(str)    # filepath
    retry_download_requested = pyqtSignal(str, str, str)  # id, channel_name, url

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False
        self._download_widgets: dict = {}   # download_id -> DownloadItemWidget
        self._recording_widgets: dict = {}  # recording_id -> RecordingItemWidget
        self._queued_widgets: dict = {}     # download_id -> QueuedItemWidget

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toggle button
        self.toggle_button = QPushButton("\u25BC Downloads & Recordings")
        self.toggle_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: #888;
                border: none;
                border-top: 1px solid #333;
                padding: 6px 12px;
                font-size: 12px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #222;
                color: #ccc;
            }
        """)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.clicked.connect(self._toggle)
        layout.addWidget(self.toggle_button)

        # Collapsible content area
        self._content_widget = QWidget()
        self._content_widget.setStyleSheet("background-color: #1a1a1a;")

        content_layout = QVBoxLayout(self._content_widget)
        content_layout.setContentsMargins(8, 4, 8, 8)
        content_layout.setSpacing(4)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #1a1a1a;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #444;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self._scroll_layout = QVBoxLayout(scroll_content)
        self._scroll_layout.setContentsMargins(0, 0, 0, 0)
        self._scroll_layout.setSpacing(6)

        # Sections
        self._downloads_section = SectionWidget("Active Downloads")
        self._scroll_layout.addWidget(self._downloads_section)

        self._recordings_section = SectionWidget("Active Recordings")
        self._scroll_layout.addWidget(self._recordings_section)

        self._queued_section = SectionWidget("Queued")
        self._scroll_layout.addWidget(self._queued_section)

        self._completed_section = SectionWidget("Completed")
        self._scroll_layout.addWidget(self._completed_section)

        self._scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        content_layout.addWidget(scroll)

        self._content_widget.setVisible(False)
        layout.addWidget(self._content_widget)

        # Panel always visible (toggle button shown), content starts collapsed

    def _toggle(self):
        self._expanded = not self._expanded
        self._content_widget.setVisible(self._expanded)
        self._update_toggle_text()

    def _update_toggle_text(self):
        dl_count = len(self._download_widgets)
        rec_count = len(self._recording_widgets)
        q_count = len(self._queued_widgets)

        parts = []
        if dl_count:
            parts.append(f"{dl_count} download{'s' if dl_count > 1 else ''}")
        if rec_count:
            parts.append(f"{rec_count} recording{'s' if rec_count > 1 else ''}")
        if q_count:
            parts.append(f"{q_count} queued")

        arrow = "\u25B2" if self._expanded else "\u25BC"

        if parts:
            summary = " | ".join(parts)
            self.toggle_button.setText(f"{arrow} Downloads & Recordings  ({summary})")
        else:
            self.toggle_button.setText(f"{arrow} Downloads & Recordings")

    def _ensure_visible(self):
        """Auto-expand the panel content when items are added."""
        pass  # Panel toggle is always visible; auto-expand handled in add methods

    # ========================== Add/remove items ==========================

    def add_active_download(self, download_id: str, channel_name: str):
        """Add a new active download to the panel."""
        if download_id in self._download_widgets:
            return

        widget = DownloadItemWidget(download_id, channel_name)
        widget.pause_clicked.connect(self.pause_download_requested.emit)
        widget.resume_clicked.connect(self.resume_download_requested.emit)
        widget.cancel_clicked.connect(self.cancel_download_requested.emit)

        self._download_widgets[download_id] = widget
        self._downloads_section.add_item(widget)
        self._ensure_visible()
        self._update_toggle_text()

        # Auto-expand when a download starts
        if not self._expanded:
            self._expanded = True
            self._content_widget.setVisible(True)
            self._update_toggle_text()

    def remove_download(self, download_id: str):
        """Remove a download from the active section."""
        widget = self._download_widgets.pop(download_id, None)
        if widget:
            self._downloads_section.remove_item(widget)
            self._update_toggle_text()
            self._check_auto_hide()

    def add_active_recording(self, recording_id: str, channel_name: str):
        """Add a new active recording to the panel."""
        if recording_id in self._recording_widgets:
            return

        widget = RecordingItemWidget(recording_id, channel_name)
        widget.stop_clicked.connect(self.stop_recording_requested.emit)

        self._recording_widgets[recording_id] = widget
        self._recordings_section.add_item(widget)
        self._ensure_visible()
        self._update_toggle_text()

        # Auto-expand
        if not self._expanded:
            self._expanded = True
            self._content_widget.setVisible(True)
            self._update_toggle_text()

    def remove_recording(self, recording_id: str):
        """Remove a recording from the active section."""
        widget = self._recording_widgets.pop(recording_id, None)
        if widget:
            self._recordings_section.remove_item(widget)
            self._update_toggle_text()
            self._check_auto_hide()

    def add_queued_download(self, download_id: str, channel_name: str, position: int):
        """Add a queued download to the panel."""
        if download_id in self._queued_widgets:
            return

        widget = QueuedItemWidget(download_id, channel_name, position)
        widget.cancel_clicked.connect(self.cancel_download_requested.emit)

        self._queued_widgets[download_id] = widget
        self._queued_section.add_item(widget)
        self._ensure_visible()
        self._update_toggle_text()

    def remove_queued_download(self, download_id: str):
        """Remove a queued download from the panel."""
        widget = self._queued_widgets.pop(download_id, None)
        if widget:
            self._queued_section.remove_item(widget)
            self._update_toggle_text()
            self._check_auto_hide()

    def promote_queued_to_active(self, download_id: str, channel_name: str):
        """Move a download from queued to active (when slot opens)."""
        self.remove_queued_download(download_id)
        self.add_active_download(download_id, channel_name)

    def add_completed_item(self, item_data: dict):
        """Add a completed/failed/cancelled item to the completed section."""
        widget = CompletedItemWidget(item_data)
        widget.open_folder_clicked.connect(self.open_folder_requested.emit)
        widget.retry_clicked.connect(self.retry_download_requested.emit)

        self._completed_section.add_item(widget)

        # Cap at 20 visible completed items
        if self._completed_section.count > 20:
            # Remove oldest (last child in layout)
            items_layout = self._completed_section._items_layout
            if items_layout.count() > 20:
                old_item = items_layout.takeAt(items_layout.count() - 1)
                old_widget = old_item.widget()
                if old_widget:
                    old_widget.deleteLater()
                    self._completed_section._item_count -= 1

    # ========================== Update items ==========================

    def update_download_progress(self, download_id: str, bytes_downloaded: int, total_bytes: int):
        """Update progress for an active download."""
        widget = self._download_widgets.get(download_id)
        if widget:
            widget.update_progress(bytes_downloaded, total_bytes)

    def update_download_speed(self, download_id: str, speed_mbps: float, eta_seconds: float):
        """Update speed/ETA for an active download."""
        widget = self._download_widgets.get(download_id)
        if widget:
            widget.update_speed(speed_mbps, eta_seconds)

    def update_recording_elapsed(self, recording_id: str, elapsed_seconds: int):
        """Update elapsed time for an active recording."""
        widget = self._recording_widgets.get(recording_id)
        if widget:
            widget.update_elapsed(elapsed_seconds)

    def mark_download_paused(self, download_id: str):
        """Mark a download as paused in the panel."""
        widget = self._download_widgets.get(download_id)
        if widget:
            widget.mark_paused()

    def mark_download_resumed(self, download_id: str):
        """Mark a download as resumed in the panel."""
        widget = self._download_widgets.get(download_id)
        if widget:
            widget.mark_resumed()

    # ========================== Helpers ==========================

    def _check_auto_hide(self):
        """Collapse the content area if there are no items at all."""
        has_items = (
            len(self._download_widgets) > 0
            or len(self._recording_widgets) > 0
            or len(self._queued_widgets) > 0
            or self._completed_section.count > 0
        )
        if not has_items:
            self._expanded = False
            self._content_widget.setVisible(False)
            self._update_toggle_text()

    def get_summary_text(self) -> str:
        """Get summary text for external status bar."""
        parts = []
        dl = len(self._download_widgets)
        rec = len(self._recording_widgets)
        q = len(self._queued_widgets)
        if dl:
            parts.append(f"{dl} download{'s' if dl > 1 else ''}")
        if rec:
            parts.append(f"{rec} recording{'s' if rec > 1 else ''}")
        if q:
            parts.append(f"{q} queued")
        return ", ".join(parts) if parts else ""
