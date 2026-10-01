import math
import time
import requests
import numpy as np
from typing import List, Dict, Any, Tuple
from urllib.parse import quote_plus
from django.conf import settings
from routing.geo import resolve_location
from routing.models import Station

# In-memory station numpy cache
_STATION_CACHE = None


def get_station_cache() -> Dict[str, Any]:
    """
    Lazy-load fuel stations into in-memory numpy arrays for high-performance snapping.
    """
    global _STATION_CACHE
    if _STATION_CACHE is not None:
        return _STATION_CACHE

    stations = list(
        Station.objects.all().values(
            "opis_id",
            "name",
            "address",
            "city",
            "state",
            "latitude",
            "longitude",
            "price_per_gallon",
        )
    )

    if not stations:
        # If DB not loaded yet, return empty structure
        _STATION_CACHE = {
            "stations": [],
            "lats": np.array([]),
            "lons": np.array([]),
            "prices": np.array([]),
        }
        return _STATION_CACHE

    _STATION_CACHE = {
        "stations": stations,
        "lats": np.array([s["latitude"] for s in stations], dtype=np.float64),
        "lons": np.array([s["longitude"] for s in stations], dtype=np.float64),
        "prices": np.array([s["price_per_gallon"] for s in stations], dtype=np.float64),
    }
    return _STATION_CACHE


def invalidate_station_cache():
    """Clear station cache if database is reloaded."""
    global _STATION_CACHE
    _STATION_CACHE = None


def fetch_route(start_coords: Tuple[float, float], finish_coords: Tuple[float, float]) -> Dict[str, Any]:
    """
    Calls OSRM API to fetch driving route between start (lat, lon) and finish (lat, lon).
    Returns dict containing distance_miles, duration_hours, and GeoJSON LineString geometry.
    """
    start_lat, start_lon = start_coords
    finish_lat, finish_lon = finish_coords

    osrm_base = getattr(settings, "OSRM_URL", "https://router.project-osrm.org").rstrip("/")
    timeout_s = getattr(settings, "ROUTING_TIMEOUT_S", 15.0)

    # OSRM coordinate format is lon,lat
    url = f"{osrm_base}/route/v1/driving/{start_lon},{start_lat};{finish_lon},{finish_lat}?overview=full&geometries=geojson"

    try:
        response = requests.get(url, timeout=timeout_s)
    except requests.RequestException as e:
        raise ValueError(f"Routing service connection failed: {str(e)}")

    if response.status_code != 200:
        raise ValueError(f"Routing service returned HTTP status {response.status_code}")

    try:
        data = response.json()
    except Exception:
        raise ValueError("Routing service returned invalid JSON response.")

    routes = data.get("routes")
    if not routes or len(routes) == 0:
        raise ValueError("No route found between the specified locations.")

    primary_route = routes[0]
    distance_meters = primary_route.get("distance", 0.0)
    duration_seconds = primary_route.get("duration", 0.0)
    geometry = primary_route.get("geometry", {})

    distance_miles = round(distance_meters / 1609.344, 1)
    duration_hours = round(duration_seconds / 3600.0, 1)

    return {
        "distance_miles": distance_miles,
        "duration_hours": duration_hours,
        "geometry": geometry,
    }


