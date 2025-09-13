from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QIcon
import os
from src.style.buttons import nav_button_style

class navWidget(QWidget):
    button_clicked_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(20)  # Increased spacing between buttons
        
        button_style = nav_button_style()
        
        layout.addStretch(1)
        
        home_path = "Media/Icons/home-hashtag-svgrepo-com.svg"
        if os.path.exists(home_path):
            home_btn = QPushButton()
            home_btn.setIcon(QIcon(home_path))
            home_btn.setIconSize(QSize(64, 64))  # Doubled icon size
            home_btn.setFixedSize(QSize(100, 100))  # Doubled button size
            home_btn.setStyleSheet(button_style)
            home_btn.clicked.connect(lambda: self.button_clicked_signal.emit("Home"))
            layout.addWidget(home_btn)
        else:
            pass
        
        music_path = "Media/Icons/music-svgrepo-com.svg"
        if os.path.exists(music_path):
            music_btn = QPushButton()
            music_btn.setIcon(QIcon(music_path))
            music_btn.setIconSize(QSize(64, 64))  # Doubled icon size
            music_btn.setFixedSize(QSize(100, 100))  # Doubled button size
            music_btn.setStyleSheet(button_style)
            music_btn.clicked.connect(lambda: self.button_clicked_signal.emit("Music"))
            layout.addWidget(music_btn)
        else:
            pass
        
        maps_path = "Media/Icons/route-square-svgrepo-com.svg"
        if os.path.exists(maps_path):
            maps_btn = QPushButton()
            maps_btn.setIcon(QIcon(maps_path))
            maps_btn.setIconSize(QSize(64, 64))  # Doubled icon size
            maps_btn.setFixedSize(QSize(100, 100))  # Doubled button size
            maps_btn.setStyleSheet(button_style)
            maps_btn.clicked.connect(lambda: self.button_clicked_signal.emit("Maps"))
            layout.addWidget(maps_btn)
        else:
            pass
        
        games_path = "Media/Icons/gameboy-svgrepo-com.svg"
        if os.path.exists(games_path):
            games_btn = QPushButton()
            games_btn.setIcon(QIcon(games_path))
            games_btn.setIconSize(QSize(64, 64))  # Doubled icon size
            games_btn.setFixedSize(QSize(100, 100))  # Doubled button size
            games_btn.setStyleSheet(button_style)
            games_btn.clicked.connect(lambda: self.button_clicked_signal.emit("Games"))
            layout.addWidget(games_btn)
        else:
            pass
        
        layout.addStretch(1)
        self.setLayout(layout)

    def button_clicked(self, button_name):
        self.button_clicked_signal.emit(button_name)
