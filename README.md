# SPCTA Complete Guide — Usage, Maps, and API Contract

## Requirements and Installation

- Python 3.9+
- PyQt5 and PyQtWebEngine

Install:

```
pip install PyQt5 PyQtWebEngine
```

Platform notes:
- Linux may require system WebEngine packages for media playback.
- QSoundEffect (boot sound) can require additional multimedia backends.


## Assets and Configuration

- Fonts: Widgets prefer the Lexend family. Falls back to system fonts if missing.
- Images/Icons under `Media/` are optional; widgets fall back gracefully:
  - `Media/boot.png` (splash image)
  - `Media/SFX/boot.wav` (boot sound)
  - `Media/Icons/*.svg` (navbar icons)
- Widget sizing: `widget_config.py` with `WIDGET_WIDTH`, `WIDGET_HEIGHT`, `MINIMAP_SIZE`.
- Google Maps API key for `MapsWidget`:

```
export GOOGLE_MAPS_API_KEY="<your_api_key>"
```


## Running the App

This repository ships a runnable main application.

- Install dependencies: `pip install -r requirements.txt`
- Provide Google Maps key via env or `.env` (dotenv is supported):
  - `.env` example:
    - `GOOGLE_MAPS_API_KEY=your-google-key`
- Run: `python main.py` (optional `--skip-boot` is accepted but boot is already skipped in code)

Notes:
- The codebase uses a `src/` package; all imports are `from src...` and main.py expects the working directory to be the repo root.

Using the UI:
- Navbar buttons: `Home` (Entertainment menu), `Music` (YouTube/Apple/SoundCloud), `Maps` (full-size Google Map), `Games` (Intellectual games).
- Mini map: a compact map appears in the left stack; entering Maps switches to the full-size map view and hides the mini map.
- YouTube Music mini player: sits below the speedometer; controls the embedded YouTube Music view.


## Quickstart App (embed components yourself)

If you want to compose widgets in your own window instead of using `main.py`, here is a minimal example. The production app is already implemented in `main.py`.

```
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import Qt

# If you use direct imports, drop the `src.` prefix
from src.navbar import navWidget
from src.clock_widget import ClockWidget
from src.speedometer import SpeedometerWidget
from src.web_embed.youtube_music import YouTubeMusicWidget
from src.web_embed.maps import MapsWidget
from src.web_embed.manager import web_embed_manager

import os

def main():
    os.environ.setdefault('GOOGLE_MAPS_API_KEY', '<put-your-key-here>')

    app = QApplication([])

    root = QWidget(); root.setWindowTitle('SPCTA Demo')
    layout = QVBoxLayout(root); layout.setContentsMargins(12, 12, 12, 12); layout.setSpacing(12)

    # Top bar
    top = QHBoxLayout()
    clock = ClockWidget(); nav = navWidget()
    top.addWidget(clock, 1); top.addWidget(nav, 2)
    layout.addLayout(top)

    # Middle area
    middle = QHBoxLayout()
    speedo = SpeedometerWidget(); middle.addWidget(speedo, 1)
    yt = YouTubeMusicWidget()
    maps = MapsWidget(api_key=os.getenv('GOOGLE_MAPS_API_KEY'))
    maps.hide()
    middle.addWidget(yt, 2); middle.addWidget(maps, 2)
    layout.addLayout(middle, 1)

    def on_nav(name: str):
        if name == 'Music':
            web_embed_manager.open('YouTubeMusic', yt); maps.hide()
        elif name == 'Maps':
            web_embed_manager.close_current(); maps.show()
        else:
            web_embed_manager.close_current(); maps.hide()
    nav.button_clicked_signal.connect(on_nav)

    root.resize(1600, 1000); root.show(); app.exec_()

if __name__ == '__main__':
    main()
```


## Widget Reference (as used by main.py)

- `boot_animation.BootAnimation`
  - Start: `start_boot_sequence()`; signal: `boot_complete` when finished.
  - Assets: `Media/boot.png`, `Media/SFX/boot.wav` (optional).

- `clock_widget.ClockWidget`, `TimeOnlyWidget`, `DateOnlyWidget`
  - QTimer‑based time/date labels with themed styles.

- `speedometer.SpeedometerWidget`
  - `set_speed(value)` updates gauge (0–300 mph) and derived power; responds to Up/Down keys when focused.

