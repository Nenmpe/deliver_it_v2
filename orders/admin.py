from django.contrib import admin
from .models import Order, Delivery, OrderRequest
from leaflet.admin import LeafletGeoAdmin


@admin.register(Order)
class OrderAdmin(LeafletGeoAdmin):
    ordering = ['-created_at']
    list_display = (
        'order_id', 'supplier', 'delivery_date', 'driver',
        'estimated_time', 'total_distance_km',
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


@admin.register(Delivery)
class DeliveryAdmin(LeafletGeoAdmin):
    list_display = ('order', 'customer', 'item', 'qty', 'total_price', 'delivery_location')

    list_filter = ('order',)

    def total_price(self, obj):
        return obj.price
    
    total_price.short_description = 'Total Price'


@admin.register(OrderRequest)
class OrderRequestAdmin(LeafletGeoAdmin):
    list_display = ('uid', 'supplier', 'item', 'quantity', 'date', 'customer', 'is_accepted')
    list_filter = ('supplier', 'is_accepted')
    search_fields = ('uid', 'supplier__user__fullname', 'item__name', 'customer__user__fullname')