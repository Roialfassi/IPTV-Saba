import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QProgressBar, QMessageBox
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal

from src.data.data_loader import DataLoader

import sys
from PyQt5.QtWidgets import (
    QDialog, QLabel, QProgressBar, QVBoxLayout, QMessageBox
)
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot

from src.controller.controller import Controller


class LoadingScreen(QDialog):
    """
    Loading Screen that displays a progress bar while data is being loaded.
    Integrates with the Controller to receive progress updates and handle completion.
    """

    loading_finished = pyqtSignal(dict)  # Emitting the loaded groups

    def __init__(self, controller: Controller):
        super().__init__()
        self.controller = controller
        self.setWindowTitle("IPTV - Loading")
        self.setFixedSize(500, 300)
        self.setWindowFlags(
            Qt.Window | Qt.FramelessWindowHint | Qt.Dialog
        )
        self.setModal(True)
        self.init_ui()
        self.connect_signals()

    def init_ui(self):
        """
        Initializes the UI components of the Loading Screen.
        """
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Status Label
        self.status_label = QLabel("Loading channels...")
        self.status_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.status_label.setStyleSheet("color: #e50914;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #e50914;
                border-radius: 5px;
                text-align: center;
                background-color: #2c2c2c;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #e50914;
                width: 20px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        self.setStyleSheet("background-color: #141414;")


    def connect_signals(self):
        """
        Connects Controller signals to Loading Screen slots.
        """
        self.controller.progress_updated.connect(self.update_progress)
        self.controller.data_loaded.connect(self.on_data_loaded)
        self.controller.error_occurred.connect(self.on_error_occurred)


    def start_loading(self):
        """
        Initiates the data loading process through the Controller.
        """
        self.controller.initiate_loading_screen()

    @pyqtSlot(int)
    def update_progress(self, value: int):
        """
        Updates the progress bar with the given value.

        Args:
            value (int): Progress percentage (0-100).
        """
        self.progress_bar.setValue(value)
        self.status_label.setText(f'Loading... {value}%')

    @pyqtSlot(dict)
    def on_data_loaded(self, groups: dict):
        """
        Handles the data loaded signal from the Controller.

        Args:
            groups (dict): Loaded groups and channels data.
        """
        # self.status_label.setText("Channels loaded successfully!")
        QMessageBox.information(
            self,
            "Loading Complete",
            "Channels were loaded successfully!"
        )
        self.loading_finished.emit(groups)
        self.accept()  # Close the Loading Screen

        # Optionally, emit a custom signal or handle the transition here
        # For example:
        # self.parent().open_choose_channel_screen(groups)

    @pyqtSlot(str)
    def on_error_occurred(self, error_message: str):
        """
        Handles the error occurred signal from the Controller.

        Args:
            error_message (str): The error message to display.
        """
        QMessageBox.critical(
            self,
            "Loading Error",
            f"An error occurred while loading channels:\n{error_message}"
        )
        self.reject()  # Close the Loading Screen


def main():
    app = QApplication(sys.argv)
    controller = Controller()
    controller.select_profile('roi')
    loading_screen = LoadingScreen(controller)
    loading_screen.loading_finished.connect(lambda groups: print("Loading Finished with groups:", groups))

    loading_screen.show()
    loading_screen.start_loading()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
