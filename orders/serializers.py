from rest_framework import serializers
from .models import Order
from driver.models import Driver
from django.contrib.gis.geos import Point
from .utils import get_nearest_driver, generate_path_matrix
from items.models import Item
from django.contrib.gis.geos import LineString

class OrderSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'supplier', 'item', 'qty', 'price', 'customer',
            'delivery_date', 'instruction', 'driver',
            'latitude', 'longitude',
            'estimated_time', 'total_distance_km', 'path_coords',  # <-- New
        ]
        read_only_fields = ['order_id', 'price', 'driver']

    def validate(self, attrs):
        item = attrs['item']
        supplier = attrs['supplier']
        if item.supplier != supplier:
            raise serializers.ValidationError("Item does not belong to the supplier.")
        return attrs

    def create(self, validated_data):
        lat = validated_data.pop('latitude')
        lon = validated_data.pop('longitude')
        delivery_location = Point(lon, lat, srid=4326)

        item = validated_data['item']
        qty = validated_data['qty']
        validated_data['price'] = item.price * qty
        validated_data['delivery_location'] = delivery_location

        # Assign nearest available driver
        driver = get_nearest_driver(delivery_location)
        if not driver:
            raise serializers.ValidationError("No available driver found.")

        validated_data['driver'] = driver

        # Calculate path, time, and distance using OSRM
        result = generate_path_matrix(
            delivery_points=[delivery_location],
            start_point=driver.location,
            vehicle_speed_kmph=driver.vehicle_speed
        )

        validated_data['estimated_time'] = result['estimated_time']
        validated_data['total_distance_km'] = result['total_distance_km']
        validated_data['path_coords'] = result['path_coords']

        # ✅ Save path as LineString for admin map visualization
        path_coords = result['path_coords']
        if path_coords:
            # Debug print to check what coordinates we're getting
            print(f"Path coordinates count: {len(path_coords)}")
            print(f"First few coordinates: {path_coords[:3]}")
            
            # OSRM already returns (lon, lat) which is what LineString needs
            # No need to swap coordinates
            validated_data['path_coords'] = path_coords  # Save original format for API response
            validated_data['delivery_path'] = LineString(path_coords)  # Convert for GIS

        # Create the order
        order = Order.objects.create(**validated_data)
        return order
