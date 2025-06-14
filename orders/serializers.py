from rest_framework import serializers
from .models import Order, Delivery
from driver.models import Driver
from django.contrib.gis.geos import Point, LineString
from .utils import generate_path_matrix
from items.models import Item
from datetime import datetime
from django.utils.timezone import now

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
        if value <= now():
            raise serializers.ValidationError("Delivery date must be in the future.")
        return value

    def create(self, validated_data):
        driver = validated_data['driver']
        delivery_date = validated_data['delivery_date']
        deliveries_data = validated_data['orders']

        # Create new order
        order = Order.objects.create(
            driver=driver,
            delivery_date=delivery_date,
            supplier=self.context['request'].user.supplier
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
            vehicle_speed_kmph=driver.vehicle_speed
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
        items_map = {item.uid: item for item in Item.objects.filter(uid__in=item_ids)}

        # Prepare the delivery instances
        deliveries = []
        for delivery_data in deliveries_data:
            item = items_map[delivery_data['item']]
            price = item.price * delivery_data['qty']
            point = Point(delivery_data['longitude'], delivery_data['latitude'], srid=4326)

            deliveries.append(Delivery(
                order=order,
                item=item,
                qty=delivery_data['qty'],
                price=price,
                customer_id=delivery_data['customer'],
                instruction=delivery_data.get('instruction', ''),
                delivery_location=point
            ))

        # Bulk create all deliveries in one query
        Delivery.objects.bulk_create(deliveries)

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
    path_coords = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['order_id', 'supplier', 'supplier_name', 'driver', 'driver_name', 
                 'delivery_date', 'estimated_time', 'total_distance_km', 
                 'path_coords', 'status', 'created_at', 'deliveries']
        
    def get_path_coords(self, obj):
        coords = obj.path_coords or []
        try:
            return [[lat, lon] for lon, lat in coords]
        except (TypeError, ValueError):
            return []

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


