from rest_framework.routers import DefaultRouter
from items.views import ItemViewSet

router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='item')

urlpatterns = router.urls
