# AGENT.md — Spotter Backend Django Assessment

You are building a small, fast, clean Django API for a hiring assessment. Read this file first, then everything in `docs/` in numeric order before writing any code.

## Mission
Build an API that takes a start and finish location in the USA and returns:
1. the driving route (as a map-ready geometry + a simple map page),
2. the cost-optimal fuel stops along it (vehicle range 500 mi, 10 mpg),
3. the total money spent on fuel.

Fuel prices come from `data/fuel_prices.csv`. Routing uses a free API. Deadline is short: **ship a small, correct, well-explained project, not a big one.**

## Hard requirements (from the assignment — never violate)
- Latest stable Django (check PyPI, pin it in `requirements.txt`).
- Fast responses. The faster the better.
- **Routing API called once per request** (twice or three times is the absolute max). Never geocode start/finish with an external API.
- Range 500 miles → multiple fuel stops possible. 10 mpg.
- Fuel stops chosen mainly by cost, from the supplied CSV.
- Must be demoable in Postman in a 5-minute Loom.

## Stack and decisions already made (do not re-debate)
- Python 3.12+, Django (latest stable), SQLite, numpy, requests. **No DRF, no Celery, no Redis, no Docker needed.** Plain Django views returning `JsonResponse`.
- Routing: public OSRM demo server (`https://router.project-osrm.org`), no API key, GeoJSON geometry.
- Geocoding: **offline**, from a bundled US cities CSV (see `docs/02_DATA_NOTES.md`). The fuel CSV has no coordinates.
- Optimizer: greedy "cheaper station ahead" algorithm (see `docs/03_ARCHITECTURE.md`). Do not use an LLM, ML, or a heavy solver.
- Full reasoning for all of this is in `docs/`. If you disagree with a decision, write the concern in `NOTES.md` and keep going with the documented choice.

## Working rules
- Work in the phases of `docs/04_BUILD_PLAN.md`. Finish and verify one phase before starting the next.
- After each phase: run the tests, run the server, hit the endpoint, and report the real output. Do not claim something works without running it.
- Keep it small: one Django app (`routing`), thin views, logic in `planner.py` and `geo.py`.
- Pure functions for the planner so they are unit-testable without network or DB.
- Never hardcode secrets. Config via `settings.py` with env overrides.
- No dead code, no speculative features, no extra endpoints beyond `docs/03_ARCHITECTURE.md`.
- Comments explain *why*, not *what*. Docstrings on public functions.
- Write the README honestly: state assumptions and limitations (city-centroid station coordinates, tank-start assumption).
- Commit in small, meaningful commits (`feat:`, `test:`, `docs:`).

## Commands (keep these working)
```
pip install -r requirements.txt
python manage.py migrate
python manage.py load_stations
python manage.py runserver
python manage.py test
```

## Definition of done
- [ ] `docs/04_BUILD_PLAN.md` all phases checked
- [ ] Tests pass; at least one live end-to-end call to OSRM verified (e.g. Chicago, IL → Los Angeles, CA)
- [ ] Warm response (cached route not required) under ~300 ms excluding the OSRM call; repeat request under ~50 ms
- [ ] README with setup, API examples, assumptions, limitations
- [ ] Postman collection exported to `postman/`
- [ ] `docs/05_DELIVERABLES.md` checklist complete

## Things to ask the human before doing
- Anything that changes the response shape in `docs/03_ARCHITECTURE.md`
- Adding any dependency not listed above
- Switching the routing provider

Otherwise: decide, build, verify, report.
