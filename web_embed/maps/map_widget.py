import os
from typing import Tuple
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

VECTOR_MAP_ID = "8ffd5464ed7851a4af500474"

class _GeoPage(QWebEnginePage):
    def featurePermissionRequested(self, origin, feature):
        self.setFeaturePermission(
            origin, feature,
            QWebEnginePage.PermissionGrantedByUser
            if feature == QWebEnginePage.Geolocation
            else QWebEnginePage.PermissionDeniedByUser
        )

class MapsWidget(QWebEngineView):
    def __init__(
        self,
        api_key: str | None = None,
        center: Tuple[float, float] = (40.758, -73.9855),
        parent=None
    ):
        try:
            super().__init__(parent)
            key  = api_key or os.getenv("GOOGLE_MAPS_API_KEY", "")
            
            if not key:
                print("No Google Maps API key found! This will cause the map to fail to load")
            else:
                print(f"MapsWidget: API key loaded (length: {len(key)})")
            here = os.path.dirname(__file__)
            
            html_path = os.path.join(here, "map.html")
            css_path = os.path.join(here, "map.css")
            js_path = os.path.join(here, "map.js")
            
            if not os.path.exists(html_path):
                print(f"map.html not found at: {html_path}")
                return
            if not os.path.exists(css_path):
                print(f"map.css not found at: {css_path}")
                return
            if not os.path.exists(js_path):
                print(f"map.js not found at: {js_path}")
                return
                
            try:
                html = open(html_path, encoding="utf-8").read()
                css  = open(css_path,  encoding="utf-8").read()
                js   = open(js_path,   encoding="utf-8").read()
            except UnicodeDecodeError:
                print("Unicode decode error, trying with cp1252 encoding")
                html = open(html_path, encoding="cp1252").read()
                css  = open(css_path,  encoding="cp1252").read()
                js   = open(js_path,   encoding="cp1252").read()
            html = (
                html
                .replace("__API_KEY__", key)
                .replace("__MAP_ID__",  VECTOR_MAP_ID)
                .replace("__LAT__",     str(center[0]))
                .replace("__LNG__",     str(center[1]))
                .replace("/*INLINE_CSS*/", css)
                .replace("//INLINE_JS",  js)
            )
            self.setPage(_GeoPage(self))
            self.setHtml(html, QUrl("https://localhost/"))
        except Exception as e:
            print(f"Error initializing MapsWidget: {str(e)}")
            super().__init__(parent)
            self.setHtml("<html><body style='background:#000;color:#fff;text-align:center;padding:50px;'><h2>Map Loading Error</h2><p>Unable to load Google Maps</p></body></html>")



