import os
import json
import shutil
import subprocess
from typing import List, Dict, Any, Optional


def _find_solver() -> Optional[str]:
    # Default expected path after CMake build
    candidates = [
        os.environ.get("VRP_SOLVER_PATH"),
        os.path.join(os.getcwd(), "cpp_backend", "build", "vrp_solver"),
        os.path.join(os.getcwd(), "cpp_backend", "vrp_solver"),
    ]
    for c in candidates:
        if c and os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def solve_vrp_with_cpp(
    depot: Dict[str, float],
    pickups: List[Dict[str, Any]],
    capacity: int,
    optimize: bool = True,
    solver_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call the C++ VRP solver CLI with a compact text protocol and return parsed JSON.

    depot: { lat: float, lng: float }
    pickups: [{ name?: str, lat: float, lng: float, demand: int }]
    capacity: vehicle capacity per trip
    optimize: if False, respect input order (manual); if True, greedy optimization
    solver_path: optional explicit path to compiled solver; otherwise auto-detect
    """
    solver = solver_path or _find_solver()
    if not solver:
        raise RuntimeError(
            "vrp_solver not found. Build C++ backend (see docs) or set VRP_SOLVER_PATH."
        )

    def sanitize_name(s: str) -> str:
        return (s or "").replace("|", "/").replace("\n", " ").strip()

    lines = []
    lines.append(f"depot: {depot['lat']},{depot['lng']}")
    lines.append(f"capacity: {int(capacity)}")
    lines.append(f"optimize: {1 if optimize else 0}")
    for p in pickups:
        name = sanitize_name(str(p.get("name", "")))
        lines.append(
            f"pickup: {name}|{float(p['lat'])}|{float(p['lng'])}|{int(p.get('demand', 1))}"
        )

    input_blob = "\n".join(lines) + "\n"

    proc = subprocess.run(
        [solver], input=input_blob.encode("utf-8"), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"vrp_solver failed with code {proc.returncode}: {proc.stderr.decode('utf-8', 'ignore')}"
        )

    out = proc.stdout.decode("utf-8", "ignore")
    try:
        return json.loads(out)
    except Exception as e:
        raise RuntimeError(f"Failed to parse solver JSON: {e}\nOutput was:\n{out}")


def draw_trips_on_maps_widget(maps_widget, trips: List[Dict[str, Any]]):
    """
    Draw simple colored polylines on the current Google Map for each trip.
    This bypasses Directions and uses straight segments between depot->stops->depot.
    """
    # Choose a small color palette to rotate through
    colors = ["#4285F4", "#34A853", "#FBBC05", "#EA4335", "#A142F4", "#00ACC1"]
    js_parts = [
        "try{ if(window._cppTripOverlays){ window._cppTripOverlays.forEach(o=>o.setMap(null)); } window._cppTripOverlays=[]; }catch(e){}"
    ]
    for i, trip in enumerate(trips):
        color = colors[i % len(colors)]
        # Reconstruct a basic path from legs: we need depot -> leg1 stop -> leg2 stop ... -> depot
        # The page does not expose depot coords, so we only connect consecutive legs (approximate).
        # For better fidelity, you can extend the solver to also return coordinates of each stop.
        path_js = []
        # The solver JSON contains only leg texts. In a production setup, include lat/lng per stop.
        # Here, we no-op if coordinates are missing.
        # Kept for completeness; users can adapt this to pass coordinates.
        #
        # Example expected structure to draw:
        # path_js = [ "new google.maps.LatLng(37.77,-122.41)", ... ]
        if not path_js:
            continue
        js_parts.append(
            "(function(){ var pl = new google.maps.Polyline({path:[" + ",".join(path_js) + 
            f"], strokeColor:'{color}', strokeOpacity:1.0, strokeWeight:5, geodesic:true}}); pl.setMap(map); (window._cppTripOverlays||(window._cppTripOverlays=[])).push(pl); } )();"
        )

    if js_parts:
        maps_widget.page().runJavaScript("\n".join(js_parts))

