from django.contrib import admin
from .models import Item


# Register your models here.

class ItemAdmin(admin.ModelAdmin):
    list_display = ('uid', 'name', 'description', 'price', 'quantity', 'supplier')
    search_fields = ('name',)
    list_filter = ('supplier',)


admin.site.register(Item, ItemAdmin)
