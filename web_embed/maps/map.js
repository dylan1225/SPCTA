let map,
  directionsService,
  directionsRenderer,
  origin = null,
  userMarker = null,
  navigating = false,
  placesService,
  geocoder,
  vrpRenderers = [],
  initialGeoCentered = false,
  accuracyCircle = null,
  savedLocations = [],
  vrpSelectedPlace = null;

function toRad(d) {
  return (d * Math.PI) / 180;
}

function dist(a, b) {
  const φ1 = toRad(a.lat),
    φ2 = toRad(b.lat),
    dφ = φ2 - φ1,
    dλ = toRad(b.lng - a.lng),
    h =
      Math.sin(dφ / 2) ** 2 +
      Math.cos(φ1) * Math.cos(φ2) * Math.sin(dλ / 2) ** 2;
  return 2 * 6371000 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}

function bearing(a, b) {
  const φ1 = toRad(a.lat),
    φ2 = toRad(b.lat),
    y = Math.sin(toRad(b.lng - a.lng)) * Math.cos(φ2),
    x =
      Math.cos(φ1) * Math.sin(φ2) -
      Math.sin(φ1) * Math.cos(φ2) * Math.cos(toRad(b.lng - a.lng));
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

function updateUser(lat, lng, hd = 0, accuracy = null) {
  const pos = { lat, lng };
  const icon = {
    path: "M 0 -26 L 8 0 L 0 -8 L -8 0 Z", // chevron-like arrow
    fillColor: "#1a73e8",
    fillOpacity: 1,
    strokeColor: "#ffffff",
    strokeWeight: 2,
    rotation: hd,
    scale: 1,
  };
  if (!userMarker) {
    userMarker = new google.maps.Marker({
      map,
      position: pos,
      icon,
      clickable: false,
      zIndex: 9999,
    });
  } else {
    userMarker.setPosition(pos);
    userMarker.setIcon(icon);
    try { userMarker.setZIndex(9999); } catch(_) {}
  }

  if (typeof accuracy === 'number' && isFinite(accuracy)) {
    if (!accuracyCircle) {
      accuracyCircle = new google.maps.Circle({
        map,
        center: pos,
        radius: Math.max(accuracy, 5),
        strokeColor: "#1a73e8",
        strokeOpacity: 0.5,
        strokeWeight: 1,
        fillColor: "#1a73e8",
        fillOpacity: 0.15,
        clickable: false,
        zIndex: 1,
      });
    } else {
      accuracyCircle.setCenter(pos);
      accuracyCircle.setRadius(Math.max(accuracy, 5));
    }
  }
  if (navigating) {
    map.panTo(pos);
    map.setZoom(18);
  }
}

function recenter() {
  if (origin) {
    navigating = true;
    map.panTo(origin);
    map.setZoom(18);
  }
}

function rotateCW() {
  map.setHeading(((map.getHeading() || 0) + 90) % 360);
}

async function searchPlaces() {
  const q = document.getElementById("dest").value.trim();
  if (!q) return;

  const results = document.getElementById("results");
  results.innerHTML = "";
  results.style.display = "block";

  try {
    placesService.textSearch({ query: q }, (pls, status) => {
      if (status !== google.maps.places.PlacesServiceStatus.OK) {
        results.innerHTML = '<div class="res">No results found</div>';
        return;
      }
      if (!pls || pls.length === 0) {
        results.innerHTML = '<div class="res">No results found</div>';
        return;
      }
      pls.forEach((pl) => {
        const div = document.createElement("div");
        div.className = "res";
        div.textContent = pl.name;
        div.onclick = () => {
          results.style.display = "none";
          showInfo(pl.place_id, pl.geometry.location);
        };
        results.appendChild(div);
      });
    });
  } catch (error) {
    console.error("Search error:", error);
    results.innerHTML = '<div class="res">Search service unavailable</div>';
  }
}

function showInfo(placeId, location) {
  try {
    placesService.getDetails(
      {
        placeId: placeId,
        fields: [
          "name",
        "formatted_address",
        "formatted_phone_number",
        "rating",
        "user_ratings_total",
        "opening_hours",
        "geometry",
        "photos",
        "types",
      ],
    },
    (place, status) => {
      if (status !== google.maps.places.PlacesServiceStatus.OK) return;

      const box = document.getElementById("infoBox");
      box.innerHTML = "";

      if (place.photos && place.photos.length) {
        const img = document.createElement("img");
        img.src = place.photos[0].getUrl({ maxWidth: 300 });
        box.appendChild(img);
      }

      const d = document.createElement("div");
      d.className = "details";

      const h2 = document.createElement("h2");
      h2.textContent = place.name;
      d.appendChild(h2);

      if (place.rating != null) {
        const rd = document.createElement("div");
        rd.className = "rating";
        rd.textContent =
          place.rating + " ★ (" + (place.user_ratings_total || 0) + ")";
        d.appendChild(rd);
      }

      if (place.types && place.types.length) {
        const t = document.createElement("p");
        t.textContent = place.types[0].replace(/_/g, " ");
        d.appendChild(t);
      }

      if (place.formatted_address) {
        const a = document.createElement("p");
        a.textContent = place.formatted_address;
        d.appendChild(a);
      }

      if (place.formatted_phone_number) {
        const p = document.createElement("p");
        p.textContent = place.formatted_phone_number;
        d.appendChild(p);
      }

      box.appendChild(d);

      const btn = document.createElement("button");
      btn.className = "directions-btn";
      btn.textContent = "Directions";
      btn.onclick = () => {
        box.style.display = "none";
        routeTo(location);
      };
      box.appendChild(btn);

      box.style.display = "block";
    }
  );
  } catch (error) {
    console.error("Place details error:", error);
    const box = document.getElementById("infoBox");
    box.innerHTML = '<div class="details"><h2>Error</h2><p>Unable to load place details</p></div>';
    box.style.display = "block";
  }
}

function routeTo(dest) {
  navigating = true;
  directionsService
    .route({
      origin: origin || map.getCenter(),
      destination: dest,
      travelMode: google.maps.TravelMode.DRIVING,
    })
    .then((r) => {
      directionsRenderer.setDirections(r);
      displayNextTurn(r.routes[0].legs[0].steps[0]);
    })
    .catch(console.error);
}

function displayNextTurn(step) {
  const box = document.getElementById("nextTurn"),
    arc = step.maneuver || "",
    arrow = arc.includes("left") ? "←" : arc.includes("right") ? "→" : "↑",
    text = step.instructions.replace(/<[^>]+>/g, ""),
    distMi = (step.distance.value / 1609.34).toFixed(2) + " mi";

  box.innerHTML = `<span class="arrow">${arrow}</span> ${text} — ${distMi}`;
  box.style.display = "block";
}

function init() {
  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: INITIAL_LAT, lng: INITIAL_LNG },
    zoom: 18,
    minZoom: 5,
    gestureHandling: "greedy",
    mapId: MAP_ID,
  });

  directionsService = new google.maps.DirectionsService();
  directionsRenderer = new google.maps.DirectionsRenderer({
    map,
    polylineOptions: { strokeWeight: 6 },
  });

  try {
    placesService = new google.maps.places.PlacesService(map);
  } catch (error) {
    console.warn("PlacesService initialization failed:", error);
    placesService = {
      textSearch: function(request, callback) {
        callback([], google.maps.places.PlacesServiceStatus.UNKNOWN_ERROR);
      },
      getDetails: function(request, callback) {
        callback(null, google.maps.places.PlacesServiceStatus.UNKNOWN_ERROR);
      }
    };
  }

  try {
    geocoder = new google.maps.Geocoder();
  } catch (e) {
    geocoder = null;
  }




  try { document.getElementById("recenter").onclick = recenter; } catch(_) {}
  document.getElementById("go").onclick = searchPlaces;
  document.getElementById("dest").addEventListener("keydown", (e) => {
    if (e.key === "Enter") searchPlaces();
  });

  initVRPPanel();
  updatePlannerVisibility();
  try { window.addEventListener('resize', updatePlannerVisibility); } catch(_) {}
  try {
    const ro = new ResizeObserver(() => updatePlannerVisibility());
    const mapEl = document.getElementById('map');
    if (mapEl) ro.observe(mapEl);
  } catch(_) {}

  try { startGeoWatch(); } catch (_) {}
}

