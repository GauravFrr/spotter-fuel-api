# 05 — Deliverables and submission

## README.md outline
1. What it does (3 lines) + example request/response (shortened)
2. Setup (5 commands), env vars
3. API reference (both endpoints, errors)
4. How it works: the flow diagram in words, why one routing call, why offline geocoding, the greedy algorithm in 5 lines
5. Assumptions: tank empty at start with first fill at the first station's price; cheapest price kept for duplicate station IDs; 10 mi on-route tolerance; Canadian rows dropped
6. Limitations: station positions are city centroids; OSRM public demo has no SLA; US cities table matches ~99.8% of stations
7. Performance numbers (cold vs cached) measured on the dev machine
8. Tests: how to run

## Postman collection (`postman/`)
Requests: (1) short route (2) medium route (3) cross-country (4) `POST` JSON variant (5) bad location → 400 (6) the map URL. Use a `{{base_url}}` variable. Add a simple test script per request checking status code and that `total_fuel_cost` exists.

## Loom script (≤ 5 min, aim for 4:30)
- 0:00–0:30 Problem + approach in one breath: one OSRM call, offline geocoding, greedy optimizer.
- 0:30–2:30 Postman: short route (one fill, no stops beyond initial), cross-country route (multiple stops, show gallons/prices/total), POST variant, error case. Open `map_url` in the browser and show the map.
- 2:30–4:15 Code tour: `geo.py` → `load_stations` (data cleaning) → `planner.py` (`stations_on_route`, `plan_fuel`) → `views.py` → tests.
- 4:15–4:45 Performance (cold vs cached) + honest limitations (city-centroid coordinates). Done.

## Submission checklist
- [ ] Public GitHub repo, README renders, no secrets, no `db.sqlite3` committed (data loads via command)
- [ ] Fresh-clone test: follow README only → API works
- [ ] Loom link works without login
- [ ] Reply in the original email thread / question box with: GitHub link + Loom link + 2-line summary of approach
- [ ] Sent **before 2 Oct 2026** (earlier submissions get review priority per Spotter's follow-up email)
