from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from .models import Order
from .serializers import OrderSerializer
from users.permissions import IsSupplier

class OrderViewSet(ModelViewSet):
    serializer_class = OrderSerializer
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated, IsSupplier]

    def get_queryset(self):
        user = self.request.user
        if user.is_supplier:
            return Order.objects.filter(supplier__user=user)
        return Order.objects.none()
