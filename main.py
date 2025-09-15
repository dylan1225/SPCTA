from __future__ import annotations  # Add this at the top
import warnings
import sys
import os
from dotenv import load_dotenv

from src.widget_config import WIDGET_WIDTH, WIDGET_HEIGHT, MINIMAP_SIZE

warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, 
    QStackedWidget, QPushButton, QHBoxLayout, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, QRectF, QPoint, QSize, QEvent
from PyQt5.QtGui import QFontDatabase, QFont, QColor, QKeyEvent
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QPainter
from src.style.buttons import primary_button_style


print("Loading environment variables")
load_dotenv()

api_key = os.getenv("GOOGLE_MAPS_API_KEY")
if api_key:
    print(f"Google Maps API key loaded successfully (length: {len(api_key)})")
else:
    print("Google Maps API key not found in environment variables")

from src.speedometer import SpeedometerWidget
from src.navbar import navWidget
from src.web_embed.maps import MapsWidget
from src.web_embed.youtube import YouTubeWidget
from src.web_embed.movies import MoviesWidget
from src.music_menu import MusicMenu
from src.web_embed.youtube_music import YouTubeMusicWidget
from src.web_embed.apple_music import AppleMusicWidget
from src.web_embed.soundcloud import SoundCloudWidget
from src.web_embed.intellectual_games_widget import IntellectualGamesWidget
from src.web_embed.mini_map import MiniMapWidget
from src.web_embed.manager import web_embed_manager
from src.clock_widget import ClockWidget, TimeOnlyWidget, DateOnlyWidget
from src.ytmusic_mini_player import YouTubeMusicMiniPlayer