function initVRPPanel() {
  const depotInput = document.getElementById('vrpDepot');
  const useCenterBtn = document.getElementById('vrpUseCenter');
  const locateMeBtn = document.getElementById('vrpLocateMe');
  const addBtn = document.getElementById('vrpAdd');
  const savedBtn = document.getElementById('vrpSavedBtn');
  const calcBtn = document.getElementById('vrpCalc');
  const list = document.getElementById('vrpList');
  const cap = document.getElementById('vrpCapacity');
  const closeBtn = document.getElementById('vrpClose');
  const openBtn = document.getElementById('vrpOpen');
  const panel = document.getElementById('vrpPanel');
  const modal = document.getElementById('vrpAddModal');
  const modalClose = document.getElementById('vrpCloseModal');
  const modalSearch = document.getElementById('vrpSearch');
  const modalSearchBtn = document.getElementById('vrpSearchBtn');
  const modalResults = document.getElementById('vrpSearchResults');
  const modalInfo = document.getElementById('vrpPlaceInfo');
  const modalPlaceName = document.getElementById('vrpPlaceName');
  const modalAddSelected = document.getElementById('vrpAddSelected');
  const modalSaveSelected = document.getElementById('vrpSaveSelected');
  const modalSavedList = document.getElementById('vrpSavedList');

  depotInput.value = `${map.getCenter().lat().toFixed(5)}, ${map.getCenter().lng().toFixed(5)}`;

  try {
    if (google.maps.places && google.maps.places.Autocomplete) {
      const ac = new google.maps.places.Autocomplete(depotInput, { fields: ['geometry'] });
      ac.addListener('place_changed', () => {
        const p = ac.getPlace();
        if (p && p.geometry && p.geometry.location) {
          const ll = p.geometry.location;
          map.setCenter(ll);
          depotInput.dataset.lat = ll.lat();
          depotInput.dataset.lng = ll.lng();
        }
      });
    }
  } catch (_) {}

  useCenterBtn.onclick = () => {
    const c = map.getCenter();
    depotInput.value = `${c.lat().toFixed(6)}, ${c.lng().toFixed(6)}`;
    depotInput.dataset.lat = c.lat();
    depotInput.dataset.lng = c.lng();
  };
  locateMeBtn.onclick = async () => {
    const onFound = (lat, lng) => {
      try {
        const p = new google.maps.LatLng(lat, lng);
        map.setCenter(p);
      } catch (_) {}
      depotInput.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
      depotInput.dataset.lat = lat;
      depotInput.dataset.lng = lng;
    };
    if (navigator.geolocation && navigator.geolocation.getCurrentPosition) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const { latitude, longitude } = pos.coords;
          onFound(latitude, longitude);
        },
        async () => {
          try {
            const res = await fetch('https://ipapi.co/json/');
            const j = await res.json();
            if (j && j.latitude && j.longitude) {
              onFound(+j.latitude, +j.longitude);
              return;
            }
          } catch (_) {}
          const c = map.getCenter();
          onFound(c.lat(), c.lng());
        },
        { enableHighAccuracy: false, timeout: 7000, maximumAge: 60000 }
      );
      return;
    }
    try {
      const res = await fetch('https://ipapi.co/json/');
      const j = await res.json();
      if (j && j.latitude && j.longitude) {
        onFound(+j.latitude, +j.longitude);
        return;
      }
    } catch (_) {}
    const c = map.getCenter();
    onFound(c.lat(), c.lng());
  };

  addBtn.onclick = () => openVRPAddModal();
  savedBtn.onclick = () => openVRPAddModal();
  calcBtn.onclick = () => calculateVRP();

  function showPanel(show) {
    if (show) {
      panel.style.display = 'block';
      openBtn.style.display = 'none';
    } else {
      panel.style.display = 'none';
      openBtn.style.display = 'block';
    }
  }
  closeBtn.onclick = () => showPanel(false);
  openBtn.onclick = () => showPanel(true);

  addPickupRow();
  setupDragAndDrop();

  function loadSavedLocations() {
    try { savedLocations = JSON.parse(localStorage.getItem('vrpSavedLocations')||'[]'); } catch(_) { savedLocations=[]; }
    if (!Array.isArray(savedLocations)) savedLocations=[];
  }
  function storeSavedLocations() {
    try { localStorage.setItem('vrpSavedLocations', JSON.stringify(savedLocations)); } catch(_) {}
  }
  function addSavedLocation(item) {
    loadSavedLocations();
    if (!savedLocations.some(s => s.name===item.name && Math.abs(s.lat-item.lat)<1e-6 && Math.abs(s.lng-item.lng)<1e-6)) {
      savedLocations.push({ name: item.name, lat: item.lat, lng: item.lng, place_id: item.place_id||'' });
      storeSavedLocations();
    }
  }

  function openVRPAddModal() {
    if (!modal) return;
    modal.style.display = 'flex';
    vrpSelectedPlace = null;
    if (modalInfo) modalInfo.innerHTML = '';
    if (modalResults) modalResults.innerHTML = '';
    if (modalPlaceName) modalPlaceName.value = '';
    renderSavedList();
    try { modalSearch && modalSearch.focus(); } catch(_){}
  }
  function closeVRPAddModal() { if (modal) modal.style.display = 'none'; }
  if (modalClose) modalClose.onclick = closeVRPAddModal;
  function runVRPSearch() {
    const q = (modalSearch?.value||'').trim();
    if (modalResults) modalResults.innerHTML = '';
    if (modalInfo) modalInfo.innerHTML = '';
    vrpSelectedPlace = null;
    if (!q) return;
    try {
      placesService.textSearch({ query: q }, (pls, status) => {
        if (status !== google.maps.places.PlacesServiceStatus.OK || !pls?.length) {
          if (modalResults) modalResults.innerHTML = '<div class="res">No results found</div>';
          return;
        }
        pls.forEach((pl) => {
          const div = document.createElement('div');
          div.className = 'res';
          div.textContent = pl.name;
          div.onclick = () => loadVRPPlaceInfo(pl.place_id, pl.geometry?.location);
          modalResults && modalResults.appendChild(div);
        });
      });
    } catch (e) {
      if (modalResults) modalResults.innerHTML = '<div class="res">Search unavailable</div>';
    }
  }
  if (modalSearchBtn) modalSearchBtn.onclick = runVRPSearch;
  if (modalSearch) modalSearch.addEventListener('keydown', (e)=>{ if (e.key==='Enter') runVRPSearch(); });
  function loadVRPPlaceInfo(placeId) {
    try {
      placesService.getDetails({ placeId, fields: ['name','formatted_address','formatted_phone_number','rating','user_ratings_total','opening_hours','geometry','photos'] }, (place, status) => {
        if (status !== google.maps.places.PlacesServiceStatus.OK) return;
        vrpSelectedPlace = place;
        if (modalPlaceName) modalPlaceName.value = place.name || '';
        if (modalInfo) {
          modalInfo.innerHTML = '';
          const box = document.createElement('div');
          const img = (place.photos && place.photos.length) ? `<img style="width:100%;border-radius:8px;" src="${place.photos[0].getUrl({maxWidth:600})}">` : '';
          box.innerHTML = `${img}<div style="padding:8px 0;"><div style=\"font-size:16px;font-weight:600;\">${escapeHtml(place.name||'')}</div>${place.rating!=null?`<div style=\"font-size:12px;color:#bbb;\">${place.rating} ★ (${place.user_ratings_total||0})</div>`:''}${place.formatted_address?`<div style=\"font-size:13px;color:#ddd;\">${escapeHtml(place.formatted_address)}</div>`:''}${place.formatted_phone_number?`<div style=\"font-size:13px;color:#ddd;\">${escapeHtml(place.formatted_phone_number)}</div>`:''}</div>`;
          modalInfo.appendChild(box);
        }
      });
    } catch (_) {}
  }
  if (modalAddSelected) modalAddSelected.onclick = () => {
    if (!vrpSelectedPlace || !vrpSelectedPlace.geometry || !vrpSelectedPlace.geometry.location) return;
    const ll = vrpSelectedPlace.geometry.location;
    const row = addPickupRow();
    const locInput = row.querySelector('.vrpLoc');
    if (locInput) {
      locInput.dataset.lat = ll.lat();
      locInput.dataset.lng = ll.lng();
      const nm = (modalPlaceName?.value || vrpSelectedPlace.name || '').trim();
      locInput.dataset.name = nm;
      locInput.value = nm || (vrpSelectedPlace.formatted_address || '');
    }
    closeVRPAddModal();
  };
  if (modalSaveSelected) modalSaveSelected.onclick = () => {
    if (!vrpSelectedPlace || !vrpSelectedPlace.geometry || !vrpSelectedPlace.geometry.location) return;
    const ll = vrpSelectedPlace.geometry.location;
    const name = (modalPlaceName?.value||'').trim() || vrpSelectedPlace.name || '';
    if (!name) return;
    addSavedLocation({ name, lat: ll.lat(), lng: ll.lng(), place_id: vrpSelectedPlace.place_id || '' });
    renderSavedList();
  };
  function renderSavedList() {
    loadSavedLocations();
    if (!modalSavedList) return;
    modalSavedList.innerHTML = '';
    if (!savedLocations.length) { modalSavedList.innerHTML = '<div class="saved-item"><div>No saved locations yet.</div></div>'; return; }
    savedLocations.forEach((it, idx) => {
      const div = document.createElement('div');
      div.className = 'saved-item';
      div.innerHTML = `<div><div>${escapeHtml(it.name)}</div><div class=\"meta\">${it.lat.toFixed(6)}, ${it.lng.toFixed(6)}</div></div><div><button class=\"btn\" data-act=\"use\" data-idx=\"${idx}\">Use</button> <button class=\"btn\" data-act=\"depot\" data-idx=\"${idx}\">Set as Depot</button> <button class=\"btn\" data-act=\"del\" data-idx=\"${idx}\">Delete</button></div>`;
      modalSavedList.appendChild(div);
    });
    modalSavedList.querySelectorAll('button').forEach(btn => {
      btn.onclick = () => {
        const act = btn.getAttribute('data-act');
        const i = +btn.getAttribute('data-idx');
        if (act === 'use') {
          const s = savedLocations[i];
          const row = addPickupRow();
          const locInput = row.querySelector('.vrpLoc');
          if (locInput) {
            locInput.dataset.lat = s.lat;
            locInput.dataset.lng = s.lng;
            locInput.dataset.name = s.name;
            locInput.value = s.name;
          }
          closeVRPAddModal();
        } else if (act === 'depot') {
          const s = savedLocations[i];
          depotInput.dataset.lat = s.lat;
          depotInput.dataset.lng = s.lng;
          depotInput.value = s.name;
          try { map.setCenter(new google.maps.LatLng(s.lat, s.lng)); } catch(_){}
        } else if (act === 'del') {
          savedLocations.splice(i,1);
          storeSavedLocations();
          renderSavedList();
        }
      };
    });
  }
}

