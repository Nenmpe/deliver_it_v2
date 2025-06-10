from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Order
from .serializers import BatchedOrderSerializer, OrderListSerializer
from users.permissions import IsSupplier


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated, IsSupplier]

    def get_serializer_class(self):
        if self.action == 'create':
            return BatchedOrderSerializer
        return OrderListSerializer

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

        # You don't need to validate `item.supplier` here because each item is handled in the serializer
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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Orders retrieved successfully',
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'status': 'success',
            'message': 'Order retrieved successfully',
            'data': serializer.data
        })
