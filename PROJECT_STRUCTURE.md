# Project structure (target)

```
spotter-fuel-api/
├── AGENT.md                      # agent rules + decisions (read first)
├── NOTES.md                      # agent: disagreements, open questions, learnings
├── README.md                     # human-facing: setup, API, assumptions, limits
├── requirements.txt              # pinned: django, numpy, requests
├── manage.py
├── .gitignore                    # db.sqlite3, __pycache__, .env, venv
├── .env.example                  # DJANGO_SECRET_KEY, DJANGO_DEBUG, OSRM_URL
│
├── config/                       # Django project package
│   ├── __init__.py
│   ├── settings.py               # env-driven; fuel/routing constants live here
│   ├── urls.py                   # mounts routing.urls under /api/
│   └── wsgi.py
│
├── routing/                      # the single Django app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                 # Station
│   ├── geo.py                    # offline geocoding: "City, ST" | "lat,lon" -> (lat, lon)
│   ├── planner.py                # OSRM fetch, station snapping, greedy optimizer, orchestration
│   ├── views.py                  # thin: parse -> resolve -> plan -> JSON
│   ├── urls.py                   # /route/ and /route/map/
│   ├── templates/routing/map.html# Leaflet map + stops table
│   ├── migrations/
│   ├── management/commands/load_stations.py   # CSV -> clean -> geocode -> DB
│   └── tests/
│       ├── test_geo.py
│       ├── test_planner.py       # pure-function tests, no network/DB
│       ├── test_load_stations.py
│       └── test_api.py           # OSRM mocked; 1 optional live test
│
├── data/
│   ├── fuel_prices.csv           # supplied by Spotter (do not edit)
│   └── us_cities.csv             # bundled geocoding table (see docs/02)
│
├── docs/
│   ├── 01_ASSIGNMENT.md
│   ├── 02_DATA_NOTES.md
│   ├── 03_ARCHITECTURE.md
│   ├── 04_BUILD_PLAN.md
│   └── 05_DELIVERABLES.md
│
└── postman/
    └── spotter-fuel-api.postman_collection.json
```

Rules: one app only; no `utils.py` dumping ground; logic in `geo.py` and `planner.py`; views stay under ~60 lines.
