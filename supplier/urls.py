from django.urls import path
from supplier.views import SupplierSignupView, SupplierLoginView

urlpatterns = [
    path('signup/', SupplierSignupView.as_view(), name='supplier_signup'),
    path('signin/', SupplierLoginView.as_view(), name='supplier_signin'),
]
