"""Downloads manager dialog."""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QListWidget, QPushButton, QProgressBar, QWidget, QListWidgetItem)
from PyQt5.QtCore import Qt


class DownloadItemWidget(QWidget):
    """Widget for download list item."""
    
    def __init__(self, task):
        super().__init__()
        self.task = task
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        header = QHBoxLayout()
        
        title = QLabel(task.name)
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(title)
        
        header.addStretch()
        
        status = QLabel(task.status.value.upper())
        status.setStyleSheet("color: #e50914; font-weight: bold;")
        header.addWidget(status)
        
        layout.addLayout(header)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(int(task.progress))
        layout.addWidget(self.progress_bar)
        
        info = QHBoxLayout()
        
        self.speed_label = QLabel(task.speed or "Initializing...")
        info.addWidget(self.speed_label)
        
        info.addStretch()
        
        self.eta_label = QLabel(task.eta)
        info.addWidget(self.eta_label)
        
        layout.addLayout(info)


class DownloadsDialog(QDialog):
    """Downloads manager dialog."""
    
    def __init__(self, download_service, parent=None):
        super().__init__(parent)
        self.download_service = download_service
        
        self.setWindowTitle("Downloads")
        self.setMinimumSize(700, 500)
        
        self._setup_ui()
        self._setup_connections()
        self._load_downloads()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        
        title = QLabel("Downloads")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        header.addWidget(title)
        
        header.addStretch()
        
        clear_btn = QPushButton("Clear Completed")
        clear_btn.clicked.connect(self._clear_completed)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        self.download_list = QListWidget()
        layout.addWidget(self.download_list)
        
        footer = QHBoxLayout()
        
        self.status_label = QLabel("0 active downloads")
        footer.addWidget(self.status_label)
        
        footer.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)
        
        layout.addLayout(footer)
    
    def _setup_connections(self):
        self.download_service.download_added.connect(self._on_download_added)
        self.download_service.download_progress.connect(self._on_download_progress)
        self.download_service.download_completed.connect(self._on_download_completed)
        self.download_service.download_failed.connect(self._on_download_failed)
    
    def _load_downloads(self):
        self.download_list.clear()
        
        tasks = self.download_service.get_all_tasks()
        
        for task in tasks:
            self._add_download_item(task)
        
        self._update_status()
    
    def _add_download_item(self, task):
        item = QListWidgetItem(self.download_list)
        widget = DownloadItemWidget(task)
        
        item.setSizeHint(widget.sizeHint())
        self.download_list.addItem(item)
        self.download_list.setItemWidget(item, widget)
    
    def _on_download_added(self, task):
        self._add_download_item(task)
        self._update_status()
    
    def _on_download_progress(self, task_id, progress, speed, eta):
        task = self.download_service.get_task(task_id)
        if task:
            for i in range(self.download_list.count()):
                item = self.download_list.item(i)
                widget = self.download_list.itemWidget(item)
                if widget and widget.task.id == task_id:
                    widget.progress_bar.setValue(int(progress))
                    widget.speed_label.setText(speed or "Downloading...")
                    widget.eta_label.setText(eta)
                    break
    
    def _on_download_completed(self, task_id):
        self._update_status()
    
    def _on_download_failed(self, task_id, error):
        self._update_status()
    
    def _update_status(self):
        tasks = self.download_service.get_all_tasks()
        active = sum(1 for t in tasks if t.status.value == "downloading")
        self.status_label.setText(f"{active} active downloads")
    
    def _clear_completed(self):
        self._load_downloads()
