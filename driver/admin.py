from django.contrib import admin
from .models import Driver
from leaflet.admin import LeafletGeoAdmin

# Register your models here.

@admin.register(Driver)
class DriverAdmin(LeafletGeoAdmin):
    list_display = ('uid', 'user', 'driving_license_no', 'vehicle_type', 'number_plate_no', 'vehicle_speed', 'location', 'status')
    search_fields = ('user__fullname', 'number_plate_no')
    list_filter = ('user__is_driver', 'vehicle_type', 'status')