- `navbar.navWidget`
  - Emits `button_clicked_signal: str` for `Home`, `Music`, `Maps`, `Games`.
  - Expects icons in `Media/Icons/`; hides buttons silently if missing.

- `keyboard.VirtualKeyboard`
  - Emits `key_pressed(str)`; used by web embeds to type into focused inputs.

- Web embeds (hidden by default, call `.show()` when needed)
- `web_embed/web_view.WebAppWidget(url)` — generic wrapper for custom URLs
  - `web_embed.youtube_music.YouTubeMusicWidget` — with ad‑blocking injection
  - `web_embed.spotify.SpotifyWidget`, `web_embed.apple_music.AppleMusicWidget`, `web_embed.soundcloud.SoundCloudWidget`
  - `web_embed.manager.web_embed_manager` — ensures only one non‑map web app visible
  - `web_embed.mini_map.MiniMapWidget` — Leaflet mini map (no API key)
  - `web_embed.maps.MapsWidget` — Google Maps with search, routing, and VRP planner

- Styling utilities
  - `style/theme.py` — colors and font families
  - `style/buttons.py` — primary and nav button styles
  - `style/mini_player.py` — styles for YouTube Music mini player


## Maps Deep Dive

Two map widgets are provided: `MapsWidget` (Google Maps + planner) and `MiniMapWidget` (Leaflet).

### MapsWidget (Google Maps)

Constructor:
```
MapsWidget(api_key: str | None = None, center: tuple[float,float] = (40.758, -73.9855))
```

Behavior and features:
- Loads `web_embed/maps/map.html` with your API key and a styled Vector Map ID (`VECTOR_MAP_ID` in `map_widget.py`).
- Geolocation permissions are granted for `QWebEnginePage.Geolocation` via a custom page subclass.
- Search box with results panel; selecting a place opens an info box with photo, rating, address, phone, and “Directions”.
- Directions with Google Directions API, plus a “Next turn” HUD.
- Recenter FAB to jump back to user location; continuous geolocation tracking with heading arrow and accuracy circle.
- Pickup Planner (VRP panel): depot selection, capacity, add pickups via modal search, saved locations via localStorage, manual or optimized order, multi‑trip rendering with per‑leg metrics and total summaries.
- Matrix building uses Google Distance Matrix API; falls back to Haversine distances when needed.

Vector Map Style (Map ID):
- Create a custom style in Google Cloud Console (Maps Styling) and set `VECTOR_MAP_ID` in `map_widget.py`.

Programmatic control examples (inside the running page):
```
# Center and zoom
lat, lng = 37.7749, -122.4194
maps.page().runJavaScript(f"map.setCenter(new google.maps.LatLng({lat},{lng})); map.setZoom(14);")

# Route to a destination
maps.page().runJavaScript(f"routeTo(new google.maps.LatLng({lat},{lng}));")

# Open the planner UI
maps.page().runJavaScript("document.getElementById('vrpOpen').click();")

# Clear VRP overlays
maps.page().runJavaScript("(window.clearVRPRoutes||function(){})();")
```

Troubleshooting:
- Blank map: verify `GOOGLE_MAPS_API_KEY` and that APIs are enabled.
- Geolocation: ensure OS location services; on Linux, services like GeoClue may be required.
- Quotas: Directions/DistanceMatrix need billing and sufficient quotas.

Security considerations:
- API key is shipped to the desktop client. Prefer API restrictions and quotas; consider proxying calls via a backend if necessary.


### Using the Main Map — Step by Step

This section focuses on the day-to-day usage of the Google Map and its built-in features.

- Search and inspect a place
  - Type into the top search box; a results panel opens below it.
  - Click a result to open the info box with photo, rating, address, and phone.
  - Press “Directions” in the info box to start routing from your current origin.

- Start navigation
  - When you press “Directions”, the app computes a route using the Google Directions API and renders it on the map.
  - A “Next turn” HUD appears at the top-right with maneuver arrow, instruction text, and distance to the turn.
  - While navigating, the map keeps the user marker in view and zooms to ~18.

- Geolocation and recentering
  - If OS/location services allow, the app uses the browser geolocation to watch your position and heading. An arrow marker shows direction of travel; an accuracy circle indicates GPS accuracy.
  - Use the floating ⌖ button (bottom-right) to recenter on your location and resume follow mode.

