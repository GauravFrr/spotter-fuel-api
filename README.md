# Spotter Fuel Routing API

A fast, lightweight Django REST API that computes driving routes across the USA and determines cost-optimal fuel stops for vehicles with a **500-mile range** and **10 MPG** fuel efficiency.

---

## Example Request & Response

### Request
```bash
curl -X GET "http://127.0.0.1:8000/api/route/?start=Chicago,%20IL&finish=Los%20Angeles,%20CA"
```

### Response (`200 OK`)
```json
{
  "start": "Chicago, IL",
  "finish": "Los Angeles, CA",
  "distance_miles": 2024.4,
  "duration_hours": 35.6,
  "vehicle": {
    "range_miles": 500,
    "mpg": 10
  },
  "initial_fill": {
    "gallons": 0.79,
    "price_per_gallon": 3.569,
    "cost": 2.83,
    "note": "Initial fill at departure point (priced at first available station on route)"
  },
  "fuel_stops": [
    {
      "name": "Gulf",
      "address": "I-290 & SR-83",
      "city": "Bensenville",
      "state": "IL",
      "lat": 41.9572,
      "lon": -87.9403,
      "mile_marker": 16.4,
      "miles_off_route": 1.7,
      "price_per_gallon": 3.39,
      "gallons": 18.92,
      "cost": 64.14
    }
  ],
  "total_gallons": 202.44,
  "total_fuel_cost": 613.88,
  "route": {
    "type": "Feature",
    "properties": {},
    "geometry": {
      "type": "LineString",
      "coordinates": [[-87.6298, 41.8781], ...]
    }
  },
  "map_url": "http://127.0.0.1:8000/api/route/map/?start=Chicago%2C+IL&finish=Los+Angeles%2C+CA"
}
```

---

## Setup & Running Locally

### Prerequisites
- Python 3.12+ installed

### Quickstart (5 Commands)
```bash
# 1. Clone repository & enter directory
git clone https://github.com/user/spotter-fuel-api.git
cd spotter-fuel-api

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run database migrations
python manage.py migrate

# 4. Clean, geocode, and load fuel stations into SQLite database
python manage.py load_stations

# 5. Start the Django server
python manage.py runserver
```

Open `http://127.0.0.1:8000/api/route/?start=Chicago, IL&finish=Los Angeles, CA` in your browser or Postman.

---

## Environment Variables (`.env`)

Default configuration is automatically loaded from `.env` or settings defaults:

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | `django-insecure-...` | Secret key for Django |
| `DJANGO_DEBUG` | `True` | Debug flag |
| `OSRM_URL` | `https://router.project-osrm.org` | Public OSRM routing base URL |
| `VEHICLE_RANGE_MI` | `500.0` | Maximum vehicle tank range (miles) |
| `VEHICLE_MPG` | `10.0` | Fuel consumption rate (miles per gallon) |
| `MAX_STATION_OFFSET_MI` | `10.0` | Maximum allowed distance off route for stations (miles) |
| `ROUTING_TIMEOUT_S` | `15.0` | OSRM HTTP request timeout (seconds) |
| `RESULT_CACHE_TTL_S` | `3600` | Local memory cache TTL for route responses (seconds) |

### Input Formats (`start` & `finish`)
The API resolves locations flexibly across 4 supported formats:
1. **City, Postal Code:** e.g., `"Chicago, IL"` (Offline, ~0 ms)
2. **City, Full State Name:** e.g., `"Chicago, Illinois"` or `"Denver, Colorado"` (Offline, ~0 ms)
3. **Coordinates:** e.g., `"39.7392, -104.9903"` (Offline, ~0 ms)
4. **Free-text Address:** e.g., `"1600 Pennsylvania Ave, Washington DC"` (Online Nominatim Fallback, 1 call)

> **Note on Routing Service:** The default routing endpoint uses the public OSRM demo server (`https://router.project-osrm.org`). If the public server is throttled or down, `OSRM_URL` can be overridden in `.env` (e.g. `OSRM_URL=http://localhost:5000` or an alternative hosted OSRM instance).

---

## API Reference

### 1. Route JSON Endpoint: `GET /api/route/` or `POST /api/route/`
Computes optimal route geometry, fuel stops, and total cost.

