import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5.QtCore import QUrl, QSize, Qt
from PyQt5.QtGui import QFont

class MiniMapPage(QWebEnginePage):
    def __init__(self, profile, parent=None):
        super().__init__(profile, parent)
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setFontSize(QWebEngineSettings.DefaultFontSize, 16)
        settings.setFontSize(QWebEngineSettings.MinimumFontSize, 14)

    def featurePermissionRequested(self, origin, feature):
        self.setFeaturePermission(
            origin,
            feature,
            QWebEnginePage.PermissionGrantedByUser
            if feature == QWebEnginePage.Geolocation
            else QWebEnginePage.PermissionDeniedByUser,
        )

class MiniMapWidget(QWidget):
    def __init__(self, parent=None):
        try:
            super().__init__(parent)
            self.profile = QWebEngineProfile("minimap_profile")
            self.profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            self.setup_ui()
            self.hide()  # Hidden by default
        except Exception as e:
            print(f"Error initializing MiniMapWidget: {str(e)}")
            super().__init__(parent)
            self.setStyleSheet("background:#000;color:#666;text-align:center;border:2px solid #444;border-radius:8px;")
            self.setFixedSize(300, 300)
            self.hide()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        
        web_container = QFrame()
        web_layout = QVBoxLayout(web_container)
        web_layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        self.page = MiniMapPage(self.profile, self.web_view)
        self.web_view.setPage(self.page)
        self._load_leaflet()
        self.web_view.setMinimumSize(QSize(296, 296))  # Slightly smaller than container
        web_layout.addWidget(self.web_view)
        
        layout.addWidget(web_container)
        self.setLayout(layout)
        
    def _load_leaflet(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <style>
                body { margin: 0; padding: 0; }
                /* Arrow marker sizing */
                .arrow-wrapper { width: 28px; height: 28px; transform: translate(-14px,-14px); }
            </style>
        </head>
        <body>
            <div id="map"></div>
            <script>
                // Initialize the map
                var map = L.map('map').setView([40.758, -73.9855], 13);
                
                // Add OpenStreetMap tiles
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);
                
                // Arrow marker builder (SVG data URL)
                function arrowIcon(angleDeg) {
                  var svg = `<?xml version="1.0" encoding="UTF-8"?>
                    <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
                      <g transform="rotate(${angleDeg} 14 14)">
                        <path d="M14 3 L20 18 L14 15 L8 18 Z" fill="#4285f4" stroke="#ffffff" stroke-width="1" />
                      </g>
                    </svg>`;
                  return L.icon({
                    iconUrl: 'data:image/svg+xml;utf8,' + encodeURIComponent(svg),
                    iconSize: [28,28],
                    iconAnchor: [14,14],
                  });
                }
                
                var userMarker = null, last = null;
                
                // Disable scroll wheel zoom to prevent accidental zooming
                map.scrollWheelZoom.disable();
                
                // Disable dragging to prevent map movement
                map.dragging.disable();

                function toRad(d){return d*Math.PI/180}
                function bearing(a,b){
                  const φ1=toRad(a.lat), φ2=toRad(b.lat);
                  const y=Math.sin(toRad(b.lng-a.lng))*Math.cos(φ2);
                  const x=Math.cos(φ1)*Math.sin(φ2)-Math.sin(φ1)*Math.cos(φ2)*Math.cos(toRad(b.lng-a.lng));
                  return ((Math.atan2(y,x)*180)/Math.PI+360)%360;
                }

                if (navigator.geolocation && navigator.geolocation.watchPosition) {
                  navigator.geolocation.watchPosition(function(pos){
                    var lat = pos.coords.latitude, lng = pos.coords.longitude;
                    var hd = (pos.coords.heading != null && !isNaN(pos.coords.heading)) ? pos.coords.heading : 0;
                    if (!hd && last) { hd = bearing(last, {lat:lat, lng:lng}); }
                    if (!userMarker) {
                      userMarker = L.marker([lat,lng], { icon: arrowIcon(hd) }).addTo(map);
                      map.setView([lat,lng], 15);
                    } else {
                      userMarker.setLatLng([lat,lng]);
                      userMarker.setIcon(arrowIcon(hd));
                    }
                    last = {lat:lat, lng:lng};
                  }, function(err){ console.log('Mini map geolocation failed', err); }, { enableHighAccuracy:true, maximumAge:5000, timeout:10000 });
                }
            </script>
        </body>
        </html>
        """
        
        self.web_view.setHtml(html, QUrl("https://localhost/"))
