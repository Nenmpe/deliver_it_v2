from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, OrderRequestViewSet

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-requests', OrderRequestViewSet, basename='orderrequest')

urlpatterns = router.urls