def stations_on_route(
    route_coords: List[List[float]],
    total_dist_mi: float,
    max_offset_mi: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Fast numpy-based snapping of stations within max_offset_mi of route vertices.
    Returns snapped stations sorted by mile_marker ascending.
    """
    st_data = get_station_cache()
    stations = st_data["stations"]
    if not stations:
        return []

    st_lats = st_data["lats"]
    st_lons = st_data["lons"]
    st_prices = st_data["prices"]

    route_pts = np.array(route_coords, dtype=np.float64)  # shape (M, 2): [lon, lat]
    route_lons = route_pts[:, 0]
    route_lats = route_pts[:, 1]

    M = len(route_pts)
    if M == 0:
        return []

    # Downsample route for snapping if vertex count > 1500
    step = max(1, M // 1500)
    ds_lats = route_lats[::step]
    ds_lons = route_lons[::step]

    mid_lat_rad = math.radians(ds_lats.mean()) if len(ds_lats) > 0 else 0.0
    cos_mid = math.cos(mid_lat_rad)

    # Compute cumulative distance along route vertices
    if len(ds_lats) > 1:
        dlat = (ds_lats[1:] - ds_lats[:-1]) * 69.0
        dlon = (ds_lons[1:] - ds_lons[:-1]) * (69.0 * cos_mid)
        seg_dists = np.sqrt(dlat**2 + dlon**2)
        cum_dist = np.insert(np.cumsum(seg_dists), 0, 0.0)
        if cum_dist[-1] > 0:
            cum_dist = cum_dist * (total_dist_mi / cum_dist[-1])
    else:
        cum_dist = np.array([0.0])

    # Pre-filter by bounding box
    lat_min, lat_max = ds_lats.min(), ds_lats.max()
    lon_min, lon_max = ds_lons.min(), ds_lons.max()
    lat_pad = max_offset_mi / 69.0
    lon_pad = max_offset_mi / (69.0 * cos_mid) if cos_mid > 0 else lat_pad

    bbox_mask = (
        (st_lats >= lat_min - lat_pad)
        & (st_lats <= lat_max + lat_pad)
        & (st_lons >= lon_min - lon_pad)
        & (st_lons <= lon_max + lon_pad)
    )

    cand_indices = np.where(bbox_mask)[0]
    snapped = []

    for idx in cand_indices:
        slat, slon = st_lats[idx], st_lons[idx]
        d_lat = (ds_lats - slat) * 69.0
        d_lon = (ds_lons - slon) * (69.0 * cos_mid)
        d2 = d_lat**2 + d_lon**2
        best_v = np.argmin(d2)
        dist_mi = math.sqrt(d2[best_v])

        if dist_mi <= max_offset_mi:
            snapped.append(
                {
                    "mile_marker": float(cum_dist[best_v]),
                    "miles_off_route": float(dist_mi),
                    "price": float(st_prices[idx]),
                    "station": stations[idx],
                }
            )

    snapped.sort(key=lambda x: x["mile_marker"])
    return snapped


def plan_fuel(
    nodes: List[Dict[str, Any]],
    total_mi: float,
    range_mi: float = 500.0,
    mpg: float = 10.0,
) -> Dict[str, Any]:
    """
    Greedy min-cost fuel optimizer.
    """
    if not nodes:
        raise ValueError("Nodes list cannot be empty.")
    if range_mi <= 0 or mpg <= 0:
        raise ValueError("Range and MPG must be positive numbers.")

    sorted_nodes = sorted(nodes, key=lambda x: x["mile_marker"])

    curr_m = 0.0
    for node in sorted_nodes:
        dist_gap = node["mile_marker"] - curr_m
        if dist_gap > range_mi:
            raise ValueError(f"No fuel station within {range_mi:.1f} miles after mile {curr_m:.1f}")
        curr_m = node["mile_marker"]

    num_nodes = len(sorted_nodes)
    curr_idx = 0
    fuel_remaining_mi = 0.0

    purchases = []

    while curr_idx < num_nodes - 1:
        curr_node = sorted_nodes[curr_idx]
        curr_mile = curr_node["mile_marker"]
        curr_price = curr_node["price"]

        reachable_indices = []
        for j in range(curr_idx + 1, num_nodes):
            dist = sorted_nodes[j]["mile_marker"] - curr_mile
            if dist <= range_mi:
                reachable_indices.append(j)
            else:
                break

        if not reachable_indices:
            raise ValueError(f"No fuel station within {range_mi:.1f} miles after mile {curr_mile:.1f}")

        cheaper_idx = None
        for j in reachable_indices:
            if sorted_nodes[j]["price"] < curr_price:
                cheaper_idx = j
                break

        if cheaper_idx is not None:
            target_node = sorted_nodes[cheaper_idx]
            needed_dist = target_node["mile_marker"] - curr_mile
            needed_fuel = max(0.0, needed_dist - fuel_remaining_mi)
            gallons = needed_fuel / mpg
            cost = gallons * curr_price

            if gallons > 0:
                purchases.append(
                    {
                        "node_idx": curr_idx,
                        "node": curr_node,
                        "gallons": gallons,
                        "price": curr_price,
                        "cost": cost,
                    }
                )
                fuel_remaining_mi += needed_fuel

            fuel_remaining_mi -= needed_dist
            curr_idx = cheaper_idx
        else:
            needed_fuel = range_mi - fuel_remaining_mi
            gallons = max(0.0, needed_fuel) / mpg
            cost = gallons * curr_price

            if gallons > 0:
                purchases.append(
                    {
                        "node_idx": curr_idx,
                        "node": curr_node,
                        "gallons": gallons,
                        "price": curr_price,
                        "cost": cost,
                    }
                )
                fuel_remaining_mi = range_mi

            next_idx = curr_idx + 1
            dist_to_next = sorted_nodes[next_idx]["mile_marker"] - curr_mile
            fuel_remaining_mi -= dist_to_next
            curr_idx = next_idx

    initial_fill = None
    fuel_stops = []
    total_gallons = 0.0
    total_cost = 0.0

    for p in purchases:
        gallons = round(p["gallons"], 2)
        cost = round(p["cost"], 2)
        price = round(p["price"], 3)
        total_gallons += p["gallons"]
        total_cost += p["cost"]

        node = p["node"]
        if p["node_idx"] == 0:
            initial_fill = {
                "gallons": gallons,
                "price_per_gallon": price,
                "cost": cost,
                "note": "Initial fill at departure point (priced at first available station on route)",
            }
        else:
            station_info = node.get("station", {})
            stop_data = {
                "name": station_info.get("name", "Unknown Station"),
                "address": station_info.get("address", ""),
                "city": station_info.get("city", ""),
                "state": station_info.get("state", ""),
                "lat": station_info.get("latitude", 0.0),
                "lon": station_info.get("longitude", 0.0),
                "mile_marker": round(node["mile_marker"], 1),
                "miles_off_route": round(node.get("miles_off_route", 0.0), 1),
                "price_per_gallon": price,
                "gallons": gallons,
                "cost": cost,
            }
            fuel_stops.append(stop_data)

    if initial_fill is None:
        initial_fill = {
            "gallons": 0.0,
            "price_per_gallon": round(sorted_nodes[0]["price"], 3),
            "cost": 0.0,
            "note": "No initial fill needed",
        }

    return {
        "initial_fill": initial_fill,
        "fuel_stops": fuel_stops,
        "total_gallons": round(total_gallons, 2),
        "total_fuel_cost": round(total_cost, 2),
    }


def build_plan(start_location: str, finish_location: str, request_obj=None) -> Dict[str, Any]:
    """
    Orchestration function:
      1. Resolves start/finish to (lat, lon)
      2. Calls OSRM route API
      3. Snaps stations along the route
      4. Executes plan_fuel optimizer
      5. Constructs final response dictionary according to contract
    """
    start_coords = resolve_location(start_location)
    finish_coords = resolve_location(finish_location)

    route_info = fetch_route(start_coords, finish_coords)
    distance_miles = route_info["distance_miles"]
    duration_hours = route_info["duration_hours"]
    geometry = route_info["geometry"]
    coords = geometry.get("coordinates", [])

    range_mi = getattr(settings, "VEHICLE_RANGE_MI", 500.0)
    mpg = getattr(settings, "VEHICLE_MPG", 10.0)
    max_offset_mi = getattr(settings, "MAX_STATION_OFFSET_MI", 10.0)

    # Snap stations along route
    snapped_stations = stations_on_route(coords, distance_miles, max_offset_mi=max_offset_mi)

    # Fallback first station price for node 0 if no stations on route
    first_price = snapped_stations[0]["price"] if snapped_stations else 3.50

    # Build node list for plan_fuel: node 0 is virtual start, node N is virtual finish
    nodes = [{"mile_marker": 0.0, "price": first_price, "station": None}]
    for st in snapped_stations:
        if st["mile_marker"] > 0.1:
            nodes.append(st)
    nodes.append({"mile_marker": distance_miles, "price": 0.0, "station": None})

    plan_res = plan_fuel(nodes, total_mi=distance_miles, range_mi=range_mi, mpg=mpg)

    # Downsample geometry coordinates for clean response size if > 1500 points
    M = len(coords)
    if M > 1500:
        step = max(1, M // 1500)
        ds_coords = coords[::step]
        if ds_coords[-1] != coords[-1]:
            ds_coords.append(coords[-1])
        out_geometry = {"type": "LineString", "coordinates": ds_coords}
    else:
        out_geometry = geometry

    # Build map_url
    map_path = f"/api/route/map/?start={quote_plus(start_location)}&finish={quote_plus(finish_location)}"
    if request_obj:
        map_url = request_obj.build_absolute_uri(map_path)
    else:
        map_url = map_path

    return {
        "start": start_location,
        "finish": finish_location,
        "distance_miles": distance_miles,
        "duration_hours": duration_hours,
        "vehicle": {"range_miles": int(range_mi), "mpg": int(mpg)},
        "initial_fill": plan_res["initial_fill"],
        "fuel_stops": plan_res["fuel_stops"],
        "total_gallons": plan_res["total_gallons"],
        "total_fuel_cost": plan_res["total_fuel_cost"],
        "route": {
            "type": "Feature",
            "properties": {},
            "geometry": out_geometry,
        },
        "map_url": map_url,
    }
