from django.db import models
import uuid
from django.contrib.gis.db import models as gis_models
from customer.models import Customer
from supplier.models import Supplier
from driver.models import Driver
from items.models import Item
from django.utils import timezone
from users.models import User


class Order(models.Model):
    status_choices = [
        ('pending', 'Pending'),
        ('picked_up', 'Picked Up'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    driver = models.ForeignKey(Driver, on_delete=models.SET_NULL, null=True, blank=True)
    delivery_date = models.DateTimeField()
    estimated_time = models.DurationField(null=True, blank=True)
    total_distance_km = models.FloatField(null=True, blank=True)
    path_coords = models.JSONField(null=True, blank=True)
    delivery_path = gis_models.LineStringField(null=True, blank=True, srid=4326)
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return str(self.order_id)

class Delivery(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='deliveries')
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    delivery_location = gis_models.PointField(geography=True)
    instruction = models.TextField(blank=True)

    def __str__(self):
        return f"Delivery to {self.customer.user.fullname} in order {self.order.order_id}"

class OrderRequest(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='order_requests')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='order_requests')
    quantity = models.PositiveIntegerField()
    date = models.DateTimeField()
    delivery_location = gis_models.PointField(geography=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='order_requests')
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"OrderRequest {self.uid} for {self.supplier} - {self.item}"
