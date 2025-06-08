from rest_framework import serializers
from .models import Order
from driver.models import Driver
from django.contrib.gis.geos import Point, LineString
from .utils import get_nearest_driver, generate_path_matrix
from items.models import Item

class OrderSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    class Meta:
        model = Order
        fields = [
            'order_id', 'supplier', 'item', 'qty', 'price', 'customer',
            'delivery_date', 'instruction', 'driver',
            'latitude', 'longitude',
            'estimated_time', 'total_distance_km', 'path_coords',
        ]
        read_only_fields = ['order_id', 'price', 'driver', 'supplier']

    def validate(self, attrs):
        item = attrs['item']
        # Optional: Enforce that item.supplier matches request.user.supplier
        # supplier = attrs['supplier']
        # if item.supplier != supplier:
        #     raise serializers.ValidationError("Item does not belong to the supplier.")
        return attrs

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

        print("✅ Step 3: Finding nearest driver")
        driver = get_nearest_driver(delivery_location)
        if not driver:
            raise serializers.ValidationError("No available driver found.")

        validated_data['driver'] = driver

        print("✅ Step 4: Generating path matrix")
        # Calculate path, time, and distance using OSRM
        result = generate_path_matrix(
            delivery_points=[delivery_location],
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
