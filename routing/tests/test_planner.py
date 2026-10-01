from unittest.mock import patch, MagicMock
from django.test import TestCase
from routing.planner import plan_fuel, fetch_route, stations_on_route, build_plan
from routing.models import Station

class PlannerTestCase(TestCase):
    def test_short_trip_single_fill(self):
        nodes = [
            {"mile_marker": 0.0, "price": 3.50},
            {"mile_marker": 300.0, "price": 0.0},
        ]
        result = plan_fuel(nodes, total_mi=300.0)
        self.assertEqual(result["total_gallons"], 30.0)
        self.assertEqual(result["total_fuel_cost"], 105.0)
        self.assertEqual(len(result["fuel_stops"]), 0)
        self.assertEqual(result["initial_fill"]["gallons"], 30.0)

    def test_cheaper_station_ahead(self):
        nodes = [
            {"mile_marker": 0.0, "price": 4.00},
            {"mile_marker": 200.0, "price": 3.00, "station": {"name": "Cheaper Stop"}},
            {"mile_marker": 600.0, "price": 0.0},
        ]
        result = plan_fuel(nodes, total_mi=600.0)
        self.assertEqual(result["total_gallons"], 60.0)
        self.assertEqual(result["total_fuel_cost"], 200.0)
        self.assertEqual(len(result["fuel_stops"]), 1)
        self.assertEqual(result["fuel_stops"][0]["name"], "Cheaper Stop")
        self.assertEqual(result["fuel_stops"][0]["gallons"], 40.0)

    def test_expensive_then_cheap(self):
        nodes = [
            {"mile_marker": 0.0, "price": 3.00},
            {"mile_marker": 100.0, "price": 4.00, "station": {"name": "Expensive Stop"}},
            {"mile_marker": 400.0, "price": 2.50, "station": {"name": "Cheap Stop"}},
            {"mile_marker": 800.0, "price": 0.0},
        ]
        result = plan_fuel(nodes, total_mi=800.0)
        self.assertEqual(result["total_gallons"], 80.0)
        self.assertEqual(result["total_fuel_cost"], 220.0)
        self.assertEqual(len(result["fuel_stops"]), 1)
        self.assertEqual(result["fuel_stops"][0]["name"], "Cheap Stop")

    def test_gap_exceeds_range_error(self):
        nodes = [
            {"mile_marker": 0.0, "price": 3.50},
            {"mile_marker": 600.0, "price": 0.0},
        ]
        with self.assertRaises(ValueError) as ctx:
            plan_fuel(nodes, total_mi=600.0)
        self.assertIn("No fuel station within 500.0 miles", str(ctx.exception))

    def test_dp_cross_check(self):
        nodes = [
            {"mile_marker": 0.0, "price": 3.80},
            {"mile_marker": 150.0, "price": 3.20, "station": {"name": "S1"}},
            {"mile_marker": 350.0, "price": 3.90, "station": {"name": "S2"}},
            {"mile_marker": 550.0, "price": 3.10, "station": {"name": "S3"}},
            {"mile_marker": 850.0, "price": 3.40, "station": {"name": "S4"}},
            {"mile_marker": 1100.0, "price": 0.0},
        ]
        greedy_res = plan_fuel(nodes, total_mi=1100.0, range_mi=500.0, mpg=10.0)
        
        dp = {}
        dp[(0, 0)] = 0.0
        N = len(nodes)
        for i in range(N):
            m_i = nodes[i]["mile_marker"]
            p_i = nodes[i]["price"]
            for f in range(51):
                if (i, f) not in dp:
                    continue
                c_cost = dp[(i, f)]
                for buy_f in range(0, 51 - f):
                    new_f = f + buy_f
                    new_cost = c_cost + buy_f * p_i
                    for j in range(i + 1, N):
                        dist = nodes[j]["mile_marker"] - m_i
                        if dist > 500:
                            break
                        needed_gal = int(round(dist / 10.0))
                        if new_f >= needed_gal:
                            rem_f = new_f - needed_gal
                            state = (j, rem_f)
                            if state not in dp or new_cost < dp[state]:
                                dp[state] = new_cost

        min_dp_cost = min(cost for (idx, f), cost in dp.items() if idx == N - 1)
        self.assertAlmostEqual(greedy_res["total_fuel_cost"], min_dp_cost, delta=1.0)

    @patch("routing.planner.requests.get")
    def test_fetch_route_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "routes": [{
                "distance": 160934.4,  # 100 miles
                "duration": 7200,      # 2 hours
                "geometry": {"type": "LineString", "coordinates": [[-104.99, 39.73], [-96.79, 32.77]]}
            }]
        }
        mock_get.return_value = mock_resp

        res = fetch_route((39.73, -104.99), (32.77, -96.79))
        self.assertEqual(res["distance_miles"], 100.0)
        self.assertEqual(res["duration_hours"], 2.0)
        self.assertIn("geometry", res)
        # Assert requests.get was called exactly once
        self.assertEqual(mock_get.call_count, 1)

    @patch("routing.planner.requests.get")
    def test_fetch_route_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_get.return_value = mock_resp

        with self.assertRaises(ValueError) as ctx:
            fetch_route((39.73, -104.99), (32.77, -96.79))
        self.assertIn("HTTP status 500", str(ctx.exception))