function addPickupRow() {
  const list = document.getElementById('vrpList');
  const row = document.createElement('div');
  row.className = 'pickup-row';
  row.innerHTML = `
    <div class="drag-handle" title="Drag">⋮⋮</div>
    <input type="text" class="vrpLoc" placeholder="Location (address or lat,lng)">
    <input type="number" class="vrpQty" placeholder="Units" min="1" step="1" value="10">
    <button class="mini-btn" title="Remove">✕</button>
  `;
  const [handle, locInput, qtyInput, removeBtn] = row.children;

  try {
    if (google.maps.places && google.maps.places.Autocomplete) {
      const ac = new google.maps.places.Autocomplete(locInput, { fields: ['geometry', 'name'] });
      ac.addListener('place_changed', () => {
        const p = ac.getPlace();
        if (p && p.geometry && p.geometry.location) {
          locInput.dataset.lat = p.geometry.location.lat();
          locInput.dataset.lng = p.geometry.location.lng();
          locInput.dataset.name = p.name || locInput.value;
        }
      });
    }
  } catch (_) {}

  removeBtn.onclick = () => {
    list.removeChild(row);
  };

  list.appendChild(row);
  wireRowDrag(row);
  return row;
}

function setupDragAndDrop() {
  const list = document.getElementById('vrpList');
  if (!list) return;
  list.addEventListener('dragover', (e) => {
    e.preventDefault();
    const after = getDragAfterElement(list, e.clientY);
    const dragging = list.querySelector('.pickup-row.dragging');
    if (!dragging) return;
    if (after == null) list.appendChild(dragging);
    else list.insertBefore(dragging, after);
  });
}

