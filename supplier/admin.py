from django.contrib import admin
from .models import Supplier
from leaflet.admin import LeafletGeoAdmin

# Register your models here.

@admin.register(Supplier)
class SupplierAdmin(LeafletGeoAdmin):
    list_display = ('uid', 'user', 'company_name', 'pan_no', 'company_location')
    search_fields = ('company_name',)
    list_filter = ('user__is_supplier',)
