from django.urls import path
from .views import CustomerSignupView, CustomerLoginView, CustomerDashboardView, SupplierListView

urlpatterns = [
    path('signup/', CustomerSignupView.as_view(), name='customer-signup'),
    path('signin/', CustomerLoginView.as_view(), name='supplier_signin'),
    path('dashboard/', CustomerDashboardView.as_view(), name='customer-dashboard'),
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),
]
