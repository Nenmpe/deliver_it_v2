from rest_framework import serializers
from .models import Order
from driver.models import Driver
from django.contrib.gis.geos import Point, LineString
from .utils import generate_path_matrix
from items.models import Item
from datetime import datetime
from django.utils.timezone import now

class OrderSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    driver = serializers.PrimaryKeyRelatedField(queryset=Driver.objects.filter(status='available'))

    class Meta:
        model = Order
        fields = [
            'order_id', 'supplier', 'item', 'qty', 'price', 'customer',
            'delivery_date', 'instruction', 'driver',
            'latitude', 'longitude',
            'estimated_time', 'total_distance_km', 'path_coords',
        ]
        read_only_fields = ['order_id', 'price', 'supplier']

    def validate(self, attrs):
        item = attrs['item']
        # Optional: Enforce that item.supplier matches request.user.supplier
        # supplier = attrs['supplier']
        # if item.supplier != supplier:
        #     raise serializers.ValidationError("Item does not belong to the supplier.")
        return attrs
    
    def validate_delivery_date(self, value):
        if value <= now():
            raise serializers.ValidationError("Delivery date must be in the future.")
        return value

    def create(self, validated_data):
        print("✅ Step 1: Entering create()")
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)

        if lat is None or lon is None:
            raise serializers.ValidationError("Latitude and Longitude are required.")

        print("✅ Step 2: Creating Point")
        delivery_location = Point(float(lon), float(lat), srid=4326)

        item = validated_data['item']
        qty = validated_data['qty']
        validated_data['price'] = item.price * qty
        validated_data['delivery_location'] = delivery_location
        driver = validated_data['driver']

        print("✅ Step 3: Generating path matrix")
        # Calculate path, time, and distance using OSM
        # Fetch existing orders for this driver (exclude ones already delivered if needed)
        existing_orders = Order.objects.filter(driver=driver)
        existing_locations = [o.delivery_location for o in existing_orders]

        # Add new one
        delivery_points = existing_locations + [delivery_location]
        result = generate_path_matrix(
            delivery_points=delivery_points,
            start_point=driver.location,
            vehicle_speed_kmph=driver.vehicle_speed
        )

        print("⬅️ Returned from generate_path_matrix")
        
        if result is None:
            raise serializers.ValidationError("Routing failed: could not calculate estimated time.")

        print("✅ Step 5: Matrix result =", result)
        validated_data['estimated_time'] = result['estimated_time']
        validated_data['total_distance_km'] = result['total_distance_km']
        validated_data['path_coords'] = result['path_coords']

        path_coords = result['path_coords']
        if path_coords:
            line_coords = [(lon, lat) for lat, lon in path_coords]
            validated_data['path_coords'] = line_coords
            validated_data['delivery_path'] = LineString(line_coords)
            # Debug print to check what coordinates we're getting
            print(f"Path coordinates count: {len(path_coords)}")
            print(f"First few coordinates: {path_coords[:3]}")
            
            # OSRM already returns (lon, lat) which is what LineString needs
            # No need to swap coordinates
            validated_data['path_coords'] = path_coords  # Save original format for API response
            validated_data['delivery_path'] = LineString(path_coords)  # Convert for GIS

        print("✅ Step 6: Creating order object")
        order = Order.objects.create(**validated_data)
        print("✅ Step 7: Order created:", order)
        return order
