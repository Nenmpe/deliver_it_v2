from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/users/', include('users.urls')),
    path('api/supplier/', include('supplier.urls')),
    path('api/customer/', include('customer.urls')),
    path('api/driver/', include('driver.urls')),
    path('api/inventory/', include('items.urls')),
    path('api/delivery/', include('orders.urls')),
]