function wireRowDrag(row) {
  const handle = row.querySelector('.drag-handle');
  if (!handle) return;
  const enable = () => row.setAttribute('draggable', 'true');
  handle.addEventListener('mousedown', enable);
  handle.addEventListener('touchstart', enable, { passive: true });
  row.addEventListener('dragstart', () => row.classList.add('dragging'));
  row.addEventListener('dragend', () => { row.classList.remove('dragging'); row.removeAttribute('draggable'); });
}

function getDragAfterElement(container, y) {
  const els = Array.from(container.querySelectorAll('.pickup-row:not(.dragging)'));
  let closest = { offset: Number.NEGATIVE_INFINITY, element: null };
  for (const child of els) {
    const box = child.getBoundingClientRect();
    const offset = y - box.top - box.height / 2;
    if (offset < 0 && offset > closest.offset) {
      closest = { offset, element: child };
    }
  }
  return closest.element;
}

function parseLatLng(text) {
  const m = String(text).split(',');
  if (m.length === 2) {
    const lat = parseFloat(m[0].trim());
    const lng = parseFloat(m[1].trim());
    if (isFinite(lat) && isFinite(lng)) return { lat, lng };
  }
  return null;
}

function readVRPInputs() {
  const depotInput = document.getElementById('vrpDepot');
  const cap = document.getElementById('vrpCapacity');
  const rows = Array.from(document.querySelectorAll('#vrpList .pickup-row'));

  let depotLL = null;
  if (depotInput.dataset.lat && depotInput.dataset.lng) {
    depotLL = { lat: +depotInput.dataset.lat, lng: +depotInput.dataset.lng };
  } else {
    depotLL = parseLatLng(depotInput.value);
  }
  if (!depotLL) {
    const c = map.getCenter();
    depotLL = { lat: c.lat(), lng: c.lng() };
  }

  const capacity = Math.max(1, Math.floor(+cap.value || 0));

  const pickups = [];
  for (const r of rows) {
    const locInput = r.querySelector('.vrpLoc');
    const qtyInput = r.querySelector('.vrpQty');
    const qty = Math.max(0, Math.floor(+qtyInput.value || 0));
    if (!qty) continue;
    let ll = null;
    if (locInput.dataset.lat && locInput.dataset.lng) {
      ll = { lat: +locInput.dataset.lat, lng: +locInput.dataset.lng };
    } else {
      ll = parseLatLng(locInput.value);
    }
    if (!ll) continue;
    pickups.push({ name: locInput.dataset.name || locInput.value || `L${pickups.length+1}`, lat: ll.lat, lng: ll.lng, demand: qty });
  }

  return { depotLL, capacity, pickups };
}

