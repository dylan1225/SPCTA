from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings, QWebEngineProfile
from PyQt5.QtCore import QUrl, QSize, Qt
from src.keyboard import VirtualKeyboard
from src.web_embed.adblock import enable_adblock
 

class SoundCloudPage(QWebEnginePage):
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

class SoundCloudWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile = QWebEngineProfile("soundcloud_profile")
        self.profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        self.default_url = "https://soundcloud.com"
        
        self.setup_ui()
        self.hide()  # Hidden by default

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)
        
        web_container = QFrame()
        self._web_container = web_container
        web_layout = QVBoxLayout(web_container)
        web_layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        self.page = SoundCloudPage(self.profile, self.web_view)
        self.web_view.setPage(self.page)
        self.web_view.setUrl(QUrl(self.default_url))
        self.web_view.setMinimumSize(QSize(1280, 768))
        web_layout.addWidget(self.web_view)
        enable_adblock(self.web_view, target="auto")
        
        self.keyboard = VirtualKeyboard(self)
        self.keyboard.hide()  # Hidden by default
        
        self.keyboard.key_pressed.connect(self.handle_key_press)
        
        layout.addWidget(web_container)
        self.setLayout(layout)
        
        self.web_view.focusProxy().installEventFilter(self)
        
    
    def showEvent(self, event):
        super().showEvent(event)
        self.web_view.loadStarted.connect(lambda: self.stack.setCurrentIndex(0))
        self.web_view.loadFinished.connect(lambda ok: self.stack.setCurrentIndex(1))
        
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
        
    def showEvent(self, event):
        super().showEvent(event)
        if self.keyboard.isVisible():
            self.keyboard.move(0, self.height() - self.keyboard.height())

    def closeEvent(self, event):
        if self.web_view:
            self.web_view.setPage(None)
            self.web_view.deleteLater()
        if hasattr(self, 'page'):
            self.page.deleteLater()
        super().closeEvent(event) 
