from django.contrib import admin
from .models import Customer

# Register your models here.

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('uid', 'user', 'country', 'state', 'city', 'postal_code')
    search_fields = ('user__fullname',)
    list_filter = ('user__is_customer',)


admin.site.register(Customer, CustomerAdmin)
