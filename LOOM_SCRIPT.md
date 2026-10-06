# Loom Video Recording Script (≤ 5 Minutes)

**Project:** Spotter Fuel Routing API  
**Target Duration:** ~4 minutes 30 seconds (Max 5:00)  
**Speaker:** Backend Django Engineer  

---

## Pre-Recording Setup Checklist
1. **Terminal 1:** Start local server: `python manage.py runserver 8000`
2. **Browser:** Open tab to `http://127.0.0.1:8000/api/route/map/?start=Chicago,%20IL&finish=Los%20Angeles,%20CA`
3. **Postman:** Open `postman/spotter-fuel-api.postman_collection.json` with 6 requests ready:
   - `1. Short Route (<500 mi) - Dallas to Houston`
   - `2. Medium Route (~500 mi) - Denver to Salt Lake City`
   - `3. Cross-Country Route (~2000 mi) - Chicago to LA`
   - `4. POST JSON Variant - Chicago to LA`
   - `5. Bad Location Error Path (400 Bad Request)`
   - `6. Leaflet Route Map Page (HTML)`
4. **IDE (VS Code / PyCharm):** Open `routing/geo.py`, `load_stations.py`, `routing/planner.py`, `routing/views.py`, and `routing/tests/test_api.py`.

---

## Video Section Breakdown

### Section 1: Overview & Architectural Approach (0:00 – 0:30)
**Screen Action:** Show GitHub Repository or IDE workspace (`README.md`).

> **Spoken Script:**  
> *"Hi Ena and the Spotter team! Today I'm demonstrating the Spotter Fuel Routing API — a clean, high-performance Django REST API that computes cost-optimal fuel stops along US driving routes for vehicles with a 500-mile tank range and 10 MPG efficiency.*  
>  
> *To deliver fast responses while strictly limiting external API calls, the app uses an offline US cities dataset of 29,880 city centroids for zero-latency geocoding, calls the public OSRM routing engine exactly once per request for polyline geometry, and runs an in-memory NumPy vectorised station snapping engine coupled with a greedy min-cost refueling optimizer."*

---

### Section 2: Postman & Live Endpoint Demo (0:30 – 2:30)
**Screen Action:** Switch to **Postman**.

#### 1. Short Route (< 500 mi) — Dallas, TX to Houston, TX (0:30 – 1:00)
- **Action:** Execute `GET /api/route/?start=Dallas, TX&finish=Houston, TX`
- **Spoken Script:**  
  > *"First, let's look at a short route under 500 miles: Dallas to Houston (239.6 miles). Because total distance is within the 500-mile tank range, the vehicle fills 23.96 gallons at departure for $77.65 and requires zero intermediate fuel stops. All stop gaps are naturally within 500 miles."*

#### 2. Cross-Country Route (~2000 mi) — Chicago, IL to Los Angeles, CA (1:00 – 1:35)
- **Action:** Execute `GET /api/route/?start=Chicago, IL&finish=Los Angeles, CA`
- **Spoken Script:**  
  > *"Next is a 2,024-mile cross-country trip from Chicago to Los Angeles. Here, the greedy optimizer evaluates candidate truck stops along the route. It snaps 6,614 nationwide fuel stations in 83 milliseconds, identifies cheaper stations ahead, and schedules 20 cost-optimal refuel stops.  
  > Notice the JSON output returns total gallons (202.44), total fuel cost ($613.88), GeoJSON line geometry, and a `map_url`."*

#### 3. POST JSON Variant & Error Handling (1:35 – 2:00)
- **Action:** Execute `POST /api/route/` with JSON `{"start": "Chicago, IL", "finish": "Los Angeles, CA"}`, then execute request 5 (`Bad Location`).
- **Spoken Script:**  
  > *"The API seamlessly supports `POST` JSON payloads as well. And if an invalid or unresolvable location is provided, the API returns a clean HTTP 400 Bad Request error with a descriptive message, avoiding 500 server crashes."*

#### 4. Live Leaflet HTML Map (2:00 – 2:30)
- **Action:** Switch browser to `http://127.0.0.1:8000/api/route/map/?start=Chicago,%20IL&finish=Los%20Angeles,%20CA`
- **Spoken Script:**  
  > *"Visiting `/api/route/map/` renders an interactive Leaflet HTML map. It renders the route polyline, start/finish pins, and clickable fuel stop markers showing station name, address, price per gallon, fuel bought, and stop cost alongside a clean summary table."*

