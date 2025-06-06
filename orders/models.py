from django.db import models
import uuid
from django.contrib.gis.db import models as gis_models
from customer.models import Customer
from supplier.models import Supplier
from driver.models import Driver
from items.models import Item
from django.utils import timezone


class Order(models.Model):
    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_orders')
    delivery_location = gis_models.PointField(geography=True)
    delivery_date = models.DateTimeField()
    instruction = models.TextField(blank=True)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)

     # ✅ New fields
    estimated_time = models.DurationField(null=True, blank=True)
    total_distance_km = models.FloatField(null=True, blank=True)
    path_coords = models.JSONField(null=True, blank=True)  # Stores ordered list of (lat, lon)

    # For map path
    delivery_path = gis_models.LineStringField(null=True, blank=True, srid=4326)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.order_id)
