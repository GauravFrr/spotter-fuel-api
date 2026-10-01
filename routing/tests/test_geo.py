from unittest.mock import patch, MagicMock
from django.test import TestCase
from routing.geo import norm_city, resolve_location, resolve_state, get_nominatim_user_agent

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

    @patch("routing.geo.requests.get")
    def test_resolve_location_nominatim_fallback_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"lat": "39.7392", "lon": "-104.9903"}]
        mock_get.return_value = mock_resp

        # Use an unrecognized city string that triggers Nominatim fallback
        lat, lon = resolve_location("UnrecognizedCustomTown99, CO")
        self.assertAlmostEqual(lat, 39.7392, delta=0.001)
        self.assertAlmostEqual(lon, -104.9903, delta=0.001)

        # Verify requests.get was called with proper headers & params
        mock_get.assert_called_once()
        _, kwargs = mock_get.call_args
        self.assertEqual(kwargs["headers"]["User-Agent"], get_nominatim_user_agent())
        self.assertEqual(kwargs["params"]["countrycodes"], "us")
        self.assertEqual(kwargs["timeout"], 5.0)

    @patch("routing.geo.requests.get")
    def test_resolve_location_nominatim_fallback_failure(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            resolve_location("NonExistentCity12345, CO")
        self.assertIn("could not be resolved offline or via Nominatim fallback", str(ctx.exception))

    def test_resolve_location_errors(self):
        with self.assertRaises(ValueError):
            resolve_location("")

        # Outside US coordinates
        with self.assertRaises(ValueError):
            resolve_location("10.0, 10.0")
