from django.urls import path
from supplier.views import SupplierSignupView, SupplierLoginView, CustomerListView, DriverListView

urlpatterns = [
    path('signup/', SupplierSignupView.as_view(), name='supplier_signup'),
    path('signin/', SupplierLoginView.as_view(), name='supplier_signin'),
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('drivers/', DriverListView.as_view(), name='driver_list'),
]