class EntertainmentMenu(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        grid_container = QFrame()
        grid_container.setStyleSheet("background: transparent;")
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(20)  # Space between buttons
        
        button_style = primary_button_style()
        
        options = [
            "YouTube", "Movies", "Board Games",
            "Wii Games", "Instagram", "Intellectual Games"
        ]
        
        self.buttons = {}  # Store buttons in a dictionary
        for i, text in enumerate(options):
            btn = QPushButton(text)
            btn.setFont(QFont("Lexend Bold"))
            btn.setStyleSheet(button_style)
            btn.setFixedSize(QSize(250, 80))  # Fixed size for consistent layout
            row = i // 2  # 2 buttons per row
            col = i % 2
            grid_layout.addWidget(btn, row, col)
            self.buttons[text] = btn
        
        main_layout.addStretch(1)
        main_layout.addWidget(grid_container)
        main_layout.addStretch(1)
        
        container_layout = QHBoxLayout()
        container_layout.addStretch(1)
        container_layout.addLayout(main_layout)
        container_layout.addStretch(1)
        
        self.setLayout(container_layout)
        self.setStyleSheet("background-color: transparent;")

class MainUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.nav_widget = navWidget()
        self.nav_widget.button_clicked_signal.connect(self.handle_nav_button)
        main_layout.addWidget(self.nav_widget)

        date_container = QFrame()
        date_layout = QHBoxLayout(date_container)
        date_layout.setContentsMargins(0, 5, 0, 5)
        
        self.date_widget = DateOnlyWidget()
        self.date_widget.setFixedHeight(25)  # Reduced height
        
        self.time_widget = TimeOnlyWidget()
        self.time_widget.setFixedHeight(25)  # Same height as date
        
        date_layout.addStretch(1)
        date_layout.addWidget(self.date_widget)
        date_layout.addSpacing(20)  # Space between date and time
        date_layout.addWidget(self.time_widget)  # Time next to date
        date_layout.addStretch(1)
        
        main_layout.addWidget(date_container)

        content_container = QFrame()
        content_layout = QHBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        speedometer_container = QFrame()
        speedometer_layout = QVBoxLayout(speedometer_container)
        speedometer_layout.setContentsMargins(20, 10, 0, 0)  # Reduced top margin from 20 to 10
        self.speedometer = SpeedometerWidget()
        speedometer_layout.addWidget(self.speedometer)
        speedometer_layout.addStretch(1)
        content_layout.addWidget(speedometer_container, 0)
        
        center_container = QFrame()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)
        
        self.content_stack = QStackedWidget()
        
        self.entertainment_menu = EntertainmentMenu()
        self.youtube_widget = YouTubeWidget()
        self.movies_widget = MoviesWidget()
        self.music_menu = MusicMenu()
        self.youtube_music_widget = YouTubeMusicWidget()
        self.apple_music_widget = AppleMusicWidget()
        self.soundcloud_widget = SoundCloudWidget()
        self.intellectual_games_widget = IntellectualGamesWidget()
        
        try:
            self.maps_container = QFrame()
            maps_container_layout = QVBoxLayout(self.maps_container)
            maps_container_layout.setContentsMargins(20, 20, 20, 20)  # Same margins as YouTube
            maps_container_layout.setSpacing(0)
            
            self.maps_widget = MapsWidget()
            self.maps_widget.setMinimumSize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
            self.maps_widget.setMaximumSize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
            self.maps_widget.setSizePolicy(self.youtube_widget.sizePolicy())
            
            maps_container_layout.addWidget(self.maps_widget)
            
        except Exception as e:
            print(f"Error creating Google Maps widget: {str(e)}")
            self.maps_container = QFrame()
            maps_container_layout = QVBoxLayout(self.maps_container)
            maps_container_layout.setContentsMargins(20, 20, 20, 20)
            self.maps_widget = QLabel("Google Maps\nUnavailable")
            self.maps_widget.setStyleSheet("background:#000;color:#666;text-align:center;padding:50px;font-size:18px;")
            self.maps_widget.setMinimumSize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
            self.maps_widget.setMaximumSize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
            maps_container_layout.addWidget(self.maps_widget)

        self.content_stack.addWidget(self.entertainment_menu)
        self.content_stack.addWidget(self.youtube_widget)
        self.content_stack.addWidget(self.movies_widget)
        self.content_stack.addWidget(self.music_menu)
        self.content_stack.addWidget(self.youtube_music_widget)
        self.content_stack.addWidget(self.apple_music_widget)
        self.content_stack.addWidget(self.soundcloud_widget)
        self.content_stack.addWidget(self.intellectual_games_widget)
        self.content_stack.addWidget(self.maps_container) # Changed from self.maps_widget to self.maps_container
        
        center_layout.addWidget(self.content_stack)
        content_layout.addWidget(center_container, 1)
        
        self.minimap_container = QFrame()
        self.minimap_container.setFixedSize(MINIMAP_SIZE, MINIMAP_SIZE)
        self.minimap_container.setStyleSheet("background:#000;border:2px solid #444;border-radius:8px;")
        self.minimap_layout = QVBoxLayout(self.minimap_container)
        self.minimap_layout.setContentsMargins(2, 2, 2, 2)
        self.minimap_container.hide()

        self.ytmusic_mini_player = YouTubeMusicMiniPlayer(self.youtube_music_widget)
        self.ytmusic_mini_player.setFixedSize(MINIMAP_SIZE, 120)
        speedometer_layout.addWidget(self.ytmusic_mini_player)
        speedometer_layout.addWidget(self.minimap_container)

        self.entertainment_menu.buttons["YouTube"].clicked.connect(self.show_youtube)
        self.entertainment_menu.buttons["Movies"].clicked.connect(self.show_movies)
        self.entertainment_menu.buttons["Intellectual Games"].clicked.connect(self.show_intellectual_games)
        
        self.music_menu.buttons["YouTube Music"].clicked.connect(self.show_youtube_music)
        self.music_menu.buttons["Apple Music"].clicked.connect(self.show_apple_music)
        self.music_menu.buttons["SoundCloud"].clicked.connect(self.show_soundcloud)
        

        main_layout.addWidget(content_container, 1)  # Give content area stretch

        self.setLayout(main_layout)
        
        self.show_minimap()
        

    def show_youtube(self):
        self.maps_container.hide()
        web_embed_manager.open("YouTube", self.youtube_widget)
        self.content_stack.setCurrentWidget(self.youtube_widget)

    def show_movies(self):
        self.maps_container.hide()
        web_embed_manager.open("Movies", self.movies_widget)
        self.content_stack.setCurrentWidget(self.movies_widget)

    def show_intellectual_games(self):
        self.maps_container.hide()
        web_embed_manager.open("IntellectualGames", self.intellectual_games_widget)
        self.content_stack.setCurrentWidget(self.intellectual_games_widget)

    def show_music_menu(self):
        self.maps_container.hide()
        web_embed_manager.close_current()
        self.content_stack.setCurrentWidget(self.music_menu)

    def show_youtube_music(self):
        self.maps_container.hide()
        self.apple_music_widget.hide()
        self.soundcloud_widget.hide()
        web_embed_manager.open("YouTubeMusic", self.youtube_music_widget)
        self.content_stack.setCurrentWidget(self.youtube_music_widget)

    def show_apple_music(self):
        self.maps_container.hide()
        self.youtube_music_widget.hide()
        self.soundcloud_widget.hide()
        web_embed_manager.open("AppleMusic", self.apple_music_widget)
        self.content_stack.setCurrentWidget(self.apple_music_widget)

    def show_soundcloud(self):
        self.maps_container.hide()
        self.youtube_music_widget.hide()
        self.apple_music_widget.hide()
        web_embed_manager.open("SoundCloud", self.soundcloud_widget)
        self.content_stack.setCurrentWidget(self.soundcloud_widget)

    def handle_nav_button(self, button_name):
        self.hide_minimap()
        if button_name == "Maps":
            self.show_map()
        elif button_name == "Games":
            self.content_stack.setCurrentWidget(self.entertainment_menu)
        elif button_name == "Music":
            self.content_stack.setCurrentWidget(self.music_menu)
        elif button_name == "Home":
            self.content_stack.setCurrentWidget(self.entertainment_menu)
        if button_name != "Maps":
            self.show_minimap()

    def show_map(self):
        self.minimap_container.hide()
        
        print(f"Setting map widget size to {WIDGET_WIDTH}x{WIDGET_HEIGHT}")
        
        
        if self.maps_widget.parent() != self.maps_container:
            self.maps_widget.setParent(self.maps_container)
            self.maps_container.layout().addWidget(self.maps_widget)
        
        self.maps_widget.setMinimumSize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
        self.maps_widget.setMaximumSize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
        self.maps_widget.resize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
        
        self.maps_container.setParent(self.content_stack)
        self.maps_container.setMinimumSize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
        self.maps_container.setMaximumSize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
        
        if self.maps_container not in [self.content_stack.widget(i) for i in range(self.content_stack.count())]:
            self.content_stack.addWidget(self.maps_container)
        
        self.content_stack.setCurrentWidget(self.maps_container)
        self.maps_container.show()
        
        self.maps_container.update()
        self.content_stack.update()
        
        print(f"Map widget actual size: {self.maps_widget.size()}")
        print(f"Map container actual size: {self.maps_container.size()}")
        
        

    def show_minimap(self):
        self.maps_widget.setParent(self.minimap_container)
        self.maps_widget.setMinimumSize(QSize(MINIMAP_SIZE, MINIMAP_SIZE))
        self.maps_widget.setMaximumSize(QSize(MINIMAP_SIZE, MINIMAP_SIZE))
        self.maps_widget.resize(QSize(MINIMAP_SIZE, MINIMAP_SIZE))
        self.minimap_layout.addWidget(self.maps_widget)
        self.minimap_container.show()
        self.maps_widget.show()

    def hide_minimap(self):
        self.minimap_container.hide()

class CarInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Puddle")
        self.setStyleSheet("background-color: #000000;")
        self.showFullScreen()

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        try:
            self.main_screen = MainUI(self)
            self.stacked_widget.addWidget(self.main_screen)
            self.main_screen.show()
        except Exception as e:
            print(f"Error creating main screen: {str(e)}")
            self.main_screen = QLabel("Main Screen\nUnavailable")
            self.main_screen.setStyleSheet("background:#000;color:#fff;text-align:center;padding:50px;font-size:24px;")
            self.stacked_widget.addWidget(self.main_screen)
            self.main_screen.show()

        self.stacked_widget.setCurrentWidget(self.main_screen)

    def show_main_ui(self):
        """Show the main UI after boot animation is complete"""
        self.main_screen.show()
        self.stacked_widget.setCurrentWidget(self.main_screen)

    def keyPressEvent(self, event):
        if isinstance(event, QKeyEvent) and event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    skip_boot = "--skip-boot" in sys.argv

    font_dir = "Fonts"
    try:
        if os.path.exists(font_dir):
            for font_file in os.listdir(font_dir):
                if font_file.endswith(".ttf"):
                    font_path = os.path.join(font_dir, font_file)
                    QFontDatabase.addApplicationFont(font_path)
        else:
            pass
    except Exception as e:
        pass

    try:
        interface = CarInterface()
        # Boot animation removed; main UI shown immediately
        
        interface.show()
    except Exception as e:
        raise

    sys.exit(app.exec()) 
