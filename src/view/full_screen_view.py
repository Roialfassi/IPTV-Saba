import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFrame, QSlider)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import vlc

from src.model.channel_model import Channel


class FullScreenView(QWidget):
    """
    A full-screen media player that takes a URL, plays the channel, and provides limited controls.
    Keys include: back to `ChooseChannelScreen`, volume control, and play/pause.
    """

    go_back_signal = pyqtSignal()  # Signal to emit when going back to ChooseChannelScreen

    def __init__(self, channel: Channel):
        super().__init__()
        self.channel_name = channel.name
        self.stream_url = channel.stream_url
        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        self.is_playing = False
        self.is_muted = False
        self.init_ui()
        self.setMouseTracking(True)
        self.play_channel()
        self.hide_controls_timer = QTimer(self, interval=2000)  # Hide controls after 2 seconds of inactivity
        self.hide_controls_timer.timeout.connect(self.hide_controls)
        self.hide_controls_timer.start(2000)

    def init_ui(self):
        self.setWindowTitle('Full Screen Channel View')
        self.setStyleSheet("""
            QWidget {
                background-color: #141414;
                color: #FFFFFF;
                font-family: Arial, sans-serif;
            }
        """)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Video frame
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        main_layout.addWidget(self.video_frame, 1)

        # Controls layout
        self.controls_widget = QWidget(self)
        controls_layout = QHBoxLayout(self.controls_widget)
        controls_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addWidget(self.controls_widget)

        # Back Button
        self.back_button = QPushButton("Back to Channels")
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(229, 9, 20, 0.8);
                border: none;
                color: white;
                padding: 5px 10px;
                text-align: center;
                font-size: 12px;
                margin: 2px 1px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: rgba(229, 9, 20, 1);
            }
        """)
        controls_layout.addWidget(self.back_button)

        # Play/Pause Button
        self.play_pause_button = QPushButton("Pause")
        self.play_pause_button.clicked.connect(self.toggle_play_pause)
        self.play_pause_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(229, 9, 20, 0.8);
                border: none;
                color: white;
                padding: 5px 10px;
                text-align: center;
                font-size: 12px;
                margin: 2px 1px;
                border-radius: 2px;
            }
            QPushButton:hover {
                background-color: rgba(229, 9, 20, 1);
            }
        """)
        controls_layout.addWidget(self.play_pause_button)

        # Volume Slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.valueChanged.connect(self.set_volume)
        controls_layout.addWidget(QLabel("Volume"))
        controls_layout.addWidget(self.volume_slider)

        # Channel name label
        self.channel_label = QLabel(self.channel_name)
        self.channel_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.channel_label)

        # Set up the VLC player with the video frame
        self.player.set_hwnd(self.video_frame.winId())

        # Timer to update the UI
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)

    def play_channel(self):
        """
        Play the channel stream provided in the URL.
        """
        media = self.vlc_instance.media_new(self.stream_url)
        self.player.set_media(media)
        self.player.play()
        self.is_playing = True
        self.play_pause_button.setText("Pause")

    def toggle_play_pause(self):
        """
        Toggle between play and pause.
        """
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
            self.play_pause_button.setText("Play")
        else:
            self.player.play()
            self.is_playing = True
            self.play_pause_button.setText("Pause")

    def set_volume(self, volume):
        """
        Set the volume of the player.
        """
        self.player.audio_set_volume(volume)

    def go_back(self):
        """
        Emit a signal to go back to the ChooseChannelScreen.
        """
        self.player.stop()
        self.go_back_signal.emit()

    def keyPressEvent(self, event):
        """
        Handle key events for basic control: back, mute/unmute, and volume control.
        """
        if event.key() == Qt.Key_Escape:
            self.go_back()
        elif event.key() == Qt.Key_Space:
            self.toggle_play_pause()
        elif event.key() == Qt.Key_Up:
            # Increase volume by 10
            current_volume = self.player.audio_get_volume()
            self.set_volume(min(current_volume + 10, 100))
            self.volume_slider.setValue(min(current_volume + 10, 100))
        elif event.key() == Qt.Key_Down:
            # Decrease volume by 10
            current_volume = self.player.audio_get_volume()
            self.set_volume(max(current_volume - 10, 0))
            self.volume_slider.setValue(max(current_volume - 10, 0))
        event.accept()

    def update_ui(self):
        """
        Update the UI periodically (optional, can be extended for more features).
        """
        pass

    def closeEvent(self, event):
        """
        Ensure the VLC player is stopped when the window is closed.
        """
        self.player.stop()
        event.accept()

    def mouseMoveEvent(self, event):
        # print(event)
        self.show_controls()
        self.hide_controls_timer.start(5000)  # Hide controls after 2 seconds of inactivity

    def show_controls(self):
        self.controls_widget.show()
        self.setCursor(Qt.ArrowCursor)

    def hide_controls(self):
        self.controls_widget.hide()
        # if self.is_fullscreen:
        #     self.setCursor(Qt.BlankCursor)




# Testing the FullScreenView class
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Sample channel details
    channel_name = "Sample Channel"
    stream_url = "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    channel_mock = Channel.from_dict({"name" : channel_name, "stream_url": stream_url})
    full_screen_view = FullScreenView(channel_mock)

    # Connect go_back_signal to a function (for now just closing the app)
    full_screen_view.go_back_signal.connect(app.quit)

    full_screen_view.showFullScreen()
    sys.exit(app.exec_())
