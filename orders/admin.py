from django.contrib import admin
from .models import Order
from leaflet.admin import LeafletGeoAdmin


@admin.register(Order)
class OrderAdmin(LeafletGeoAdmin):
    ordering = ['-created_at']
    list_display = (
        'order_id', 'supplier', 'item', 'qty', 'price', 'customer',
        'delivery_location', 'delivery_date', 'instruction', 'driver',
        'estimated_time', 'total_distance_km', 'combined_order_count'  # ✅ Added
    )
    search_fields = ('supplier__company_name', 'driver__user__fullname')
    # list_filter = ('supplier', )

    # Optional: if you want to show both location and path on map
    settings_overrides = {
        'DEFAULT_CENTER': (27.7172, 85.3240),
        'DEFAULT_ZOOM': 12,
        'MIN_ZOOM': 10,
        'MAX_ZOOM': 18,
    }

    def combined_order_count(self, obj):
        return Order.objects.filter(driver=obj.driver).count()
    combined_order_count.short_description = 'Deliveries by driver'