async function calculateVRP() {
  const summary = document.getElementById('vrpSummary');
  summary.textContent = 'Calculating…';

  clearVRPRoutes();
  setVRPInfo([]);
  try { directionsRenderer && directionsRenderer.set('directions', null); } catch (_) {}

  const { depotLL, capacity, pickups } = readVRPInputs();
  if (!pickups.length) {
    summary.textContent = 'Add at least one pickup location.';
    return;
  }

  const points = [depotLL, ...pickups.map(p => ({ lat: p.lat, lng: p.lng }))];

  const manual = !!document.getElementById('vrpManualOrder')?.checked;
  let trips;
  if (manual) {
    trips = splitTripsByCapacityInOrder(pickups.map(p=>p.demand), capacity);
  } else {
    let matrix;
    try {
      matrix = await buildDurationMatrix(points);
    } catch (e) {
      console.warn('DistanceMatrix failed, falling back to haversine distances.', e);
      matrix = buildHaversineMatrix(points);
    }
    trips = solveVRPGreedy(matrix, pickups.map(p => p.demand), capacity);
  }

  await drawTrips(trips, depotLL, pickups, !manual);

  const totalTrips = trips.length;
  const totalStops = trips.reduce((a,t)=>a+t.length,0);
  summary.textContent = `Trips: ${totalTrips} • Stops (with repeats across trips): ${totalStops}`;
}

