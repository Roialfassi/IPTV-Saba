"""Player view with integrated overlay and download support."""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from app.ui.widgets.player_overlay import PlayerOverlay


class PlayerView(QWidget):
    """Video player with overlay controls."""
    
    exit_player = pyqtSignal()
    
    def __init__(self, vlc_service, download_service):
        super().__init__()
        self.vlc_service = vlc_service
        self.download_service = download_service
        self.current_channel = None
        self.overlay = None
        
        self._setup_ui()
        self._setup_connections()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: #000000;")
        self.video_frame.setContextMenuPolicy(Qt.CustomContextMenu)
        self.video_frame.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.video_frame)
        
        self.setMouseTracking(True)
        self.video_frame.setMouseTracking(True)
    
    def _setup_connections(self):
        self.vlc_service.playback_started.connect(self._on_playback_started)
        self.vlc_service.playback_error.connect(self._on_playback_error)
    
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, self._attach_player)
    
    def _attach_player(self):
        win_id = int(self.video_frame.winId())
        self.vlc_service.create_player(win_id)
    
    def play_channel(self, channel):
        self.current_channel = channel
        self.vlc_service.play(channel.url)
        
        if not self.overlay:
            self.overlay = PlayerOverlay(self.video_frame)
            self.overlay.close_clicked.connect(self.exit_player.emit)
            self.overlay.fullscreen_clicked.connect(self.toggle_fullscreen)
            self.overlay.download_clicked.connect(self._download_current)
            self.overlay.play_pause_clicked.connect(self._toggle_playback)
        
        self.overlay.set_title(channel.name)
    
    def _on_playback_started(self):
        if self.overlay:
            self.overlay.show()
            self.overlay.set_playing(True)
    
    def _on_playback_error(self, error):
        if self.overlay:
            self.overlay.show_error(f"Playback error: {error}")
    
    def _toggle_playback(self):
        if self.vlc_service.is_playing():
            self.vlc_service.pause()
            if self.overlay:
                self.overlay.set_playing(False)
        else:
            self.vlc_service.pause()
            if self.overlay:
                self.overlay.set_playing(True)
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def _download_current(self):
        if self.current_channel:
            self.download_service.add_download(
                self.current_channel.name,
                self.current_channel.url
            )
            if self.overlay:
                self.overlay.show_notification(f"Download started: {self.current_channel.name}")
    
    def _show_context_menu(self, position):
        menu = QMenu(self)
        
        play_action = QAction("⏸ Pause" if self.vlc_service.is_playing() else "▶ Play", self)
        play_action.triggered.connect(self._toggle_playback)
        menu.addAction(play_action)
        
        fs_action = QAction("⛶ Fullscreen", self)
        fs_action.triggered.connect(self.toggle_fullscreen)
        menu.addAction(fs_action)
        
        menu.addSeparator()
        
        dl_action = QAction("⬇ Download", self)
        dl_action.triggered.connect(self._download_current)
        menu.addAction(dl_action)
        
        menu.addSeparator()
        
        exit_action = QAction("✕ Exit Player", self)
        exit_action.triggered.connect(self.exit_player.emit)
        menu.addAction(exit_action)
        
        menu.exec_(self.video_frame.mapToGlobal(position))
    
    def mouseMoveEvent(self, event):
        if self.overlay:
            self.overlay.show_controls()
        super().mouseMoveEvent(event)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self._toggle_playback()
        elif event.key() in (Qt.Key_F, Qt.Key_F11):
            self.toggle_fullscreen()
        elif event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.exit_player.emit()
        elif event.key() == Qt.Key_D:
            self._download_current()
        else:
            super().keyPressEvent(event)
    
    def stop(self):
        self.vlc_service.stop()
    
    def cleanup(self):
        if self.overlay:
            self.overlay.cleanup()
        self.stop()
