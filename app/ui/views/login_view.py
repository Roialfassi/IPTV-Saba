"""Login/Profile Selection View."""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QComboBox, QCheckBox, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from app.core.config import Config


class LoginView(QWidget):
    """Profile selection and login view."""
    
    login_success = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._load_profiles()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        title = QLabel("IPTV Saba")
        title.setStyleSheet("font-size: 48px; font-weight: bold; color: #e50914;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Select Profile or Create New")
        subtitle.setStyleSheet("font-size: 18px; color: #b3b3b3; margin-bottom: 40px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        form_frame = QFrame()
        form_frame.setMaximumWidth(500)
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
                border-radius: 8px;
                padding: 40px;
            }
        """)
        form_layout = QVBoxLayout(form_frame)
        
        self.profile_combo = QComboBox()
        self.profile_combo.addItem("-- Create New Profile --")
        form_layout.addWidget(QLabel("Profile:"))
        form_layout.addWidget(self.profile_combo)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Profile Name")
        form_layout.addWidget(QLabel("Name:"))
        form_layout.addWidget(self.name_input)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("M3U Playlist URL")
        form_layout.addWidget(QLabel("Playlist URL:"))
        form_layout.addWidget(self.url_input)
        
        self.auto_login_cb = QCheckBox("Remember me (Auto-login)")
        form_layout.addWidget(self.auto_login_cb)
        
        btn_layout = QHBoxLayout()
        
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self._on_login)
        btn_layout.addWidget(self.login_btn)
        
        self.create_btn = QPushButton("Create Profile")
        self.create_btn.clicked.connect(self._on_create)
        btn_layout.addWidget(self.create_btn)
        
        form_layout.addLayout(btn_layout)
        
        layout.addWidget(form_frame, alignment=Qt.AlignCenter)
        
        self.profile_combo.currentIndexChanged.connect(self._on_profile_selected)
    
    def _load_profiles(self):
        """Load profiles into combo box."""
        self.profile_combo.clear()
        self.profile_combo.addItem("-- Create New Profile --")
        
        profiles = Config.get_profiles()
        for name in profiles.keys():
            self.profile_combo.addItem(name)
    
    def _on_profile_selected(self, index):
        """Handle profile selection."""
        if index == 0:
            self.name_input.clear()
            self.url_input.clear()
            self.name_input.setEnabled(True)
            self.url_input.setEnabled(True)
        else:
            profile_name = self.profile_combo.currentText()
            profile = Config.get_profile(profile_name)
            
            if profile:
                self.name_input.setText(profile_name)
                self.url_input.setText(profile['url'])
                self.name_input.setEnabled(False)
                self.url_input.setEnabled(False)
    
    def _on_login(self):
        """Handle login button."""
        profile_name = self.profile_combo.currentText()
        
        if profile_name == "-- Create New Profile --":
            return
        
        if self.auto_login_cb.isChecked():
            Config.update_settings(auto_login=True, last_profile=profile_name)
        else:
            Config.update_settings(auto_login=False, last_profile="")
        
        self.login_success.emit(profile_name)
    
    def _on_create(self):
        """Handle create profile button."""
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name or not url:
            return
        
        Config.add_profile(name, url)
        self._load_profiles()
        
        index = self.profile_combo.findText(name)
        if index >= 0:
            self.profile_combo.setCurrentIndex(index)
