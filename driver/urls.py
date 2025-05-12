from django.urls import path
from .views import DriverSignupView, DriverLoginView

urlpatterns = [
    path('signup/', DriverSignupView.as_view(), name='supplier_signup'),
    path('signin/', DriverLoginView.as_view(), name='supplier_signin'),
]
