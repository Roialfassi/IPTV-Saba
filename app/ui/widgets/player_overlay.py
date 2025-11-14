"""Floating player overlay with controls."""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont


class PlayerOverlay(QWidget):
    """Transparent overlay for video player controls."""
    
    close_clicked = pyqtSignal()
    fullscreen_clicked = pyqtSignal()
    download_clicked = pyqtSignal()
    play_pause_clicked = pyqtSignal()
    
    def __init__(self, parent_widget):
        super().__init__(parent=None)
        self.parent_widget = parent_widget
        
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        
        self._setup_ui()
        
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.timeout.connect(self.hide_controls)
        self.auto_hide_timer.setInterval(3000)
        
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_geometry)
        self.position_timer.start(100)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_label = QLabel()
        self.title_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 220);
                background-color: rgba(0, 0, 0, 120);
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.title_label, 0, Qt.AlignTop | Qt.AlignLeft)
        
        layout.addStretch()
        
        self.notification_label = QLabel()
        self.notification_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(40, 40, 40, 200);
                padding: 15px 25px;
                border-radius: 10px;
                font-size: 16px;
            }
        """)
        self.notification_label.setAlignment(Qt.AlignCenter)
        self.notification_label.hide()
        layout.addWidget(self.notification_label, 0, Qt.AlignCenter)
        
        layout.addStretch()
        
        self.controls_widget = QWidget()
        self.controls_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(20, 20, 20, 200);
                border-radius: 12px;
            }
            QPushButton {
                background-color: rgba(229, 9, 20, 220);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(229, 9, 20, 255);
            }
        """)
        
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(20, 15, 20, 15)
        
        self.play_pause_btn = QPushButton("⏸ Pause")
        self.play_pause_btn.clicked.connect(self.play_pause_clicked.emit)
        controls_layout.addWidget(self.play_pause_btn)
        
        download_btn = QPushButton("⬇ Download")
        download_btn.clicked.connect(self.download_clicked.emit)
        controls_layout.addWidget(download_btn)
        
        fs_btn = QPushButton("⛶ Fullscreen")
        fs_btn.clicked.connect(self.fullscreen_clicked.emit)
        controls_layout.addWidget(fs_btn)
        
        controls_layout.addStretch()
        
        close_btn = QPushButton("✕ Close")
        close_btn.clicked.connect(self.close_clicked.emit)
        controls_layout.addWidget(close_btn)
        
        layout.addWidget(self.controls_widget, 0, Qt.AlignBottom)
    
    def _update_geometry(self):
        if self.parent_widget and self.parent_widget.isVisible():
            rect = self.parent_widget.geometry()
            pos = self.parent_widget.mapToGlobal(rect.topLeft())
            self.setGeometry(pos.x(), pos.y(), rect.width(), rect.height())
    
    def show_controls(self):
        self.controls_widget.show()
        self.auto_hide_timer.start()
        self.setCursor(Qt.ArrowCursor)
    
    def hide_controls(self):
        self.controls_widget.hide()
        self.setCursor(Qt.BlankCursor)
    
    def mouseMoveEvent(self, event):
        self.show_controls()
        super().mouseMoveEvent(event)
    
    def set_title(self, text):
        self.title_label.setText(f"📺 {text}")
    
    def set_playing(self, is_playing):
        if is_playing:
            self.play_pause_btn.setText("⏸ Pause")
        else:
            self.play_pause_btn.setText("▶ Play")
    
    def show_notification(self, message, duration=3000):
        self.notification_label.setText(message)
        self.notification_label.show()
        QTimer.singleShot(duration, self.notification_label.hide)
    
    def show_error(self, message):
        self.notification_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: rgba(200, 20, 20, 220);
                padding: 15px 25px;
                border-radius: 10px;
                font-size: 16px;
            }
        """)
        self.show_notification(message, 5000)
    
    def cleanup(self):
        self.position_timer.stop()
        self.auto_hide_timer.stop()
