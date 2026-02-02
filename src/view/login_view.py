import sys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QListWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QCheckBox, QApplication, QScrollArea, QListWidgetItem,
    QFrame, QGraphicsDropShadowEffect, QMessageBox, QDialog, QLineEdit, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

from src.controller.controller import Controller


class CreateProfileDialog(QDialog):
    """
    Dialog to create a new profile by entering name and URL.
    Enhanced with modern styling inspired by Netflix and Facebook.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Profile")
        self.setFixedSize(500, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.init_ui()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setSpacing(25)
        main_layout.setContentsMargins(40, 20, 40, 20)

        # Header Label
        header_label = QLabel("Create Your Profile")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_label.setStyleSheet("color: #e50914;")
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)

        # Profile Name Input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Profile Name")
        self.name_input.setFont(QFont("Segoe UI", 12))
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #444;
                border-radius: 5px;
                background-color: #2c2c2c;
                color: white;
            }
            QLineEdit:focus {
                border: 2px solid #e50914;
            }
        """)
        main_layout.addWidget(self.name_input)

        # Profile URL Input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter Profile URL")
        self.url_input.setFont(QFont("Segoe UI", 12))
        self.url_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid #444;
                border-radius: 5px;
                background-color: #2c2c2c;
                color: white;
            }
            QLineEdit:focus {
                border: 2px solid #1877f2;
            }
        """)
        main_layout.addWidget(self.url_input)

        # Buttons Layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        # Create Button
        self.create_button = QPushButton("Create")
        self.create_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.create_button.setCursor(Qt.PointingHandCursor)
        self.create_button.setStyleSheet("""
            QPushButton {
                background-color: #e50914;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f40612;
            }
            QPushButton:pressed {
                background-color: #bf0c0c;
            }
        """)
        self.create_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self.create_button)

        # Cancel Button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #145dbf;
            }
            QPushButton:pressed {
                background-color: #0d4ea2;
            }
        """)
        self.cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_button)

        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)
        self.setStyleSheet("background-color: #141414;")

    def get_inputs(self):
        """
        Retrieves the entered profile name and URL.

        Returns:
            tuple: (profile_name, profile_url)
        """
        return self.name_input.text().strip(), self.url_input.text().strip()

    def accept(self):
        """
        Overrides the accept method to validate inputs before closing the dialog.
        """
        name, url = self.get_inputs()
        if not name or not url:
            QMessageBox.warning(self, "Incomplete Data", "Please enter both name and URL for the profile.")
            return
        # Additional validation can be added here (e.g., URL format)
        # print("accepted")
        super().accept()


