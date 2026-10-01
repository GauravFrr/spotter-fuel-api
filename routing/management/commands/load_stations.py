import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from routing.models import Station
from routing.geo import norm_city, get_city_db

CANADIAN_PROVINCES = {"AB", "BC", "MB", "NB", "NS", "ON", "QC", "SK", "YT", "NL", "PE", "NT", "NU"}

class Command(BaseCommand):
    help = "Loads and geocodes fuel stations from data/fuel_prices.csv into the database."

    def handle(self, *args, **options):
        csv_path = getattr(settings, "BASE_DIR", Path(".")) / "data" / "fuel_prices.csv"
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"File not found: {csv_path}"))
            return

        self.stdout.write(f"Reading fuel prices from {csv_path}...")
        city_db = get_city_db()

        # Step 1: Read, filter US only, dedupe by OPIS Truckstop ID keeping cheapest price
        raw_stations = {}
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = row["State"].strip().upper()
                if state in CANADIAN_PROVINCES:
                    continue

                try:
                    opis_id = int(row["OPIS Truckstop ID"].strip())
                    price = float(row["Retail Price"].strip())
                except (ValueError, KeyError):
                    continue

                name = row["Truckstop Name"].strip()
                address = row["Address"].strip()
                city = row["City"].strip()

                # Deduplication rule: keep cheapest price for duplicate OPIS IDs
                if opis_id not in raw_stations or price < raw_stations[opis_id]["price"]:
                    raw_stations[opis_id] = {
                        "opis_id": opis_id,
                        "name": name,
                        "address": address,
                        "city": city,
                        "state": state,
                        "price": price,
                    }

        self.stdout.write(f"Processed {len(raw_stations)} unique US stations. Geocoding...")

        # Step 2: Geocode against city_db
        stations_to_create = []
        skipped_count = 0

        for opis_id, sdata in raw_stations.items():
            c_norm = norm_city(sdata["city"])
            st_code = sdata["state"]

            coords = city_db.get((c_norm, st_code))
            if not coords:
                skipped_count += 1
                continue

            lat, lon = coords
            stations_to_create.append(
                Station(
                    opis_id=opis_id,
                    name=sdata["name"],
                    address=sdata["address"],
                    city=sdata["city"],
                    state=sdata["state"],
                    latitude=lat,
                    longitude=lon,
                    price_per_gallon=sdata["price"],
                )
            )

        # Step 3: Populate DB atomically
        with transaction.atomic():
            Station.objects.all().delete()
            Station.objects.bulk_create(stations_to_create)

        loaded_count = len(stations_to_create)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully loaded {loaded_count} stations into database ({skipped_count} skipped due to geocoding failure)."
            )
        )
