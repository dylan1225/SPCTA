from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
from PyQt5.QtCore import QUrl, QSize, Qt
from src.keyboard import VirtualKeyboard
from src.widget_config import WIDGET_WIDTH, WIDGET_HEIGHT
 

class DarkModePage(QWebEnginePage):
    def __init__(self, parent=None):
        super().__init__(parent)
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setFontSize(QWebEngineSettings.DefaultFontSize, 16)
        settings.setFontSize(QWebEngineSettings.MinimumFontSize, 14)

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        if isMainFrame:
            self.runJavaScript("""
                (function() {
                    const style = document.createElement('style');
                    style.textContent = `
                        html { background: #1a1a1a !important; }
                        body { background: #1a1a1a !important; color: #ffffff !important; }
                        * { color: #ffffff !important; background-color: #1a1a1a !important; }
                        a { color: #00FFA3 !important; }
                        input, textarea { background: #2d2d2d !important; border-color: #404040 !important; }
                    `;
                    document.head.appendChild(style);
                })();
            """)
        return super().acceptNavigationRequest(url, _type, isMainFrame)

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

class WebAppWidget(QWidget):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.url = url
        self._loaded = False
        self.setup_ui()
        self.hide()  # Hidden by default

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)  # left, top, right, bottom
        layout.setSpacing(0)  # Space between widgets in layout
        
        web_container = QFrame()
        self._web_container = web_container
        web_layout = QVBoxLayout(web_container)
        web_layout.setContentsMargins(0, 0, 0, 0)  # left, top, right, bottom
        
        self.web_view = QWebEngineView()
        self.page = DarkModePage(self.web_view)
        self.web_view.setPage(self.page)
        self.web_view.setUrl(QUrl(self.url))
        self.web_view.setMinimumSize(QSize(WIDGET_WIDTH, WIDGET_HEIGHT))
        web_layout.addWidget(self.web_view)
        
        self.keyboard = VirtualKeyboard(self)
        self.keyboard.hide()  # Hidden by default
        
        self.keyboard.key_pressed.connect(self.handle_key_press)
        
        layout.addWidget(web_container)
        self.setLayout(layout)
        
        self.web_view.focusProxy().installEventFilter(self)

        
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