class LoginScreen(QWidget):
    # Define a new signal to indicate successful login with profile URL
    login_success = pyqtSignal(str)  # Emitting the profile's URL
    easy_mode_success = pyqtSignal(str)  # Emitting the profile's URL

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller
        self.init_ui()
        self.load_profiles()
        self.connect_signals()

    def init_ui(self):
        # Window Setup
        self.setWindowTitle("Profile Selection")
        # Use a vertical gradient for the background.
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                            stop:0 #141414, stop:1 #000000);
                color: white;
                font-family: 'Netflix Sans', Arial, sans-serif;
            }
        """)

        # Main Layout (centers our login card)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addStretch()

        # Create a central "card" for the login elements.
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: rgba(20, 20, 20, 0.95);
                border-radius: 15px;
            }
        """)
        card.setMinimumSize(500, 600)

        # Add a drop shadow effect to the card for depth.
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(Qt.black)
        card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)
        self.auto_login = False  # Boolean value to track checkbox state
        # Header
        header = QLabel("Select Your Profile")
        header.setFont(QFont("Calibri", 28, QFont.Bold))
        header.setStyleSheet("color: #E50914; letter-spacing: 1px;")
        header.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(header)

        # Scrollable Profiles List
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: rgba(50, 50, 50, 0.5);
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background-color: #E50914;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.profiles_list = QListWidget()
        self.profiles_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: rgba(50, 50, 50, 0.7);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
                color: white;
            }
            QListWidget::item:selected {
                background-color: #E50914;
            }
            QListWidget::item:selected:hover {
                background-color: #f6121d;
            }
            QListWidget::item:hover {
                background-color: rgba(100, 100, 100, 0.5);
            }
        """)
        self.profiles_list.setFont(QFont("Segoe UI", 12))
        self.profiles_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll_area.setWidget(self.profiles_list)
        card_layout.addWidget(scroll_area)

        # Auto-Login Checkbox
        self.auto_login_checkbox = QCheckBox("Remember this profile")
        self.auto_login_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                font-size: 14px;
                background-color:transparent
                
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #E50914;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #f72a35;
            }
        """)
        card_layout.addWidget(self.auto_login_checkbox)
        self.auto_login_checkbox.stateChanged.connect(self.update_auto_login)
        # Buttons Layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        # Login Button
        self.login_button = QPushButton("Login")
        self.login_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.login_button.setCursor(Qt.PointingHandCursor)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #e50914;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff0909;
            }
            QPushButton:pressed {
                background-color: #bf0c0c;
            }
            QPushButton:focus {
                outline: none;
                border: 2px solid #ffffff;
            }
        """)
        self.login_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        buttons_layout.addWidget(self.login_button)

        # Easy Mode Button
        self.easy_mode_button = QPushButton("Easy Mode")
        self.easy_mode_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.easy_mode_button.setCursor(Qt.PointingHandCursor)
        self.easy_mode_button.setStyleSheet("""
            QPushButton {
                background-color: #ff5733;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ff3a11;
            }
            QPushButton:pressed {
                background-color: #bf0c0c;
            }
            QPushButton:focus {
                outline: none;
                border: 2px solid #ffffff;
            }
        """)
        self.easy_mode_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        buttons_layout.addWidget(self.easy_mode_button)

        # Create Profile Button
        self.create_profile_button = QPushButton("Create Profile")
        self.create_profile_button.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.create_profile_button.setCursor(Qt.PointingHandCursor)
        self.create_profile_button.setStyleSheet("""
           QPushButton {
                background-color: #1877f2;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #145dbf;
            }
            QPushButton:pressed {
                background-color: #0d4ea2;
            }
            QPushButton:focus {
                outline: none;
                border: 2px solid #ffffff;
            }
        """)
        self.create_profile_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        buttons_layout.addWidget(self.create_profile_button)

        card_layout.addLayout(buttons_layout)

        main_layout.addWidget(card, alignment=Qt.AlignCenter)
        main_layout.addStretch()
        self.setLayout(main_layout)

    def connect_signals(self):
        # Connect buttons to their respective slots
        self.login_button.clicked.connect(self.handle_login)
        self.easy_mode_button.clicked.connect(self.handle_easy_mode)
        self.create_profile_button.clicked.connect(self.open_create_profile_dialog)

        # Connect Controller signals to GUI slots
        self.controller.profiles_updated.connect(self.load_profiles)
        self.controller.error_occurred.connect(self.show_error)

    def load_profiles(self):
        """
        Loads profiles from the Controller and populates the profiles list.
        """
        self.profiles_list.clear()
        profiles = self.controller.list_profiles()
        self.profiles_list.addItems(profiles)

    def handle_login(self):
        """
        Handles the login process by selecting the active profile and emitting the login_success signal.
        """
        selected_items = self.profiles_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Profile Selected", "Please select a profile to login.")
            return
        profile_name = selected_items[0].text()
        profile = self.controller.profile_manager.get_profile(profile_name)
        if not profile:
            QMessageBox.critical(self, "Error", "Selected profile does not exist.")
            return
        # Select the profile in the Controller
        self.controller.select_profile(profile_name)
        if self.auto_login:
            self.controller.config_manager.set_value("auto_login_enabled", True)
        else:
            self.controller.config_manager.set_value("auto_login_enabled", False)
        self.controller.config_manager.set_value("last_active_profile_id", profile_name)
        # Emit the login_success signal with the profile's URL
        self.login_success.emit(profile.url)

    def handle_easy_mode(self):
        """
        Handles the login process by selecting the active profile and emitting the login_success signal.
        """
        try:
            selected_items = self.profiles_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "No Profile Selected", "Please select a profile to login.")
                return
            profile_name = selected_items[0].text()
            profile = self.controller.profile_manager.get_profile(profile_name)
            if not profile:
                QMessageBox.critical(self, "Error", "Selected profile does not exist.")
                return
            if len(profile.favorites) < 1:
                QMessageBox.critical(self, "Error", "Need to add favorites to this profile.")
                return
            self.controller.select_profile(profile_name)
            self.easy_mode_success.emit(profile.url)
        except Exception as e:
            print(f"handle_easy_mode {e}")

    def open_create_profile_dialog(self):
        """
        Opens a dialog to create a new profile.
        """
        dialog = CreateProfileDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            name, url = dialog.get_inputs()
            # print(name , url)
            if not name or not url:
                QMessageBox.warning(self, "Incomplete Data", "Please enter both name and URL for the profile.")
                return
            try:
                self.controller.create_profile(name, url)
            except Exception as e:
                print(e)

    def show_error(self, message: str):
        """
        Displays an error message to the user.

        Args:
            message (str): The error message to display.
        """
        QMessageBox.critical(self, "Error", message)

    def update_auto_login(self, state):
        """Update the boolean variable based on the checkbox state"""
        self.auto_login = state == 2  # Checked (Qt.Checked) is 2, Unchecked (Qt.Unchecked) is 0

    def closeEvent(self, event):
        """
        Handle window close event for clean exit.
        
        Ensures any open dialogs are closed and resources are cleaned up.
        """
        # Close any open dialogs
        for child in self.findChildren(QDialog):
            try:
                child.close()
            except Exception:
                pass
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("Assets/your_icon.png"))
    controller = Controller()
    login_screen = LoginScreen(controller)
    print("starting")
    login_screen.show()
    print("started")
    sys.exit(app.exec_())
