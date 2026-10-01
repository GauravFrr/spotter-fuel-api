# 04 — Build plan (do in order; verify each phase with real output)

## Phase 0 — Scaffold (15 min)
- [ ] Django project `config` + app `routing`; `requirements.txt` (django latest stable, numpy, requests); `.gitignore`; `.env.example`
- [ ] Copy `fuel_prices.csv` to `data/`; download `us_cities.csv` to `data/`
- [ ] **Accept:** `python manage.py check` passes; confirm the data facts in `02_DATA_NOTES.md`

## Phase 1 — Data layer
- [ ] `Station` model + migration
- [ ] `geo.py`: `norm_city`, city table (lazy, cached), `resolve_location`
- [ ] `load_stations` command per cleaning rules
- [ ] Tests: normalisation, `"Denver, CO"` / `"Denver, Colorado"` / `"39.74,-104.99"`, bad input, outside-US coords
- [ ] **Accept:** command prints ~6,600 loaded, ~12 skipped; tests green

## Phase 2 — Optimizer (pure functions)
- [ ] `plan_fuel(nodes, total_mi, range_mi, mpg)` exactly as in `03_ARCHITECTURE.md`
- [ ] Tests (no network/DB): trip shorter than range = one fill; cheaper station ahead → buy minimum; expensive-then-cheap; gap > 500 mi raises error; total cost equals gallons × prices; no fuel left over at destination
- [ ] **Accept:** all planner tests green; cross-check one case against a brute-force/DP solution in the test file

## Phase 3 — Routing + snapping
- [ ] `fetch_route` (single OSRM call, timeout, clean errors)
- [ ] `stations_on_route` (numpy, chunked)
- [ ] **Live test** Chicago, IL → Los Angeles, CA; print distance, number of candidate stations, timings
- [ ] **Accept:** distance within a few % of known (~2,000 mi); snapping < 300 ms; OSRM called exactly once (assert in a test with a mock)

## Phase 4 — API
- [ ] `build_plan` orchestration + cache
- [ ] `/api/route/` GET+POST, error handling (400/422), `/api/route/map/`
- [ ] Tests with mocked OSRM for success and each error path; one `@skipUnless(LIVE)` live test
- [ ] **Accept:** real `curl` output for 3 routes: short (<500 mi, e.g. Dallas, TX → Houston, TX), medium, cross-country; verify stops are ≤ 500 mi apart and total cost is consistent

## Phase 5 — Polish and deliverables
- [ ] README per `05_DELIVERABLES.md`
- [ ] Postman collection with the 3 demo routes + 2 error cases, exported to `postman/`
- [ ] Timing check (cold vs cached) recorded in README
- [ ] `git log` clean; push; confirm the repo opens on a fresh clone with the README steps only
- [ ] **Accept:** `05_DELIVERABLES.md` checklist complete
