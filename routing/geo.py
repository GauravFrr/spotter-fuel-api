import csv
import re
from pathlib import Path
from django.conf import settings

US_STATES = {
    'ALABAMA': 'AL', 'ALASKA': 'AK', 'ARIZONA': 'AZ', 'ARKANSAS': 'AR', 'CALIFORNIA': 'CA',
    'COLORADO': 'CO', 'CONNECTICUT': 'CT', 'DELAWARE': 'DE', 'FLORIDA': 'FL', 'GEORGIA': 'GA',
    'HAWAII': 'HI', 'IDAHO': 'ID', 'ILLINOIS': 'IL', 'INDIANA': 'IN', 'IOWA': 'IA',
    'KANSAS': 'KS', 'KENTUCKY': 'KY', 'LOUISIANA': 'LA', 'MAINE': 'ME', 'MARYLAND': 'MD',
    'MASSACHUSETTS': 'MA', 'MICHIGAN': 'MI', 'MINNESOTA': 'MN', 'MISSISSIPPI': 'MS',
    'MISSOURI': 'MO', 'MONTANA': 'MT', 'NEBRASKA': 'NE', 'NEVADA': 'NV', 'NEW HAMPSHIRE': 'NH',
    'NEW JERSEY': 'NJ', 'NEW MEXICO': 'NM', 'NEW YORK': 'NY', 'NORTH CAROLINA': 'NC',
    'NORTH DAKOTA': 'ND', 'OHIO': 'OH', 'OKLAHOMA': 'OK', 'OREGON': 'OR', 'PENNSYLVANIA': 'PA',
    'RHODE ISLAND': 'RI', 'SOUTH CAROLINA': 'SC', 'SOUTH DAKOTA': 'SD', 'TENNESSEE': 'TN',
    'TEXAS': 'TX', 'UTAH': 'UT', 'VERMONT': 'VT', 'VIRGINIA': 'VA', 'WASHINGTON': 'WA',
    'WEST VIRGINIA': 'WV', 'WISCONSIN': 'WI', 'WYOMING': 'WY', 'DISTRICT OF COLUMBIA': 'DC'
}

STATE_CODE_SET = set(US_STATES.values())

_CITY_DB = None


def norm_city(name: str) -> str:
    """
    Normalise city name for offline lookup.
    Lowercases, strips punctuation, and standardises common prefixes.
    """
    if not name:
        return ""
    text = name.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    words = text.split()
    res = []
    for w in words:
        if w in ("saint", "st"):
            res.append("st")
        elif w in ("mount", "mt"):
            res.append("mt")
        elif w in ("fort", "ft"):
            res.append("ft")
        else:
            res.append(w)
    return " ".join(res)


def resolve_state(state_input: str) -> str:
    """
    Normalise state input into 2-letter postal code or return upper string if valid.
    """
    st = state_input.strip().upper()
    if st in STATE_CODE_SET:
        return st
    clean_name = re.sub(r"[^\w\s]", "", state_input).strip().upper()
    if clean_name in US_STATES:
        return US_STATES[clean_name]
    return st


def get_city_db() -> dict:
    """
    Lazy-load US cities database from data/us_cities.csv into an in-memory dict:
    (norm_city, STATE_CODE) -> (latitude, longitude)
    """
    global _CITY_DB
    if _CITY_DB is not None:
        return _CITY_DB

    _CITY_DB = {}
    cities_file = getattr(settings, "BASE_DIR", Path(".")) / "data" / "us_cities.csv"
    if not cities_file.exists():
        raise FileNotFoundError(f"US cities table not found at {cities_file}")

    with open(cities_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            city_n = norm_city(r["CITY"])
            st_code = r["STATE_CODE"].strip().upper()
            try:
                lat = float(r["LATITUDE"])
                lon = float(r["LONGITUDE"])
                _CITY_DB[(city_n, st_code)] = (lat, lon)
            except (ValueError, KeyError):
                continue

    return _CITY_DB


def resolve_location(loc_input: str) -> tuple[float, float]:
    """
    Resolve location string (either 'lat, lon' or 'City, State') to (latitude, longitude).
    Raises ValueError on invalid input or location not found.
    """
    if not loc_input or not loc_input.strip():
        raise ValueError("Location input cannot be empty.")

    text = loc_input.strip()

    # 1. Check if 'lat, lon' format
    if "," in text:
        parts = text.split(",")
        if len(parts) == 2:
            try:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                # Basic sanity check for continental US / North America lat/lon
                if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                    # Validate within reasonable US bounding box
                    if 24.0 <= lat <= 50.0 and -125.0 <= lon <= -66.0:
                        return (lat, lon)
                    raise ValueError(f"Coordinates ({lat}, {lon}) are outside the continental US.")
            except ValueError as e:
                if "outside the continental US" in str(e):
                    raise
                # Not numeric floats, fall through to City, State resolution

    # 2. Treat as 'City, State'
    if "," in text:
        city_part, state_part = text.rsplit(",", 1)
        c_norm = norm_city(city_part)
        st_code = resolve_state(state_part)

        city_db = get_city_db()
        coords = city_db.get((c_norm, st_code))
        if coords:
            return coords

        raise ValueError(f"City '{city_part.strip()}, {state_part.strip()}' could not be resolved from US cities database.")

    raise ValueError("Location must be in 'City, State' format (e.g. 'Chicago, IL') or 'lat, lon' coordinates.")
