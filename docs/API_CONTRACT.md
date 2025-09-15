# Proposed Backend–Frontend API Contract (HTTP)

This contract spec proposes a simple REST interface the backend can expose so a PyQt frontend (this repo) can control and observe the UI state. It follows the style and sections from the provided template.


## Conventions
- Base URL: `/api`
- Headers: `Content-Type: application/json`, `Authorization: Bearer <token>` where noted
- Success status: `200` unless otherwise specified
- Error payload: `{ "error": "Message" }`


## Class: Widget
Represents a UI widget pane (e.g., YouTube Music, Maps, Speedometer panel visibility, etc.).

```
{
  id: string,              // e.g., "ytmusic" | "maps" | "speedometer"
  name: string,            // Human-friendly name
  type: string,            // "web" | "native"
  visible: boolean,
  meta: object | null      // arbitrary widget metadata
}
```

GET /widgets — List widgets
- URL Params: None
- Data Params: None
- Headers: Content-Type: application/json
- Success Response: 200
- Content: `{ "widgets": [ {<widget_object>}, ... ] }`

GET /widgets/:id — Get a widget
- URL Params: Required: `id = [string]`
- Data Params: None
- Headers: Content-Type: application/json Authorization: Bearer
- Success Response: 200
- Content: `{ <widget_object> }`
- Error Responses: 404 / 401

PATCH /widgets/:id/visibility — Show/hide a widget
- URL Params: Required: `id = [string]`
- Data Params: `{ visible: boolean }`
- Headers: Content-Type: application/json Authorization: Bearer
- Success Response: 200
- Content: `{ <widget_object> }` (updated)
- Error Responses: 404 / 401 / 422 (invalid body)


## Class: MusicService
Represents the music service integration and playback state.

```
{
  id: string,                 // "ytmusic" | "spotify" | "apple" | "soundcloud"
  name: string,               // "YouTube Music" | ...
  loggedIn: boolean,
  state: "playing" | "paused" | "stopped",
  trackTitle: string | null,
  artUrl: string | null
}
```

GET /music/services — Available services
- URL Params: None
- Data Params: None
- Headers: Content-Type: application/json
- Success Response: 200
- Content: `{ "services": [ {<music_service_object>}, ... ] }`

GET /music/status — Current playback summary
- URL Params: None
- Data Params: None
- Headers: Content-Type: application/json
- Success Response: 200
- Content: `{ <music_service_object> }`

POST /music/service — Switch active service
- URL Params: None
- Data Params: `{ id: "ytmusic" | "spotify" | "apple" | "soundcloud" }`
- Headers: Content-Type: application/json Authorization: Bearer
- Success Response: 200
- Content: `{ <music_service_object> }` (active)
- Error Responses: 404 / 401 / 422

POST /music/play
- Data Params: None
- Headers: Authorization: Bearer
- Success Response: 200 `{ state: "playing" }`

POST /music/pause
- Success Response: 200 `{ state: "paused" }`

POST /music/next
- Success Response: 200 `{ state: "playing" }`

POST /music/prev
- Success Response: 200 `{ state: "playing" }`


## Class: MapView
Represents the map state for the Maps widget.

```
{
  id: string,                 // "maps"
  center: { lat: number, lng: number },
  zoom: number,
  destination: { lat: number, lng: number } | null,
  etaMinutes: number | null,
  apiKeyConfigured: boolean
}
```

GET /maps — Map view state
- Headers: Content-Type: application/json
- Success: 200 `{ <map_view_object> }`

POST /maps/center — Set center
- Data Params: `{ lat: number, lng: number, zoom?: number }`
- Headers: Authorization: Bearer
- Success: 200 `{ <map_view_object> }`
- Error: 422 (invalid lat/lng)

POST /maps/destination — Set destination
- Data Params: `{ lat: number, lng: number }`
- Headers: Authorization: Bearer
- Success: 200 `{ <map_view_object> }`

GET /maps/key — API key status
- Success: 200 `{ "apiKeyConfigured": true | false }`

POST /maps/vrp/depot — Set depot
- Data Params: `{ lat: number, lng: number, name?: string }`
- Headers: Authorization: Bearer
- Success: 200 `{ depot: { lat, lng, name } }`

POST /maps/vrp/pickups — Replace pickup list
- Data Params: `{ pickups: [{ lat: number, lng: number, name?: string, demand?: number }] }`
- Headers: Authorization: Bearer
- Success: 200 `{ pickups: [...] }`

POST /maps/vrp/capacity — Set vehicle capacity
- Data Params: `{ capacity: integer }`
- Headers: Authorization: Bearer
- Success: 200 `{ capacity: integer }`
- Error: 422 (invalid capacity)

POST /maps/vrp/calc — Calculate routes
- Data Params: `{ optimize: boolean }  // false = respect manual order`
- Headers: Authorization: Bearer
- Success: 200
- Content:
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
    },
    ...
  ]
}
```
- Error: 422 (invalid data) / 429 (quota exceeded)



## Class: SpeedometerData
Represents vehicle speed/power values shown by the speedometer widget.

```
{
  speedMph: integer,         // 0..300
  powerW: integer
}
```

GET /vehicle/speed — Current speed/power
- Success: 200 `{ "speedMph": 65, "powerW": 650 }`

POST /vehicle/speed — Update speed
- Data Params: `{ speedMph: integer }`
- Headers: Authorization: Bearer
- Success: 200 `{ "speedMph": 70, "powerW": 700 }`
- Error: 422 (out of range)


## Class: System
General application/system status.

```
{
  id: string,              // e.g., host or device id
  name: string,            // device name
  version: string,         // app version/build
  uptimeSec: integer,
  timezone: string
}
```

GET /system/health — Basic health
- Success: 200 `{ status: "ok" }`

GET /system/info — App/device info
- Success: 200 `{ <system_object> }`

GET /system/logs — Recent log lines
- Query: `?limit=100`
- Success: 200 `{ lines: string[] }`
- Error: 401 (if protected)


## Class: Config
UI configuration and theme values that can be read and adjusted at runtime.

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

GET /config — Current config
- Success: 200 `{ <config_object> }`

PATCH /config — Update config
- Data Params: partial fields, e.g., `{ widgetWidth: 1280 }`
- Headers: Authorization: Bearer
- Success: 200 `{ <config_object> }`
- Error: 422 (invalid values)


## Notes on frontend bindings
- Widget visibility: the frontend must ensure only one non-map web embed is visible at a time (mirrors `WebEmbedManager` semantics). Backend visibility commands should therefore close the currently open web widget before opening a new one.
- Music control: the frontend translates play/pause/next/prev into JavaScript actions in a `QWebEngineView` (see `ytmusic_mini_player.py` and `web_embed/*`). Responses should reflect best-effort state.
- Maps: setting center/destination updates `QWebEngineView` HTML/JS; ETA can be computed server-side or omitted.