- Pickup Planner (VRP)
  - Open via the 📦 button (top-left). The panel slides in.
  - Set Depot:
    - Use Center: use the map’s current center.
    - Locate Me: try GPS; if unavailable, falls back to IP-based rough location; else uses current map center.
    - Or type an address/lat,lng into the depot input; autocomplete is supported.
  - Capacity: set the integer vehicle capacity per trip.
  - Add Pickups:
    - Click Add or Saved to open a modal.
    - Search a place, select it, optionally set a Saved name; Add to Pickups to add a row.
    - Reuse saved locations; or set a saved location as Depot.
  - Manual vs Optimized order:
    - Manual order on: trips will follow the order you entered (capacity splits applied).
    - Manual order off: system optimizes using a travel-time matrix and a greedy heuristic.
  - Calculate: press Calculate to draw colored routes for each trip; see summary and per-leg metrics in the info panel.

- Reordering pickups
  - Drag the ◇ handle in each pickup row to reorder (when visible). Order impacts manual mode and the baseline for optimization.

- Clearing overlays
  - Close the planner or press a Clear/refresh action (if present) to remove routes; or programmatically call `clearVRPRoutes` (see below).


### Internals — How Routing and VRP Work

Terminology:
- Depot: start/end location for each trip (round trip).
- Pickups: intermediate stops with an optional demand (units to collect).
- Capacity: vehicle limit per trip; if total demand exceeds capacity, multiple trips are created.

Pipeline overview:
1) Inputs are read from the panel: depot lat/lng, a list of pickup lat/lng (+ demand), capacity, and the manual-order flag.
2) If manual order is ON → run `splitTripsByCapacityInOrder`:
   - Iterate pickups in given order and “pack” demands sequentially into the current trip until capacity is reached, then start a new trip.
3) If manual order is OFF → build a travel-time matrix among all points (depot plus pickups):
   - First attempt: Google Distance Matrix API (driving, with current departure time).
   - Fallback: Haversine straight-line distance, converted to time by dividing meters by 11.11 (approx 40 km/h). This preserves relative ordering when API is unavailable.
   - With this matrix and per-stop demands, run `solveVRPGreedy`:
     - While there’s remaining demand, begin a new trip at the depot with full capacity.
     - Repeatedly select the next unserved stop with the smallest travel time from current location.
     - Load as much as possible up to remaining capacity; mark demand as served (possibly partially) and move current location to that stop.
     - End trip when capacity is exhausted or no reachable stops remain.
4) Draw trips via `drawTrips`:
   - Preferred: Google Directions API with waypoints (and `optimizeWaypoints=true` in optimized mode) to get a realistic route. Each trip has its own color.
   - Fallback: draw a straight-line polyline through depot → pickups → depot when directions fail.
   - Metrics: If Directions succeed, use leg distance/duration texts. If not, compute approximate texts from Haversine distances and an assumed speed (~40 km/h).
5) Surface results: the right info panel shows per-trip legs (stop names with distance/duration), totals, and return-to-depot leg metrics.

Why greedy VRP?
- It is fast, simple, and avoids bringing in large solvers. It produces sensible routes for small to medium pickup counts, especially with Distance Matrix travel times. For improved optimization, you can replace it with a backend service (e.g., OR-Tools) and feed results to the frontend using the API contract endpoints below.

Error handling and fallbacks:
- Distance Matrix quota/errors → fallback matrix via Haversine.
- Directions route failure → fallback polyline with approximate metrics.
- Geolocation failure → “Locate Me” attempts IP-based fallback; otherwise uses map center.


### Programmatic Control (extended)

Center and zoom:
```
lat, lng, zoom = 51.5072, -0.1276, 13
maps.page().runJavaScript(f"map.setCenter(new google.maps.LatLng({lat},{lng})); map.setZoom({zoom});")
```

Route to a coordinate:
```
maps.page().runJavaScript("routeTo(new google.maps.LatLng(48.8566,2.3522));")
```

Open/close planner panel:
```
maps.page().runJavaScript("document.getElementById('vrpOpen').click();")
maps.page().runJavaScript("document.getElementById('vrpClose').click();")
```

