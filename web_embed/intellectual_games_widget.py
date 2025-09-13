from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt5.QtCore import QUrl
from src.keyboard import VirtualKeyboard
from src.web_embed.adblock import enable_adblock
 

class GamePage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebGLEnabled, True)
        settings.setAttribute(QWebEngineSettings.DnsPrefetchEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        
        settings.setFontSize(QWebEngineSettings.DefaultFontSize, 16)
        settings.setFontSize(QWebEngineSettings.MinimumFontSize, 14)

    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        msg = str(message)
        noisy = (
            'preloaded using link preload but not used' in msg or
            'blocked by CORS policy' in msg or
            'generate_204' in msg
        )
        if noisy:
            return
        return super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)

class IntellectualGamesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.hide()  # Hidden by default

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        title = QLabel("Intellectual Games")
        title.setFont(QFont("Lexend Bold", 24))
        title.setStyleSheet("color: #00FFA3;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        games_layout = QGridLayout()
        games_layout.setSpacing(20)

        games = [
            ("Wordle", "https://www.nytimes.com/games/wordle/index.html"),
            ("Connections", "https://www.nytimes.com/games/connections"),
            ("Mini Crossword", "https://www.nytimes.com/crosswords/game/mini"),
            ("Spelling Bee", "https://www.nytimes.com/puzzles/spelling-bee"),
            ("Trolley Problems", "https://neal.fun/absurd-trolley-problems/"),
            ("Minesweeper", "https://minesweeper.online/"),
            ("Wiki Game", "https://www.thewikigame.com/group")
        ]

        button_style = """
            QPushButton {
                background-color: #1A1A1A;
                color: #00FFA3;
                border: 2px solid #00FFA3;
                border-radius: 10px;
                padding: 20px;
                font-family: 'Lexend Bold';
                font-size: 18px;
                min-width: 200px;
                min-height: 60px;
            }
            QPushButton:hover {
                background-color: #00FFA3;
                color: #000000;
            }
        """

        self.buttons = {}
        for i, (name, url) in enumerate(games):
            btn = QPushButton(name)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(lambda checked, u=url, n=name: self.load_game(u, n))
            row = i // 3  # 3 buttons per row
            col = i % 3
            games_layout.addWidget(btn, row, col)
            self.buttons[name] = btn

        layout.addLayout(games_layout)
        
        self.web_container = QWidget()
        web_layout = QVBoxLayout(self.web_container)
        web_layout.setContentsMargins(0, 0, 0, 0)
        
        back_button = QPushButton("← Back to Games")
        back_button.setStyleSheet(button_style)
        back_button.clicked.connect(self.show_menu)
        web_layout.addWidget(back_button)
        
        self.profile = QWebEngineProfile("games_profile")
        self.profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.web_view = QWebEngineView()
        self.page = GamePage(self.profile, self.web_view)
        self.web_view.setPage(self.page)
        web_layout.addWidget(self.web_view)
        enable_adblock(self.web_view, target="auto")
        
        
        self.keyboard = VirtualKeyboard(self)
        self.keyboard.hide()
        self.keyboard.key_pressed.connect(self.handle_key_press)
        
        layout.addWidget(self.web_container)
        self.web_container.hide()
        
        self.setLayout(layout)

    def load_game(self, url, name):
        self.web_view.setUrl(QUrl(url))
        for button in self.buttons.values():
            button.hide()
        self.web_container.show()
        
        if self.web_view.focusProxy():
            self.web_view.focusProxy().installEventFilter(self)
        

    def show_menu(self):
        self.web_container.hide()
        for button in self.buttons.values():
            button.show()

    def handle_key_press(self, key):
        if key == '\b':
            self.web_view.page().runJavaScript(
                "document.activeElement.value = document.activeElement.value.slice(0, -1);"
            )
        elif key == '\n':
            self.web_view.page().runJavaScript(
                "document.activeElement.form && document.activeElement.form.submit();"
            )
        else:
            self.web_view.page().runJavaScript(
                f"document.activeElement.value += '{key}';"
            )
    
    def eventFilter(self, obj, event):
        if event.type() == event.FocusIn:
            self.web_view.page().runJavaScript(
                "document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'TEXTAREA'",
                lambda result: self.keyboard.setVisible(result)
            )
        return super().eventFilter(obj, event)
        
    def closeEvent(self, event):
        if self.web_view:
            self.web_view.setPage(None)
            self.web_view.deleteLater()
        if hasattr(self, 'page'):
            self.page.deleteLater()
        super().closeEvent(event) 
