from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

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

    def create(self, request, *args, **kwargs):
        print("✅ Authenticated user:", request.user)
        supplier = request.user.supplier

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("❌ Serializer validation failed:")
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # manual validation here:
        item = serializer.validated_data['item']
        if item.supplier != supplier:
            return Response({"error": "Item does not belong to the supplier."}, status=400)
        print("✅ Supplier:", supplier)
        print("✅ Request Data:", request.data)
        print("✅ Validated Data:", serializer.validated_data)


        serializer.save(supplier=supplier)

        return Response(serializer.data, status=status.HTTP_201_CREATED)
