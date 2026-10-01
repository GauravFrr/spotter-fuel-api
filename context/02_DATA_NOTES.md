# 02 — Data notes (read before touching the CSV)

File: `data/fuel_prices.csv` (as supplied). Columns:
`OPIS Truckstop ID, Truckstop Name, Address, City, State, Rack ID, Retail Price`

## Findings (agent: verify these numbers first thing)
- 8,151 data rows, **no latitude/longitude anywhere**. Addresses look like `I-44, EXIT 283 & US-69`, which cannot be geocoded offline.
- **Duplicates:** only ~6,738 unique `OPIS Truckstop ID`s. Same ID appears multiple times, sometimes with different name spellings (`PILOT TRAVEL CENTER #1243` vs `PILOT #1243`) and ~597 IDs with different prices.
- **Not all US:** the `State` column has 57 values including Canadian provinces: `AB BC MB NB NS ON QC SK YT`. Drop them (US-only assignment).
- `Retail Price` is USD per gallon (range roughly 2.x–6.4). Some trailing whitespace in `City`.
- Rack ID is irrelevant to this task.

## Cleaning rules (decided)
1. Drop non-US states (list above, plus `NL PE NT NU` defensively).
2. Strip whitespace on all text fields.
3. Dedupe by `OPIS Truckstop ID`; for repeated IDs **keep the cheapest price** (document this in README).
4. Geocode each remaining station by `(city, state)` against the bundled cities table.
5. Skip stations that fail to geocode and report the count. Expected: ~6,600 loaded, ~12 skipped (e.g. Elizabethport NJ, Brookpark OH, Evergreen AL, Henrico VA, University Park IL).

## Geocoding table
- Source: `https://raw.githubusercontent.com/kelvins/US-Cities-Database/main/csv/us_cities.csv` → save as `data/us_cities.csv`.
- Columns: `ID, STATE_CODE, STATE_NAME, CITY, COUNTY, LATITUDE, LONGITUDE` (~29,880 rows).
- Normalise names before matching: lowercase, strip punctuation, `saint→st`, `mount→mt`, `fort→ft`. Expected match rate ≈ 99.8%.
- The same table resolves the API's `start`/`finish` text (`"Denver, CO"` or `"Denver, Colorado"`) so no external geocoder is needed.

## Known limitation (state it in the README, don't hide it)
Station coordinates are **city centroids**, not exact truck-stop positions, so a station can be a few miles from where it truly is. That is why a station counts as "on the route" if it is within **10 miles** of the route line. This is a deliberate trade-off to keep routing calls at one per request.
