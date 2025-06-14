from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework import status

from .models import Order
from .serializers import BatchedOrderSerializer, OrderListSerializer, CustomerOrderSerializer
from users.permissions import IsSupplier, IsDriver
from .utils import send_order_notification


class IsSupplierOrDriverOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                   (request.user.is_supplier or request.user.is_driver or request.user.is_customer))


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    permission_classes = [IsAuthenticated, IsSupplierOrDriverOrCustomer]

    def get_serializer_class(self):
        if self.action == 'create':
            return BatchedOrderSerializer
        elif self.request.user.is_customer:
            return CustomerOrderSerializer
        return OrderListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        user = self.request.user
        if user.is_supplier:
            return Order.objects.filter(supplier__user=user)
        elif user.is_driver:
            return Order.objects.filter(driver__user=user)
        elif user.is_customer:
            return Order.objects.filter(deliveries__customer__user=user).distinct()
        return Order.objects.none()

    def create(self, request, *args, **kwargs):
        supplier = request.user.supplier
        context = {'request': request}

        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        # You don't need to validate `item.supplier` here because each item is handled in the serializer
        order = serializer.save()  # supplier is set via `get_or_create()` inside serializer

        # Get all users to notify
        users_to_notify = []
        
        # Add driver
        if order.driver:
            users_to_notify.append(order.driver.user)
        
        # Add customers
        customer_users = [delivery.customer.user for delivery in order.deliveries.all()]
        users_to_notify.extend(customer_users)

        # Prepare notification data
        title = "New Order Created"
        body = f"New order {order.order_id} has been created by {supplier.company_name}. "
        body += f"Delivery is scheduled for {order.delivery_date}."
        
        # Additional data to send with notification
        data = {
            'order_id': str(order.order_id),
            'type': 'order_created',
            'delivery_date': order.delivery_date.isoformat(),
            'supplier_name': supplier.company_name
        }
        
        send_order_notification(
            order=order,
            notification_type='order_created',
            users=users_to_notify,
            title=title,
            body=body,
            data=data
        )

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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'status': 'success',
            'message': 'Order deleted successfully'
        }, status=status.HTTP_200_OK)
