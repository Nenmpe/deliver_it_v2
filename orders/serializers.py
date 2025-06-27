from rest_framework import serializers
from .models import Order, Delivery, OrderRequest
from driver.models import Driver
from django.contrib.gis.geos import Point, LineString
from .utils import generate_path_matrix
from items.models import Item
from datetime import datetime
from django.utils.timezone import now
from supplier.models import Supplier
from users.models import User
from customer.models import Customer

# serializers.py
class DeliveryInputSerializer(serializers.Serializer):
    customer = serializers.UUIDField()
    item = serializers.UUIDField()
    qty = serializers.IntegerField()
    instruction = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

class BatchedOrderSerializer(serializers.Serializer):
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.filter(status='available'))
    delivery_date = serializers.DateTimeField()
    orders = DeliveryInputSerializer(many=True)

    def validate_delivery_date(self, value):
        if value < now():
            raise serializers.ValidationError("Delivery date must be in the future.")
        return value

    def create(self, validated_data):
        driver = validated_data['driver']
        delivery_date = validated_data['delivery_date']
        deliveries_data = validated_data['orders']
        supplier = self.context['request'].user.supplier

        # Create new order
        order = Order.objects.create(
            driver=driver,
            delivery_date=delivery_date,
            supplier=supplier
        )

        # Gather delivery locations
        delivery_points = []
        for delivery in deliveries_data:
            point = Point(delivery['longitude'], delivery['latitude'], srid=4326)
            delivery_points.append(point)

        # Generate path
        result = generate_path_matrix(
            delivery_points=delivery_points,
            start_point=driver.location,
            vehicle_speed_kmph=driver.vehicle_speed,
            supplier_point=supplier.company_location
        )

        if result is None:
            raise serializers.ValidationError("Could not generate route.")
        
        print("Path Coords:", result['path_coords'])
        print("LineString:", [(lon, lat) for lat, lon in result['path_coords']])

        order.estimated_time = result['estimated_time']
        order.total_distance_km = result['total_distance_km']
        order.path_coords = result['path_coords']
        order.delivery_path = LineString(result['path_coords'])
        order.save()

        # Save each delivery
        # First, fetch all needed items in one query
        item_ids = [delivery['item'] for delivery in deliveries_data]
        items = {str(item.uid): item for item in Item.objects.filter(uid__in=item_ids)}

        # Create all deliveries
        for delivery_data in deliveries_data:
            item = items[str(delivery_data['item'])]
            Delivery.objects.create(
                order=order,
                item=item,
                qty=delivery_data['qty'],
                price=item.price * delivery_data['qty'],
                customer_id=delivery_data['customer'],
                delivery_location=Point(delivery_data['longitude'], delivery_data['latitude'], srid=4326),
                instruction=delivery_data.get('instruction', '')
            )

        return order

class DeliverySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    customer_name = serializers.CharField(source='customer.user.fullname', read_only=True)

    class Meta:
        model = Delivery
        fields = ['id', 'item', 'item_name', 'qty', 'price', 'customer', 'customer_name', 'delivery_location', 'instruction']

class CustomerDeliverySerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    customer_name = serializers.CharField(source='customer.user.fullname', read_only=True)

    class Meta:
        model = Delivery
        fields = ['id', 'item', 'item_name', 'qty', 'price', 'customer', 'customer_name', 'delivery_location', 'instruction']

class OrderListSerializer(serializers.ModelSerializer):
    deliveries = DeliverySerializer(many=True, read_only=True)
    driver_name = serializers.CharField(source='driver.user.fullname', read_only=True)
    supplier_name = serializers.CharField(source='supplier.user.fullname', read_only=True)
    supplier_location = serializers.SerializerMethodField()
    path_coords = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['order_id', 'supplier', 'supplier_name', 'supplier_location', 'driver', 'driver_name', 
                 'delivery_date', 'estimated_time', 'total_distance_km', 
                 'path_coords', 'status', 'created_at', 'deliveries']
        
    def get_path_coords(self, obj):
        coords = obj.path_coords or []
        try:
            return [[lat, lon] for lon, lat in coords]
        except (TypeError, ValueError):
            return []

    def get_supplier_location(self, obj):
        if obj.supplier.company_location:
            return {
                'latitude': obj.supplier.company_location.y,
                'longitude': obj.supplier.company_location.x
            }
        return None

class CustomerOrderSerializer(serializers.ModelSerializer):
    deliveries = serializers.SerializerMethodField()
    driver_name = serializers.CharField(source='driver.user.fullname', read_only=True)
    supplier_name = serializers.CharField(source='supplier.user.fullname', read_only=True)

    class Meta:
        model = Order
        fields = ['order_id', 'supplier', 'supplier_name', 'driver', 'driver_name', 
                 'delivery_date', 'deliveries']

    def get_deliveries(self, obj):
        # Get only deliveries for the current customer
        user = self.context['request'].user
        customer_deliveries = obj.deliveries.filter(customer__user=user)
        return CustomerDeliverySerializer(customer_deliveries, many=True).data

class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']
        extra_kwargs = {
            'status': {'choices': Order.status_choices}
        }

    def validate_status(self, value):
        order = self.instance
        current_status = order.status
        
        # Define valid status transitions
        valid_transitions = {
            'pending': ['picked_up', 'cancelled'],
            'picked_up': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],  # No transitions from completed
            'cancelled': []   # No transitions from cancelled
        }
        
        if value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from {current_status} to {value}. "
                f"Valid transitions from {current_status} are: {valid_transitions[current_status]}"
            )
        
        return value

class OrderRequestSerializer(serializers.ModelSerializer):
    supplier = serializers.PrimaryKeyRelatedField(queryset=Supplier.objects.all())
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    customer = serializers.PrimaryKeyRelatedField(read_only=True)
    latitude = serializers.FloatField(write_only=True, required=True)
    longitude = serializers.FloatField(write_only=True, required=True)
    delivery_location = serializers.SerializerMethodField(read_only=True)
    item_name = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = OrderRequest
        fields = ['uid', 'supplier', 'item', 'item_name', 'quantity', 'date', 'latitude', 'longitude', 'delivery_location', 'customer', 'is_accepted']
        read_only_fields = ['uid', 'is_accepted', 'delivery_location', 'customer', 'item_name']

    def validate(self, attrs):
        supplier = attrs.get('supplier')
        item = attrs.get('item')
        if item.supplier != supplier:
            raise serializers.ValidationError('Item must belong to the supplier.')
        return attrs

    def create(self, validated_data):
        latitude = validated_data.pop('latitude')
        longitude = validated_data.pop('longitude')
        validated_data['delivery_location'] = Point(longitude, latitude)
        try:
            validated_data['customer'] =  Customer.objects.get(user=self.context['request'].user)
        except Customer.DoesNotExist:

            raise serializers.ValidationError("Associated Customer profile not found for this user.")

        return super().create(validated_data)
    

    def get_delivery_location(self, obj):
        if obj.delivery_location:
            return {
                'latitude': obj.delivery_location.y,
                'longitude': obj.delivery_location.x
            }
        return None
    
    def get_item_name(self, obj):
        return obj.item.name if obj.item else None


