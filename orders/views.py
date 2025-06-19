from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .models import Order, OrderRequest
from .serializers import (
    BatchedOrderSerializer, OrderListSerializer, CustomerOrderSerializer,
    OrderStatusUpdateSerializer, OrderRequestSerializer
)
from users.permissions import IsSupplier, IsDriver, IsCustomer
from rest_framework import viewsets, mixins


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
        elif self.action == 'update_status':
            return OrderStatusUpdateSerializer
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

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated, IsDriver])
    def update_status(self, request, pk=None):
        order = self.get_object()
        
        # Verify that the order belongs to the requesting driver
        if order.driver.user != request.user:
            return Response(
                {"detail": "You can only update status of orders assigned to you."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # Get users to notify about status change
        users_to_notify = []
        users_to_notify.append(order.supplier.user)  # Notify supplier
        customer_users = [delivery.customer.user for delivery in order.deliveries.all()]
        users_to_notify.extend(customer_users)  # Notify customers

        # Prepare notification data
        status_display = dict(Order.status_choices)[order.status]
        title = f"Order Status Updated"
        body = f"Order {order.order_id} status has been updated to {status_display}."
        
        data = {
            'order_id': str(order.order_id),
            'type': 'order_updated',
            'status': order.status,
            'status_display': status_display
        }
        
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        # Check for OrderRequest update in payload
        request_id = request.data.get('requestId')
        is_accepted = request.data.get('is_accepted')
        if request_id and is_accepted is True:
            try:
                order_request = OrderRequest.objects.get(uid=request_id)
                order_request.is_accepted = True
                order_request.save()
            except OrderRequest.DoesNotExist:
                return Response({'detail': 'OrderRequest not found.'}, status=status.HTTP_400_BAD_REQUEST)
        # Continue with normal order creation
        supplier = request.user.supplier
        context = {'request': request}

        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        order = serializer.save()  # supplier is set via `get_or_create()` inside serializer

        users_to_notify = []
        if order.driver:
            users_to_notify.append(order.driver.user)
        customer_users = [delivery.customer.user for delivery in order.deliveries.all()]
        users_to_notify.extend(customer_users)

        title = "New Order Created"
        body = f"New order {order.order_id} has been created by {supplier.company_name}. "
        body += f"Delivery is scheduled for {order.delivery_date}."
        data = {
            'order_id': str(order.order_id),
            'type': 'order_created',
            'delivery_date': order.delivery_date.isoformat(),
            'supplier_name': supplier.company_name
        }
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


class IsSupplierOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.is_supplier or request.user.is_customer))


class OrderRequestViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin):
    queryset = OrderRequest.objects.all()
    serializer_class = OrderRequestSerializer
    permission_classes = [IsAuthenticated, IsSupplierOrCustomer]

    def get_queryset(self):
        user = self.request.user
        if user.is_supplier:
            return OrderRequest.objects.filter(supplier__user=user, is_accepted=False)
        elif user.is_customer:
            return OrderRequest.objects.filter(customer__user=user, is_accepted=True)
        return OrderRequest.objects.none()

    def create(self, request, *args, **kwargs):
        if not request.user.is_customer:
            return Response({'detail': 'Only customers can create order requests.'}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not request.user.is_supplier:
            return Response({'detail': 'Only suppliers can update order requests.'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        if 'is_accepted' in request.data:
            instance.is_accepted = request.data['is_accepted']
            instance.save()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return Response({'detail': 'No valid fields to update.'}, status=status.HTTP_400_BAD_REQUEST)
