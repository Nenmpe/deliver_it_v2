from django.contrib.gis.db import models as gis_models
from django.db import models
from django.conf import settings
import uuid

class Driver(models.Model):
    VEHICLE_CHOICES = (
        ('two-wheel', 'Two-Wheel'),
        ('four-wheel', 'Four-Wheel'),
    )

    STATUS_CHOICES = (
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    )

    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    driving_license_no = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES)
    number_plate_no = models.CharField(max_length=50)
    vehicle_speed = models.DecimalField(max_digits=5, decimal_places=2)
    location = gis_models.PointField(geography=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='offline')
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.fullname} - {self.number_plate_no}"
