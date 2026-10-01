from django.db import models

class Station(models.Model):
    """
    Represents a fuel truck stop station with geocoded coordinates and retail fuel price.
    """
    opis_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=10)
    latitude = models.FloatField()
    longitude = models.FloatField()
    price_per_gallon = models.FloatField()

    def __str__(self):
        return f"{self.name} (#{self.opis_id}) - {self.city}, {self.state}: ${self.price_per_gallon:.3f}"
