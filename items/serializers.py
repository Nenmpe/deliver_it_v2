from rest_framework.serializers import ModelSerializer
from items.models import Item

class ItemSerializer(ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['uid', 'created_at', 'updated_at']

    def create(self, validated_data):
        item = Item.objects.create(**validated_data)
        return item