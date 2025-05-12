from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsSupplier
from items.models import Item
from .serializers import ItemSerializer

class ItemViewSet(ModelViewSet):
    serializer_class = ItemSerializer
    permission_classes = [IsAuthenticated, IsSupplier]
    queryset = Item.objects.all()

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.is_supplier:
            return self.queryset.filter(supplier__user=user)
        return self.queryset.none()

    def perform_create(self, serializer):
        supplier = self.request.user.supplier  # OneToOneField from Supplier to User
        serializer.save(supplier=supplier)
