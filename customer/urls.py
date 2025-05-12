from django.urls import path
from .views import CustomerSignupView, CustomerLoginView

urlpatterns = [
    path('signup/', CustomerSignupView.as_view(), name='supplier_signup'),
    path('signin/', CustomerLoginView.as_view(), name='supplier_signin'),
]
