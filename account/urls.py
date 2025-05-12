from django.urls import path
from .views import RequestOTPView, VerifyOTPView, ResetPasswordWithOTPView, ChangePasswordView


urlpatterns = [
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordWithOTPView.as_view(), name='reset-password'),

    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]