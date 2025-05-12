from django.urls import path
from users.views import LogoutView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
