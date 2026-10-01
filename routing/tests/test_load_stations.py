from django.test import TestCase
from django.core.management import call_command
from routing.models import Station

class LoadStationsTestCase(TestCase):
    def test_load_stations_command(self):
        call_command("load_stations")
        count = Station.objects.count()
        self.assertEqual(count, 6614)

        # Check a known station instance
        station = Station.objects.filter(city__iexact="Chicago").first()
        self.assertIsNotNone(station)
        self.assertTrue(24.0 <= station.latitude <= 50.0)
        self.assertTrue(-125.0 <= station.longitude <= -66.0)
        self.assertGreater(station.price_per_gallon, 0)