Set depot/pickups via DOM and trigger calculation (no direct JS API is exported):
```
js = r"""
(function(){
  function q(id){return document.getElementById(id)}
  // Ensure panel is open
  q('vrpOpen') && q('vrpOpen').click();
  // Set depot
  q('vrpDepot').value = 'Warehouse';
  q('vrpDepot').dataset.lat = '37.7749';
  q('vrpDepot').dataset.lng = '-122.4194';
  // Set capacity
  q('vrpCapacity').value = '120';
  // Add two pickup rows by simulating the Add button
  q('vrpAdd') && q('vrpAdd').click();
  q('vrpAdd') && q('vrpAdd').click();
  // Fill rows
  var rows = document.querySelectorAll('#vrpList .pickup-row');
  function setRow(row, name, lat, lng, demand){
    var loc = row.querySelector('.vrpLoc');
    var dem = row.querySelector('.vrpDemand');
    if (loc){ loc.value = name; loc.dataset.name=name; loc.dataset.lat=lat; loc.dataset.lng=lng; }
    if (dem){ dem.value = demand; }
  }
  if (rows[0]) setRow(rows[0], 'Pickup A', '37.779','-122.419','60');
  if (rows[1]) setRow(rows[1], 'Pickup B', '37.768','-122.431','80');
  // Optimized order (unchecked = manual order)
  var manual = document.getElementById('vrpManualOrder');
  if (manual) manual.checked = false;
  // Calculate
  document.getElementById('vrpCalc').click();
})();
"""
maps.page().runJavaScript(js)
```

Clear VRP overlays:
```
maps.page().runJavaScript("(window.clearVRPRoutes||function(){})();")
```


### MiniMapWidget (Leaflet)

- Loads Leaflet CSS/JS from unpkg and OpenStreetMap tiles; shows a heading arrow marker that rotates with motion and estimates bearing if heading is missing.
- Interactions like scroll/drag are disabled to keep a compact, static view.
- Requires internet access to CDNs and OSM. For offline/locked environments, bundle Leaflet and point to a self‑hosted tile server.


### Google Cloud Configuration

Enable these APIs in your Google Cloud project (billing required):
- Maps JavaScript API
- Places API
- Directions API
- Distance Matrix API

Key steps:
1) Create project, enable billing.
2) Enable the four APIs above.
3) Create an API key.
4) Restrictions for desktop apps: HTTP referrer checks aren’t effective inside a webview. Apply API restrictions to only the used APIs and set quotas. Rotate keys if leaked. Consider backend proxying if you need tighter control.
5) Provide the key via env var `GOOGLE_MAPS_API_KEY` or pass `api_key` to `MapsWidget`.


## Proposed Backend–Frontend API Contract (HTTP)

Conventions:
- Base URL: `/api`
- Headers: `Content-Type: application/json`, `Authorization: Bearer <token>` where noted
- Success status: `200` unless specified
- Error payload: `{ "error": "Message" }`


### Class: Widget

Represents a UI widget pane (e.g., web music, maps).

```
{
  id: string,              // e.g., "ytmusic" | "maps" | "speedometer"
  name: string,
  type: string,            // "web" | "native"
  visible: boolean,
  meta: object | null
}
```

- GET `/widgets` → `{ "widgets": [ {<widget>}, ... ] }`
- GET `/widgets/:id` → `{ <widget> }` (404/401 on error)
- PATCH `/widgets/:id/visibility` body `{ visible: boolean }` → `{ <widget> }`


### Class: MusicService

```
{
  id: "ytmusic"|"spotify"|"apple"|"soundcloud",
  name: string,
  loggedIn: boolean,
  state: "playing"|"paused"|"stopped",
  trackTitle: string|null,
  artUrl: string|null
}
```

- GET `/music/services` → `{ services: [ {<service>}, ... ] }`
- GET `/music/status` → `{ <service> }`
- POST `/music/service` body `{ id }` → `{ <service> }`
- POST `/music/play|pause|next|prev` → `{ state: ... }`


### Class: MapView

```
{
  id: "maps",
  center: { lat: number, lng: number },
  zoom: number,
  destination: { lat: number, lng: number } | null,
  etaMinutes: number | null,
  apiKeyConfigured: boolean
}
```

- GET `/maps` → `{ <map_view> }`
- POST `/maps/center` body `{ lat, lng, zoom? }` → `{ <map_view> }`
- POST `/maps/destination` body `{ lat, lng }` → `{ <map_view> }`
- GET `/maps/key` → `{ apiKeyConfigured: boolean }`

