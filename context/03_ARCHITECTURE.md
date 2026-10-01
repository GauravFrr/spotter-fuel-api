# 03 — Architecture and decisions

## Request flow
```
GET/POST /api/route/  { start, finish }
  1. geo.resolve_location(start/finish)      offline, microseconds
  2. cache lookup on rounded (start, finish)  hit -> return
  3. planner.fetch_route()                    ONE OSRM call, geojson, overview=full
  4. planner.stations_on_route()              numpy: snap stations to route, get mile markers
  5. planner.plan_fuel()                      greedy min-cost refuel
  6. build response, cache it, return JSON
```

## Routing provider
OSRM public demo: `GET {OSRM_URL}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson`
- No API key. Returns `distance` (meters), `duration` (seconds), `geometry.coordinates` as `[lon, lat]`.
- Convert meters → miles (÷ 1609.344). Note GeoJSON is lon,lat; internal code uses lat,lon — convert once, at the boundary.
- `OSRM_URL` configurable via env. If the demo server is down or throttled, fail with a clear 422/503 error. The planning environment could not reach OSRM, so **the agent must verify it live**.

## Station snapping (performance-critical)
- Load all stations into memory once as a numpy array `[id, lat, lon, price]`.
- Pre-filter by the route's bounding box (+ offset padding).
- Downsample route vertices to ≤ ~2,000 points; compute cumulative distance per vertex (equirectangular approximation, 69 mi/deg lat, × cos(lat) for lon), scaled so the total equals OSRM's distance.
- For candidates (in chunks of ~400 to bound memory), find the nearest route vertex; keep if distance ≤ `MAX_STATION_OFFSET_MI` (10). The vertex's cumulative distance is the station's **mile marker**.

## Optimizer (greedy, provably optimal for this problem)
Classic "gas station" min-cost problem with tank capacity = 500 miles of range.
- Nodes: virtual start (mile 0, priced at the first station on route) + stations sorted by mile + destination (mile = total, **price 0**).
- At node `i` with remaining range `fuel`:
  - Look at nodes reachable within 500 mi. If one is **strictly cheaper**, buy just enough to reach the nearest such node (`max(0, distance − fuel)`), go there.
  - Otherwise **fill the tank** and move to the next station.
  - If nothing is reachable within 500 mi → error 422 (`no fuel station within 500 miles after mile X`).
- Destination price 0 guarantees no wasted fuel at the end.
- Gallons = miles / 10. Cost = gallons × price. Total cost = sum of purchases.
- Assumption (state in README): tank is empty at departure and the first fill is priced at the first station along the route (shown as `initial_fill`, not as a stop). Alternative start-full models are a one-line change in the planner, but pick one and document it.

## API contract

### `GET /api/route/?start=Chicago, IL&finish=Los Angeles, CA` (also `POST` JSON `{"start": "...", "finish": "..."}`)
Success 200:
```json
{
  "start": "Chicago, IL",
  "finish": "Los Angeles, CA",
  "distance_miles": 2015.3,
  "duration_hours": 29.4,
  "vehicle": {"range_miles": 500, "mpg": 10},
  "initial_fill": {"gallons": 20.1, "price_per_gallon": 3.12, "cost": 62.71, "note": "..."},
  "fuel_stops": [
    {"name": "...", "address": "...", "city": "...", "state": "..", "lat": 0, "lon": 0,
     "mile_marker": 412.0, "miles_off_route": 3.2,
     "price_per_gallon": 3.05, "gallons": 38.7, "cost": 118.04}
  ],
  "total_gallons": 201.5,
  "total_fuel_cost": 640.12,
  "route": {"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": [[lon, lat], "..."]}},
  "map_url": "http://host/api/route/map/?start=...&finish=..."
}
```
(Numbers are illustrative.)

Errors: `400 {"error": "..."}` for bad/unknown locations or invalid JSON; `422 {"error": "..."}` when no route/stations/routing service failure.

### `GET /api/route/map/?start=...&finish=...`
HTML page: Leaflet map (route polyline + stop markers with popups) and a stops table. Leaflet/tiles load from public CDNs in the browser; the server makes no extra calls.

## Performance targets
- Cache miss (excluding OSRM latency): < 300 ms.
- Cache hit: < 50 ms. Cache key = rounded coordinates (3 decimals). Local-memory cache, TTL 1 h.
- Response size: route geometry downsampled to ≤ ~1,500 points.

## Config (settings.py, env-overridable)
`OSRM_URL`, `VEHICLE_RANGE_MI=500`, `VEHICLE_MPG=10`, `MAX_STATION_OFFSET_MI=10`, `ROUTING_TIMEOUT_S=15`, `RESULT_CACHE_TTL_S=3600`.

## Out of scope (do not build)
Auth, DRF, DB-heavy ORM queries at request time, Docker, async, front-end app, truck-specific routing, live price updates, multi-vehicle support.