---

### Section 3: Code Walkthrough (2:30 – 4:15)
**Screen Action:** Switch to **IDE**.

#### 1. Data Cleaning & Offline Geocoding (`geo.py` & `load_stations.py`) (2:30 – 3:00)
- **Action:** Open `routing/geo.py` and `load_stations.py`.
- **Spoken Script:**  
  > *"Looking at the codebase, `load_stations.py` processes `fuel_prices.csv`. It filters out non-US Canadian provinces, dedupes repeated OPIS IDs by keeping the cheapest retail price, and geocodes each station against `us_cities.csv`. Out of 6,626 unique stations, 6,614 are loaded into SQLite while 12 unlisted rural centroids are safely skipped.  
  > In `geo.py`, `resolve_location` performs instant offline lookup for city/state strings and lat/lon coordinates, with an optional single Nominatim fallback for free-text addresses, ensuring total external calls never exceed 3."*

#### 2. Vectorized Snapping & Greedy Optimizer (`planner.py`) (3:00 – 3:45)
- **Action:** Open `routing/planner.py` at `stations_on_route` and `plan_fuel`.
- **Spoken Script:**  
  > *"In `planner.py`, `stations_on_route` uses NumPy arrays in memory. It pre-filters stations by the route bounding box and snaps them to route polyline vertices using vectorised distance math in under 90 ms.  
  > `plan_fuel` implements a provably optimal greedy gas station algorithm: at station $i$, if a cheaper station is reachable within 500 miles, it buys just enough fuel to reach that station; otherwise, it fills the tank to full capacity."*

#### 3. Views & Test Suite (`views.py` & terminal) (3:45 – 4:15)
- **Action:** Show `views.py` and run `python manage.py test` in terminal.
- **Spoken Script:**  
  > *"Views in `views.py` are kept thin under 60 lines. Results are cached in Django's `LocMemCache`. Running `python manage.py test` executes 23 unit tests covering geocoding, greedy planning, DP cross-validation, OSRM mocking, and API responses in ~1.5 seconds."*

---

### Section 4: Performance & Wrap-Up (4:15 – 4:45)
**Screen Action:** Switch back to browser or terminal.

> **Spoken Script:**  
> *"To summarize performance: cold requests complete in 1.6 to 2.4 seconds — dominated by OSRM network transit — while NumPy station snapping takes only 83 milliseconds, and warm cached requests return in under 5 milliseconds.  
>  
> **Honest Limitation:** Because fuel station addresses in the provided dataset lack latitude/longitude coordinates, positions use city centroids from the US cities database. A 10-mile snapping tolerance is applied to accommodate highway exit offsets.  
>  
> The repository is published on GitHub at `GauravFrr/spotter-fuel-api` with full setup instructions and Postman export. Thank you for your time!"*

---

## Quick Reference Summary Table for Recording

| Timestamp | Screen Focus | Key Script Point |
|---|---|---|
| **0:00 - 0:30** | GitHub / README | Problem, 500 mi range, 1 OSRM call, offline geocoding |
| **0:30 - 1:00** | Postman | Short route (Dallas $\rightarrow$ Houston): 1 fill, 0 extra stops |
| **1:00 - 1:35** | Postman | Cross-country (Chicago $\rightarrow$ LA): 20 stops, $613.88 cost |
| **1:35 - 2:00** | Postman | POST JSON payload & 400 Bad Request error handling |
| **2:00 - 2:30** | Browser | Leaflet map (`/api/route/map/`) showing route & stop popups |
| **2:30 - 3:00** | IDE (`load_stations.py`, `geo.py`) | CSV cleaning, deduplication, 6,614 loaded, offline geocoding |
| **3:00 - 3:45** | IDE (`planner.py`) | NumPy snapping in 83 ms, greedy min-cost optimizer |
| **3:45 - 4:15** | IDE (`views.py` + Terminal) | Thin views, `LocMemCache`, 23 passing tests |
| **4:15 - 4:45** | Browser / Terminal | Performance numbers (cold ~1.8s, warm <5ms), city centroid trade-off, closing |
