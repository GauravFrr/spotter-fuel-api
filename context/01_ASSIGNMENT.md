# 01 — The assignment (source of truth)

From Ena at Spotter, role **Backend Django Engineer**, received **29 Sept 2026**. Due **within 3 days → submit by 2 Oct 2026**.

## Task
Build an API that takes inputs of start and finish location both within the USA.
- Return a map of the route along with optimal location(s) to fuel up along the route. "Optimal" mostly means cost effective based on fuel prices.
- Assume the vehicle has a maximum range of **500 miles**, so multiple fuel ups might need to be displayed on the route.
- Also return the **total money spent on fuel**, assuming the vehicle achieves **10 miles per gallon**.
- Use the attached CSV for fuel prices (`data/fuel_prices.csv`).
- Find a free API yourself for the map and routing.

## Requirements
- Build the app in the latest stable Django.
- The API should return results quickly — the quicker the better.
- The API shouldn't call the free map/routing API too much: **one call is ideal, two or three acceptable.**
- Make a Loom (max 5 minutes) using Postman (or similar) to demonstrate the API working, while giving a quick overview of the code.
- Share the GitHub code.
- Attach the GitHub link and Loom link in the reply to the email.
- $100 bonus only upon successful completion.

## Requirement checklist (map to tests/README)
| # | Requirement | How we satisfy it |
|---|---|---|
| R1 | Input: start + finish, USA | `start`/`finish` as `"City, ST"` or `"lat,lon"` |
| R2 | Return route map | GeoJSON LineString in JSON + `/api/route/map/` Leaflet page |
| R3 | Optimal (cheapest) fuel stops | Greedy min-cost refuel over snapped stations |
| R4 | 500 mi range, multiple stops | Tank capacity = 500 mi of range |
| R5 | Total fuel cost @ 10 mpg | Sum of gallons bought × price |
| R6 | Uses supplied CSV | `load_stations` command |
| R7 | Free map/routing API | OSRM public server |
| R8 | Latest stable Django | Pinned in requirements |
| R9 | Fast | In-memory numpy index + result cache |
| R10 | Few routing calls | Exactly 1 per request; geocoding is offline |
| R11 | Loom + Postman | See `05_DELIVERABLES.md` |
| R12 | GitHub | Public repo |
