"""Main channel browser view."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QListWidget, QPushButton, QComboBox, QSplitter)
from PyQt5.QtCore import Qt, pyqtSignal
from app.models.channel import Channel


class MainView(QWidget):
    """Channel browser and selection."""
    
    play_channel = pyqtSignal(Channel)
    logout_requested = pyqtSignal()
    downloads_requested = pyqtSignal()
    
    def __init__(self, playlist_service):
        super().__init__()
        self.playlist_service = playlist_service
        self.current_profile = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        
        title = QLabel("IPTV Saba")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #e50914;")
        header.addWidget(title)
        
        header.addStretch()
        
        downloads_btn = QPushButton("⬇ Downloads")
        downloads_btn.clicked.connect(self.downloads_requested.emit)
        header.addWidget(downloads_btn)
        
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout_requested.emit)
        header.addWidget(logout_btn)
        
        layout.addLayout(header)
        
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search channels...")
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        
        self.group_combo = QComboBox()
        self.group_combo.addItem("All Groups")
        self.group_combo.currentTextChanged.connect(self._on_group_changed)
        search_layout.addWidget(self.group_combo)
        
        layout.addLayout(search_layout)
        
        self.channel_list = QListWidget()
        self.channel_list.itemDoubleClicked.connect(self._on_channel_double_clicked)
        layout.addWidget(self.channel_list)
        
        play_btn = QPushButton("▶ Play Channel")
        play_btn.clicked.connect(self._on_play_clicked)
        layout.addWidget(play_btn)
    
    def load_data(self, profile: dict):
        """Load data from profile."""
        self.current_profile = profile
        
        self.group_combo.clear()
        self.group_combo.addItem("All Groups")
        
        groups = self.playlist_service.get_group_names()
        self.group_combo.addItems(groups)
        
        self._load_channels()
    
    def _load_channels(self, channels=None):
        """Load channels into list."""
        self.channel_list.clear()
        
        if channels is None:
            channels = self.playlist_service.channels
        
        for channel in channels:
            self.channel_list.addItem(f"{channel.name} ({channel.group})")
    
    def _on_search(self, text):
        """Handle search."""
        if text:
            results = self.playlist_service.search(text)
            self._load_channels(results)
        else:
            self._on_group_changed(self.group_combo.currentText())
    
    def _on_group_changed(self, group_name):
        """Handle group selection."""
        self.search_input.clear()
        
        if group_name == "All Groups":
            self._load_channels()
        else:
            channels = self.playlist_service.get_channels_in_group(group_name)
            self._load_channels(channels)
    
    def _on_channel_double_clicked(self, item):
        """Handle channel double click."""
        self._play_selected()
    
    def _on_play_clicked(self):
        """Handle play button click."""
        self._play_selected()
    
    def _play_selected(self):
        """Play selected channel."""
        current_item = self.channel_list.currentItem()
        if not current_item:
            return
        
        channel_name = current_item.text().split(" (")[0]
        
        for channel in self.playlist_service.channels:
            if channel.name == channel_name:
                self.play_channel.emit(channel)
                return
