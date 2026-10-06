# Loom Video Recording Script (Short & Bulleted)

**Project:** Spotter Fuel Routing API  
**Target Duration:** ~3 to 4 Minutes  
**Speaker:** Backend Django Engineer  

---

## Quick Setup Before Recording
1. **Terminal:** Server running (`python manage.py runserver 8000`).
2. **Browser:** Tab open to `http://127.0.0.1:8000/api/route/map/?start=Chicago,%20IL&finish=Los%20Angeles,%20CA`.
3. **Postman:** 6 requests ready in left panel.
4. **IDE:** VS Code open to `geo.py`, `planner.py`, `views.py`.

---

## Section 1: Intro & Architecture (0:00 – 0:30)
**Screen:** Show `README.md` or GitHub Repository.

> **Say this:**
> - *"Hi Ena and the Spotter team! This is the Spotter Fuel Routing API."*
> - *"It computes cost-optimal fuel stops for vehicles with a 500-mile tank range and 10 MPG."*
> - *"Key architecture: 29,880 offline US city centroids for instant geocoding, exactly 1 OSRM routing call per request, and an in-memory NumPy station snapping engine."*

---

## Section 2: Postman Demo (0:30 – 2:00)
**Screen:** Switch to **Postman**.

### 1. Short Route — Dallas to Houston
- **Action:** Click Request 1 $\rightarrow$ **Send**
> **Say this:**
> - *"First, a short route under 500 miles: Dallas to Houston (239 miles)."*
> - *"Because it's under 500 miles, it fills up once at departure ($77.65) with zero intermediate fuel stops."*

### 2. Cross-Country Route — Chicago to LA
- **Action:** Click Request 3 $\rightarrow$ **Send**
> **Say this:**
> - *"Next, a 2,024-mile cross-country trip: Chicago to LA."*
> - *"The NumPy engine snaps 6,614 stations in 83ms and selects 20 optimal fuel stops for $613.88."*

### 3. POST JSON & Error Handling
- **Action:** Click Request 4 (POST JSON) $\rightarrow$ **Send**, then Request 5 (Bad Location) $\rightarrow$ **Send**
> **Say this:**
> - *"The API also accepts POST JSON requests."*
> - *"For unresolvable locations, it returns a clean 400 Bad Request error instead of crashing."*

---

## Section 3: Interactive Leaflet Map (2:00 – 2:30)
**Screen:** Switch to **Browser** (`/api/route/map/`).

> **Say this:**
> - *"Opening `/api/route/map/` renders an interactive Leaflet map."*
> - *"It shows the blue polyline, start/finish pins, and clickable fuel stop popups with prices, gallons bought, and costs."*

---

## Section 4: Code Walkthrough (2:30 – 3:30)
**Screen:** Switch to **IDE** (VS Code).

### `geo.py` & `load_stations.py`
- **Action:** Show `load_stations.py` and `geo.py`
> **Say this:**
> - *"`load_stations.py` cleans the CSV, filters Canadian rows, dedupes prices, and loads 6,614 stations."*
> - *"`geo.py` resolves locations offline using `us_cities.csv`, keeping external calls $\le 3$."*

### `planner.py` & `views.py`
- **Action:** Show `planner.py` and `views.py`
> **Say this:**
> - *"`planner.py` runs a greedy min-cost refuel algorithm."*
> - *"`views.py` stays thin under 60 lines with in-memory caching."*
> - *"All 23 unit tests pass in under 2 seconds."*

---

## Section 5: Performance & Wrap-Up (3:30 – 4:00)
**Screen:** Switch back to Browser or Terminal.

> **Say this:**
> - *"Performance: Cold requests take ~1.8s (OSRM transit), NumPy snapping takes 83ms, and cached requests return under 5ms."*
> - *"Trade-off note: Station coordinates use city centroids since the raw CSV lacked lat/lon."*
> - *"Code and Postman collection are live on GitHub. Thank you!"*
