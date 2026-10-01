from django.test import TestCase
from routing.geo import norm_city, resolve_location, resolve_state

class GeoTestCase(TestCase):
    def test_norm_city(self):
        self.assertEqual(norm_city("Saint Louis"), "st louis")
        self.assertEqual(norm_city("St. Louis"), "st louis")
        self.assertEqual(norm_city("Fort Worth"), "ft worth")
        self.assertEqual(norm_city("Mount Pleasant"), "mt pleasant")
        self.assertEqual(norm_city("  CHICAGO! "), "chicago")

    def test_resolve_state(self):
        self.assertEqual(resolve_state("CO"), "CO")
        self.assertEqual(resolve_state("Colorado"), "CO")
        self.assertEqual(resolve_state(" Illinois "), "IL")

    def test_resolve_location_city_state(self):
        lat, lon = resolve_location("Denver, CO")
        self.assertAlmostEqual(lat, 39.7392, delta=0.1)
        self.assertAlmostEqual(lon, -104.9903, delta=0.1)

        lat2, lon2 = resolve_location("Denver, Colorado")
        self.assertEqual(lat, lat2)
        self.assertEqual(lon, lon2)

    def test_resolve_location_coords(self):
        lat, lon = resolve_location("39.74, -104.99")
        self.assertAlmostEqual(lat, 39.74)
        self.assertAlmostEqual(lon, -104.99)

    def test_resolve_location_errors(self):
        with self.assertRaises(ValueError):
            resolve_location("")

        with self.assertRaises(ValueError):
            resolve_location("NonExistentCity12345, CO")

        # Outside US coordinates
        with self.assertRaises(ValueError):
            resolve_location("10.0, 10.0")

        with self.assertRaises(ValueError):
            resolve_location("Invalid Location Format No Comma")
