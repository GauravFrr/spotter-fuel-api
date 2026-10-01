import os
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.core.cache import cache
from routing.models import Station

class ApiTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        cache.clear()

        # Create sample station in test DB
        Station.objects.create(
            opis_id=1,
            name="Test Truckstop",
            address="123 Main St",
            city="Des Moines",
            state="IA",
            latitude=41.5868,
            longitude=-93.625,
            price_per_gallon=3.20,
        )

    def tearDown(self):
        cache.clear()

    @patch("routing.planner.requests.get")
    def test_route_api_get_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "routes": [{
                "distance": 482803.2, # 300 miles
                "duration": 18000,
                "geometry": {"type": "LineString", "coordinates": [[-87.6298, 41.8781], [-93.625, 41.5868]]}
            }]
        }
        mock_get.return_value = mock_resp

        response = self.client.get("/api/route/?start=Chicago, IL&finish=Des Moines, IA")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["start"], "Chicago, IL")
        self.assertEqual(data["finish"], "Des Moines, IA")
        self.assertEqual(data["distance_miles"], 300.0)
        self.assertIn("total_fuel_cost", data)
        self.assertIn("map_url", data)

    @patch("routing.planner.requests.get")
    def test_route_api_post_json_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "routes": [{
                "distance": 482803.2,
                "duration": 18000,
                "geometry": {"type": "LineString", "coordinates": [[-87.6298, 41.8781], [-93.625, 41.5868]]}
            }]
        }
        mock_get.return_value = mock_resp

        response = self.client.post(
            "/api/route/",
            data={"start": "Chicago, IL", "finish": "Des Moines, IA"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["distance_miles"], 300.0)

    def test_route_api_missing_params(self):
        response = self.client.get("/api/route/?start=Chicago, IL")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_route_api_unknown_location(self):
        response = self.client.get("/api/route/?start=UnknownFakeCity999, IL&finish=Chicago, IL")
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    @patch("routing.planner.requests.get")
    def test_route_api_caching(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "routes": [{
                "distance": 160934.4,
                "duration": 7200,
                "geometry": {"type": "LineString", "coordinates": [[-87.6298, 41.8781], [-88.0, 41.9]]}
            }]
        }
        mock_get.return_value = mock_resp

        # First request (cache miss)
        res1 = self.client.get("/api/route/?start=Chicago, IL&finish=Denver, CO")
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(mock_get.call_count, 1)

        # Second request (cache hit)
        res2 = self.client.get("/api/route/?start=Chicago, IL&finish=Denver, CO")
        self.assertEqual(res2.status_code, 200)
        # OSRM requests.get should NOT have been called a second time!
        self.assertEqual(mock_get.call_count, 1)

    @patch("routing.planner.requests.get")
    def test_route_map_view(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "routes": [{
                "distance": 160934.4,
                "duration": 7200,
                "geometry": {"type": "LineString", "coordinates": [[-87.6298, 41.8781], [-88.0, 41.9]]}
            }]
        }
        mock_get.return_value = mock_resp

        response = self.client.get("/api/route/map/?start=Chicago, IL&finish=Denver, CO")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fuel Route Map")
        self.assertContains(response, "leaflet.css")

    @unittest.skipUnless(os.environ.get("LIVE_TEST"), "Live test skipped by default")
    def test_live_route(self):
        response = self.client.get("/api/route/?start=Chicago, IL&finish=Los Angeles, CA")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(data["distance_miles"], 1800)