function buildHaversineMatrix(points) {
  const n = points.length;
  const M = Array.from({length:n}, ()=>Array(n).fill(0));
  for (let i=0;i<n;i++) {
    for (let j=0;j<n;j++) {
      if (i===j) { M[i][j]=0; continue; }
      const dM = dist(points[i], points[j]);
      M[i][j] = dM / 11.11; // seconds
    }
  }
  return M;
}

function buildDurationMatrix(points) {
  return new Promise((resolve, reject) => {
    if (!google.maps || !google.maps.DistanceMatrixService) {
      reject(new Error('DistanceMatrixService unavailable'));
      return;
    }
    const svc = new google.maps.DistanceMatrixService();
    const origins = points.map(p => new google.maps.LatLng(p.lat, p.lng));
    const destinations = origins;
    svc.getDistanceMatrix({
      origins,
      destinations,
      travelMode: google.maps.TravelMode.DRIVING,
      drivingOptions: { departureTime: new Date() },
    }, (res, status) => {
      if (status !== 'OK' || !res || !res.rows) {
        reject(new Error('Bad DistanceMatrix response'));
        return;
      }
      const n = points.length;
      const M = Array.from({length:n}, ()=>Array(n).fill(0));
      for (let i=0;i<n;i++) {
        const row = res.rows[i].elements;
        for (let j=0;j<n;j++) {
          const el = row[j];
          M[i][j] = el && el.duration && el.duration.value ? el.duration.value : (i===j?0:Infinity);
        }
      }
      resolve(M);
    });
  });
}

function solveVRPGreedy(matrix, demands, capacity) {
  const n = demands.length; // nodes (excluding depot)
  const remaining = demands.slice();
  const trips = [];

  function anyRemaining() {
    return remaining.some(x => x > 0);
  }

  while (anyRemaining()) {
    let capLeft = capacity;
    let cur = 0; // start at depot
    const trip = [];

    while (capLeft > 0 && anyRemaining()) {
      let bestIdx = -1, bestTime = Infinity;
      for (let i=0;i<n;i++) {
        if (remaining[i] <= 0) continue;
        const t = matrix[cur][i+1];
        if (t < bestTime) { bestTime = t; bestIdx = i; }
      }
      if (bestIdx === -1 || !isFinite(bestTime)) break;

      const amt = Math.min(remaining[bestIdx], capLeft);
      remaining[bestIdx] -= amt;
      capLeft -= amt;
      if (!trip.includes(bestIdx)) trip.push(bestIdx);
      cur = bestIdx + 1;
    }
    trips.push(trip); // trip is list of node indices (0..n-1)
  }

  return trips;
}

function splitTripsByCapacityInOrder(demands, capacity) {
  const n = demands.length;
  const remaining = demands.slice();
  const trips = [];
  let capLeft = capacity;
  let trip = [];
  for (let i = 0; i < n; i++) {
    while (remaining[i] > 0) {
      if (capLeft === 0) {
        if (trip.length) trips.push(trip);
        trip = [];
        capLeft = capacity;
      }
      const take = Math.min(remaining[i], capLeft);
      remaining[i] -= take;
      if (!trip.includes(i)) trip.push(i);
      capLeft -= take;
    }
  }
  if (trip.length) trips.push(trip);
  return trips;
}