VRP planner endpoints:
- POST `/maps/vrp/depot` body `{ lat, lng, name? }` → `{ depot: { lat, lng, name } }`
- POST `/maps/vrp/pickups` body `{ pickups: [{ lat, lng, name?, demand? }] }` → `{ pickups: [...] }`
- POST `/maps/vrp/capacity` body `{ capacity: integer }` → `{ capacity }`
- POST `/maps/vrp/calc` body `{ optimize: boolean }` →

```
{
  trips: [
    {
      color: string,
      items: [ { name: string, distanceText: string, durationText: string } ],
      totalMeters: number,
      totalSeconds: number,
      returnDistanceText: string,
      returnDurationText: string
    }
  ]
}
```


### Class: SpeedometerData

```
{
  speedMph: integer,  // 0..300
  powerW: integer
}
```

- GET `/vehicle/speed` → `{ speedMph, powerW }`
- POST `/vehicle/speed` body `{ speedMph }` → `{ speedMph, powerW }`


### Class: System

```
{
  id: string,
  name: string,
  version: string,
  uptimeSec: integer,
  timezone: string
}
```

- GET `/system/health` → `{ status: "ok" }`
- GET `/system/info` → `{ <system> }`
- GET `/system/logs?limit=100` → `{ lines: string[] }`


### Class: Config

```
{
  widgetWidth: integer,
  widgetHeight: integer,
  theme: {
    colorBg: string,
    colorAccent: string,
    colorText: string
  }
}
```

- GET `/config` → `{ <config> }`
- PATCH `/config` body `{ ...partial }` → `{ <config> }`


## Troubleshooting

- Import errors `src.*`: provide a `src` package mapping to repo root or update imports.
- WebEngine blank/crash: ensure `PyQtWebEngine` is present and codecs installed.
- Google Maps: verify API key, APIs enabled, and quotas/billing.
- Boot sound: confirm `Media/SFX/boot.wav` and multimedia backends.


## Repository Structure

```
main.py                             # Entry point; launches the full UI
src/                                # Application package used by main.py
  boot.py, boot_animation.py        # Boot sequence UI/signals (boot currently skipped)
  clock_widget.py, speedometer.py   # Core dashboard widgets
  navbar.py, keyboard.py            # Navigation and virtual keyboard
  widget_config.py                  # Widget sizing constants
  style/                            # Theming and reusable styles
  web_embed/                        # Web views and helpers (music, maps, mini map)
  ytmusic_mini_player.py            # YouTube Music mini player
  debug_logger.py                   # Simple rotating logger
Fonts/, Media/                      # Optional fonts and media assets
cpp_backend/                        # C++ VRP solver (CLI) + CMake build files
requirements.txt                    # Python dependencies (includes PyQtWebEngine, dotenv)
```


## C++ Backend Calculation (VRP)

You can offload the VRP (pickup planner) computation to a native C++ backend for speed and separation of concerns.

What’s provided:
- `cpp_backend/vrp_solver.cpp`: a small CLI app that reads inputs from stdin and prints trip results as JSON.
- `cpp_backend/CMakeLists.txt`: build configuration.
- `src/vrp_cpp.py`: a Python helper to call the solver and (optionally) draw simple polylines on the map.

Build steps (Linux/macOS):
```
cd cpp_backend
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Usage from Python:
```
from src.vrp_cpp import solve_vrp_with_cpp

depot = {"lat": 37.7749, "lng": -122.4194}
pickups = [
  {"name": "Pickup A", "lat": 37.779, "lng": -122.419, "demand": 60},
  {"name": "Pickup B", "lat": 37.768, "lng": -122.431, "demand": 80},
]
res = solve_vrp_with_cpp(depot, pickups, capacity=100, optimize=True)
print(res["trips"])  # list of trips with leg texts and totals
```

Integration with MapsWidget (as used in main.py):
- For full fidelity, take the trip orders from the solver and call the in‑page JavaScript `directionsService.route` for each trip to render real routes and metrics (see the Programmatic Control examples to run JS).
- As a quick approximation, you can draw straight polylines using Google Maps JS. For production, prefer Directions for accurate travel times.

Switching strategy:
- Keep the current in‑page (JS) VRP as a fallback.
- Provide a toggle (env var or config) to choose C++ backend or in‑page logic.
- Optional: implement the VRP endpoints in your backend server; the Qt app can POST pickups/capacity and receive trip data, matching the API contract above.


## License

See `LICENSE`.

