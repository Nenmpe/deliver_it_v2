from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Order
from .serializers import BatchedOrderSerializer
from users.permissions import IsSupplier


class OrderViewSet(ModelViewSet):
    serializer_class = BatchedOrderSerializer
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated, IsSupplier]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'supplier'):
            return Order.objects.filter(supplier__user=user)
        return Order.objects.none()

    def create(self, request, *args, **kwargs):
        supplier = request.user.supplier
        context = {'request': request}

        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        # You don’t need to validate `item.supplier` here because each item is handled in the serializer
        order = serializer.save()  # supplier is set via `get_or_create()` inside serializer

        return Response({
            'order_id': str(order.order_id),
            'driver_id': order.driver.uid,
            'delivery_date': order.delivery_date,
            'estimated_time': order.estimated_time,
            'total_distance_km': order.total_distance_km,
            'path_coords': order.path_coords,
            'delivery_count': order.deliveries.count(),
        }, status=status.HTTP_201_CREATED)
