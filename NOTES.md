# Architectural Notes & Decisions

## 1. Tank Model & Departure Fueling
- **Decision:** The vehicle tank is assumed empty at departure, and the initial fill is priced at the first available fuel station along the route.
- **Rationale:** Aligns with standard route cost optimization when starting a commercial trip without assuming pre-existing fuel.

## 2. Station Coordinate Resolution (City Centroids)
- **Decision:** Fuel stations in `data/fuel_prices.csv` are geocoded using `(city, state)` against `data/us_cities.csv`.
- **Rationale:** The raw CSV contains street addresses without latitude/longitude (e.g., `I-44, EXIT 283 & US-69`). Offline geocoding with city centroids avoids external API dependency, keeping routing fast and avoiding API rate limits.
- **Tolerance:** A 10-mile perpendicular snapping distance (`MAX_STATION_OFFSET_MI=10.0`) accounts for city centroid displacement from highway exit locations.

## 3. Station Deduplication Strategy
- **Decision:** When duplicate `OPIS Truckstop ID` entries occur in `fuel_prices.csv`, the entry with the **cheapest price per gallon** is retained.
- **Rationale:** Ensures cost minimisation for the user while cleaning duplicate reporting artifacts.

## 4. OSRM Integration & Performance
- **Decision:** OSRM public API (`https://router.project-osrm.org`) is queried exactly once per request.
- **Performance:** In-memory numpy station snapping executes in ~80 ms. Cold API responses return in ~1.6–2.4 s (dominated by network latency to OSRM). Warm responses from `LocMemCache` return in < 5 ms.
