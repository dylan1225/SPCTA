# Maps and Routing — Detailed Guide

This document explains the two mapping widgets in this repo, their features, how to configure Google APIs, and how to control them from your PyQt app.


## Components

- `web_embed/maps/map_widget.py` — `MapsWidget`: a Google Maps JavaScript embed with search, place details, directions, and a built‑in pickup planner (VRP).
- `web_embed/mini_map.py` — `MiniMapWidget`: a compact Leaflet map for showing current location and heading.
- Assets used by `MapsWidget`:
  - `web_embed/maps/map.html` — main HTML template
  - `web_embed/maps/map.css` — styles (dark theme, panels, controls)
  - `web_embed/maps/map.js` — logic (search, places, directions, VRP)


## `MapsWidget` (Google Maps)

Constructor:
```
MapsWidget(api_key: str | None = None, center: tuple[float,float] = (40.758, -73.9855))
```

Behavior:
- Injects the provided API key into `map.html` and loads the Google Maps JavaScript API from the network.
- Applies a custom Vector Map Style ID via `VECTOR_MAP_ID` constant in `map_widget.py`.
- Grants Geolocation permission (via `_GeoPage.featurePermissionRequested`).

UI features (from map.html/css/js):
- Search bar: type a destination, autocomplete results panel appears below. Selecting a result opens the info box.
- Place info box: photo, rating, address, phone; “Directions” button to start routing from current origin.
- Directions: Uses Google Directions API to compute a route and display turn‑by‑turn. A “Next turn” box shows the upcoming maneuver and distance.
- Recenter FAB: returns camera to the user’s current position and zooms in.
- Geolocation tracking: watches position and heading, shows an arrow marker and an accuracy circle.
- Pickup Planner (VRP):
  - Open/Close panel: left side “📦 Planner” button.
  - Depot: set via current center, locate me, or place search/autocomplete.
  - Capacity: integer capacity for the vehicle per trip.
  - Pickups: add multiple pickup locations via a modal place search or saved locations. Each pickup supports a demand quantity.
  - Saved locations: persist to `localStorage` with name and coordinates; reuse or set as Depot; delete individual items.
  - Manual order: when enabled, routes are built in entered order with capacity splitting.
  - Optimized order: when disabled, builds a duration matrix using Google Distance Matrix API; falls back to Haversine if the matrix call fails. Greedy VRP heuristic splits into multiple trips as needed by capacity.
  - Trip rendering: each trip is drawn in a different color; summary and per‑leg distances/durations shown in the info panel.


### Google Cloud configuration

Required APIs (enable in Google Cloud Console for your project):
- Maps JavaScript API
- Places API
- Directions API
- Distance Matrix API

Steps:
1) Create a project and enable billing (required by Google Maps APIs).
2) Enable the four APIs above.
3) Create an API key.
4) Restrictions:
   - For a desktop PyQt/QWebEngine app, “HTTP referrer” restrictions do not apply reliably. Consider:
     - Using no application restriction but applying API restrictions to only the above APIs and setting per‑API quota limits.
     - Or proxying Google API calls via your backend so the key is never shipped to the client (advanced).
   - Always rotate keys if leaked and monitor usage.
5) Provide the key to `MapsWidget`:
   - Environment variable: `export GOOGLE_MAPS_API_KEY="..."`
   - Or pass explicitly: `MapsWidget(api_key="...")`

Vector Map Style (mapId):
- `VECTOR_MAP_ID` in `map_widget.py` controls the map style. Create a custom style in Google Cloud Console (Maps Styling), obtain its Map ID, and set it there.


### Permissions and privacy

- Geolocation: The widget requests geolocation via the browser runtime. The Qt page `_GeoPage` grants permission only for `QWebEnginePage.Geolocation`. OS‑level location permissions must be granted by the user/system.
- Network: All Google services are loaded from the network. Ensure connectivity and that corporate firewalls/proxies allow access.
- The “Locate Me” fallback may query `https://ipapi.co/json/` if the browser geolocation fails; this is used only to approximate position. You can remove or firewall this if undesired.


### Programmatic control from Python

You can drive the map at runtime by executing JavaScript on the page:

- Center the map:
```
view = maps_widget.page()
lat, lng = 37.7749, -122.4194
js = f"map.setCenter(new google.maps.LatLng({lat}, {lng})); map.setZoom(14);"
maps_widget.page().runJavaScript(js)
```

- Route to a destination coordinate:
```
lat, lng = 37.779, -122.419
js = f"routeTo(new google.maps.LatLng({lat}, {lng}));"
maps_widget.page().runJavaScript(js)
```

- Open the planner UI:
```
maps_widget.page().runJavaScript("document.getElementById('vrpOpen').click();")
```

- Clear VRP overlays (if present):
```
maps_widget.page().runJavaScript("(window.clearVRPRoutes||function(){})();")
```

Note: these calls rely on functions and globals defined in `map.js` and may no‑op if the page has not finished initializing. If needed, connect to the QWebEngineView `loadFinished` signal.


## `MiniMapWidget` (Leaflet)

Behavior:
- Loads Leaflet CSS/JS from unpkg CDN and initializes a simple OpenStreetMap basemap.
- Shows a heading arrow marker that rotates with movement; approximates bearing if heading is unavailable.
- Disables scroll/drag interactions to keep the map static in a small area.

Notes:
- Requires internet access to fetch Leaflet and OSM tiles (unpkg and tile servers). For offline or locked‑down environments, consider bundling Leaflet assets and pointing to a self‑hosted tile server.
- No Google API key is required for MiniMap.


## Troubleshooting

- Blank map or errors about API key:
  - Verify `GOOGLE_MAPS_API_KEY` is set and correct.
  - Ensure the four Google APIs are enabled.
  - Check console logs (run app from terminal) for network/permission errors.

- Geolocation not working:
  - Ensure OS location services are enabled for your user.
  - On Linux, some distros require additional services (e.g., GeoClue). Qt uses Chromium’s geolocation; ensure it can talk to geolocation providers.

- Directions/DistanceMatrix errors:
  - Inspect quota and billing in Google Cloud; exceeded quotas return errors.
  - The VRP planner falls back to a Haversine‑based matrix when Distance Matrix fails.

- Slow loads:
  - Consider preloading fonts and reducing photo sizes in place details.
  - Vector maps and Places searches can be network‑heavy; cache or limit requests.


## Security considerations

- API key exposure: A desktop webview ships the key to the client. Prefer strict API restrictions and quotas; consider proxying sensitive endpoints via your backend if you need tighter control.
- LocalStorage: Saved locations are stored locally in the webview profile; they do not sync across machines.