async function drawTrips(trips, depotLL, pickups, optimizeWaypoints=true) {
  clearVRPRoutes();

  const colors = ['#4285F4', '#34A853', '#FBBC05', '#EA4335', '#A142F4', '#00ACC1'];
  const tripsInfo = [];

  for (let t=0; t<trips.length; t++) {
    const idxs = trips[t];
    if (!idxs.length) continue;
    const waypoints = idxs.map(i => ({ location: new google.maps.LatLng(pickups[i].lat, pickups[i].lng), stopover: true }));
    try {
      const result = await directionsService.route({
        origin: depotLL,
        destination: depotLL,
        waypoints,
        optimizeWaypoints: optimizeWaypoints,
        travelMode: google.maps.TravelMode.DRIVING,
      });
      const dr = new google.maps.DirectionsRenderer({
        map,
        suppressMarkers: false,
        polylineOptions: { strokeWeight: 6, strokeColor: colors[t % colors.length] },
        preserveViewport: true,
      });
      dr.setDirections(result);
      vrpRenderers.push({ overlay: dr });

      try {
        const route = result.routes && result.routes[0];
        if (route) {
          const order = route.waypoint_order || idxs.map((_, i)=>i);
          const legs = route.legs || [];
          let totalMeters = 0, totalSeconds = 0;
          const items = [];
          for (let k = 0; k < order.length; k++) {
            const stopIdxInPickups = idxs[order[k]];
            const stopName = pickups[stopIdxInPickups]?.name || `Stop ${k+1}`;
            const leg = legs[k];
            if (leg && leg.distance && leg.duration) {
              items.push({ name: stopName, distanceText: leg.distance.text, durationText: leg.duration.text });
              totalMeters += leg.distance.value || 0;
              totalSeconds += leg.duration.value || 0;
            }
          }
          const retLeg = legs[order.length];
          let returnDistanceText = '', returnDurationText = '';
          if (retLeg && retLeg.distance && retLeg.duration) {
            totalMeters += retLeg.distance.value || 0;
            totalSeconds += retLeg.duration.value || 0;
            returnDistanceText = retLeg.distance.text;
            returnDurationText = retLeg.duration.text;
          }
          tripsInfo.push({
            trip: t + 1,
            color: colors[t % colors.length],
            items,
            totalMeters,
            totalSeconds,
            returnDistanceText,
            returnDurationText,
          });
        }
      } catch (_) {}
    } catch (e) {
      console.warn('Directions route failed for trip', t, e);
      const path = [new google.maps.LatLng(depotLL.lat, depotLL.lng), ...idxs.map(i => new google.maps.LatLng(pickups[i].lat, pickups[i].lng)), new google.maps.LatLng(depotLL.lat, depotLL.lng)];
      const pl = new google.maps.Polyline({ path, strokeColor: colors[t % colors.length], strokeOpacity: 1.0, strokeWeight: 5, map });
      vrpRenderers.push({ overlay: pl });

      try {
        let prev = depotLL;
        let totalMeters = 0, totalSeconds = 0;
        const items = [];
        for (let k = 0; k < idxs.length; k++) {
          const p = pickups[idxs[k]];
          const dM = dist(prev, {lat: p.lat, lng: p.lng});
          const durS = dM / 11.11; // ~40km/h
          items.push({ name: p.name || `Stop ${k+1}`, distanceText: `${(dM/1609.34).toFixed(1)} mi`, durationText: `${Math.round(durS/60)} min` });
          totalMeters += dM;
          totalSeconds += durS;
          prev = {lat: p.lat, lng: p.lng};
        }
        const backM = dist(prev, depotLL);
        const backS = backM / 11.11;
        totalMeters += backM;
        totalSeconds += backS;
        tripsInfo.push({
          trip: t + 1,
          color: colors[t % colors.length],
          items,
          totalMeters,
          totalSeconds,
          returnDistanceText: `${(backM/1609.34).toFixed(1)} mi`,
          returnDurationText: `${Math.round(backS/60)} min`,
        });
      } catch (_) {}
    }
  }

  setVRPInfo(tripsInfo);
}

window.init = init;

function isMiniViewport() {
  try {
    const el = document.getElementById('map');
    const w = el?.clientWidth || window.innerWidth;
    const h = el?.clientHeight || window.innerHeight;
    return w < 520 || h < 420; // heuristic for mini map
  } catch (_) {
    return false;
  }
}

function updatePlannerVisibility() {
  const mini = isMiniViewport();
  const panel = document.getElementById('vrpPanel');
  const openBtn = document.getElementById('vrpOpen');
  const info = document.getElementById('vrpInfoPanel');
  if (!panel || !openBtn || !info) return;
  if (mini) {
    panel.style.display = 'none';
    openBtn.style.display = 'none';
    info.style.display = 'none';
    clearVRPRoutes();
  } else {
    if (panel.style.display === 'none' || !panel.style.display) {
      openBtn.style.display = 'block';
    } else {
      openBtn.style.display = 'none';
    }
  }
}