- **Query Parameters (GET):**
  - `start` (string, required): e.g. `"Chicago, IL"` or `"39.7392,-104.9903"`
  - `finish` (string, required): e.g. `"Los Angeles, CA"` or `"34.0522,-118.2437"`

- **JSON Body (POST):**
  - `{"start": "Chicago, IL", "finish": "Los Angeles, CA"}`

- **Status Codes:**
  - `200 OK`: Success.
  - `400 Bad Request`: Missing parameters, invalid JSON, or unresolvable location string.
  - `422 Unprocessable Entity`: No reachable fuel station within 500 miles, or OSRM routing service error.

### 2. Leaflet Map Page: `GET /api/route/map/`
Renders an interactive dark-themed Leaflet HTML map displaying:
- Start and Finish location markers
- High-resolution blue route polyline
- Clickable fuel stop markers showing station popups (Price, Gallons bought, Cost, Mile marker)
- Summary card and interactive fuel stop table

---

## How It Works

### Flow
```
User Request (start, finish)
  │
  ├── 1. geo.resolve_location(start/finish) ──── [1st: Offline US Cities Table lookup]
  │                                               [2nd: Nominatim API fallback if unrecognized]
  ├── 2. cache lookup on (start, finish) ─────── [Return warm cached JSON if hit]
  ├── 3. planner.fetch_route() ───────────────── [Single HTTP GET to OSRM API]
  ├── 4. planner.stations_on_route() ─────────── [Numpy vectorised station snapping]
  ├── 5. planner.plan_fuel() ─────────────────── [Greedy min-cost refuel optimizer]
  └── 6. Cache response & return JSON
```

### Architectural Highlights
- **Strictly Bounded External Calls ($\le 3$ calls total):** Start and finish locations are geocoded offline against `data/us_cities.csv` (29,880 US city centroids). If an unrecognized location string is provided, a single OpenStreetMap Nominatim search request (`countrycodes=us`, User-Agent header, 5s timeout) is made only as a fallback. The driving route polyline is fetched via 1 single call to OSRM. Total external API calls per request are guaranteed to be $\le 3$ (and exactly 1 for standard cities).
- **Numpy Station Snapping:** All 6,614 stations are indexed in memory. Stations are pre-filtered by bounding box and snapped to route line vertices using vectorized Euclidean distance in **~80 ms**.
- **Greedy Min-Cost Optimizer:**
  1. At current node $i$, look ahead up to 500 miles.
  2. If a strictly cheaper station $j$ is reachable, purchase just enough fuel to reach station $j$.
  3. Otherwise, fill the tank to capacity (500 mi range) and advance to the next station.
  4. Destination is priced at $0.00 to guarantee no unused fuel is bought.

---

## Key Assumptions

1. **Departure Fill:** Tank starts empty at departure; the initial fill is priced at the first available station along the route.
2. **Station Deduplication:** Duplicate `OPIS Truckstop ID` entries in `fuel_prices.csv` are cleaned by retaining the lowest retail fuel price.
3. **On-Route Tolerance:** A station is considered "on route" if its city centroid is within **10 miles** of the driving route polyline.
4. **Geography:** Canadian records in the CSV are filtered out (US-only scope).

---

## Limitations

1. **City Centroid Coordinates:** Station locations in `fuel_prices.csv` lack exact street coordinates and use city centroids (`us_cities.csv`), introducing up to a few miles of offset.
2. **OSRM Public Server:** The public demo server `router.project-osrm.org` has no SLA guarantees.
3. **Geocoding Matching:** ~12 stations (0.18%) in unincorporated areas (e.g., Port Wentworth GA, Elizabethport NJ) fail offline geocoding and are safely skipped.

---

## Performance Benchmark

Measured on development system (Intel / Windows):

| Request Type | Latency |
|---|---|
| **Cold Request** (OSRM call + station snapping + optimizer) | **~1.6 s - 2.4 s** (dominated by OSRM network round-trip) |
| **Numpy Station Snapping** (6,614 stations) | **83 ms** |
| **Warm Request** (In-memory cache hit) | **< 5 ms** |

---

## Running Unit & Integration Tests

```bash
python manage.py test
```

Includes 20 unit tests covering offline geocoding, station cleaning, greedy planner edge cases, DP cross-validation, OSRM mocking, and API cache responses.