function startGeoWatch() {
  if (!navigator.geolocation || !navigator.geolocation.watchPosition) return;
  navigator.geolocation.watchPosition((pos) => {
    const { latitude, longitude } = pos.coords;
    const hd = (pos.coords.heading != null && !isNaN(pos.coords.heading)) ? pos.coords.heading : 0;
    if (!origin) origin = { lat: latitude, lng: longitude };
    updateUser(latitude, longitude, hd, pos.coords.accuracy);
    if (!initialGeoCentered) {
      try { map.panTo({lat: latitude, lng: longitude}); map.setZoom(16); } catch(_){}
      initialGeoCentered = true;
    }
    try { document.getElementById('go').disabled = false; } catch (_) {}
  }, (err) => {
    console.warn('Geolocation watch failed', err);
    locateViaFallback();
  }, { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 });

  setTimeout(() => { if (!initialGeoCentered) locateViaFallback(); }, 7000);
}

async function locateViaFallback() {
  try {
    const res = await fetch('https://ipapi.co/json/');
    if (res && res.ok) {
      const j = await res.json();
      if (j && j.latitude && j.longitude) {
        const lat = +j.latitude, lng = +j.longitude;
        updateUser(lat, lng, 0, null);
        if (!initialGeoCentered) {
          try { map.panTo({lat, lng}); map.setZoom(14); } catch(_){}
          initialGeoCentered = true;
        }
        return;
      }
    }
  } catch (_) {}

  try {
    if (typeof GOOGLE_API_KEY !== 'undefined' && GOOGLE_API_KEY) {
      const res = await fetch(`https://www.googleapis.com/geolocation/v1/geolocate?key=${GOOGLE_API_KEY}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ considerIp: true })
      });
      if (res && res.ok) {
        const j = await res.json();
        const lat = j?.location?.lat, lng = j?.location?.lng, acc = j?.accuracy;
        if (isFinite(lat) && isFinite(lng)) {
          updateUser(lat, lng, 0, acc);
          if (!initialGeoCentered) {
            try { map.panTo({lat, lng}); map.setZoom(14); } catch(_){}
            initialGeoCentered = true;
          }
          return;
        }
      }
    }
  } catch (_) {}

  try {
    const c = map.getCenter();
    updateUser(c.lat(), c.lng(), 0, null);
    if (!initialGeoCentered) {
      map.setZoom(12);
      initialGeoCentered = true;
    }
  } catch(_) {}
}

function clearVRPRoutes() {
  try {
    vrpRenderers.forEach(obj => obj && obj.overlay && obj.overlay.setMap && obj.overlay.setMap(null));
  } catch (_) {}
  vrpRenderers = [];
}

function setVRPInfo(tripsInfo) {
  const panel = document.getElementById('vrpInfoPanel');
  if (!panel) return;
  if (!tripsInfo || !tripsInfo.length) {
    panel.style.display = 'none';
    panel.innerHTML = '';
    return;
  }
  const parts = [
    '<h4>Route Details</h4>',
    '<div class="trip"><a href="#" data-trip="all" style="color:#9cf;text-decoration:none;">Show all trips</a></div>'
  ];
  tripsInfo.sort((a,b)=>a.trip-b.trip).forEach(info => {
    const totalMi = (info.totalMeters/1609.34).toFixed(1);
    const totalMin = Math.round(info.totalSeconds/60);
    parts.push(`<div class="trip"><strong style="color:${info.color}">Trip ${info.trip}</strong> — ${totalMi} mi • ${totalMin} min</div>`);
    info.items.forEach(it => {
      parts.push(`<div class="item"><div class="name">${escapeHtml(it.name)}</div><div class="metrics">${it.distanceText} • ${it.durationText}</div></div>`);
    });
    if (info.returnDistanceText || info.returnDurationText) {
      parts.push(`<div class="item"><div class="name">Return to depot</div><div class="metrics">${info.returnDistanceText} • ${info.returnDurationText}</div></div>`);
    }
    parts.push(`<div class="item" style="border:0;padding-top:6px;"><a href="#" data-trip="${info.trip}" style="color:#9cf;text-decoration:none;">Show only Trip ${info.trip}</a></div>`);
  });
  panel.innerHTML = parts.join('');
  panel.style.display = 'block';
  panel.querySelectorAll('a[data-trip]').forEach(a => {
    a.onclick = (e) => {
      e.preventDefault();
      const v = a.getAttribute('data-trip');
      if (v === 'all') showAllVRPTrips(); else showOnlyVRPTrip(parseInt(v,10));
    };
  });
}

function showOnlyVRPTrip(tripNum) {
  vrpRenderers.forEach((obj, idx) => {
    if (!obj || !obj.overlay || !obj.overlay.setMap) return;
    obj.overlay.setMap(idx === (tripNum-1) ? map : null);
  });
}

function showAllVRPTrips() {
  vrpRenderers.forEach((obj) => {
    if (!obj || !obj.overlay || !obj.overlay.setMap) return;
    obj.overlay.setMap(map);
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
}
