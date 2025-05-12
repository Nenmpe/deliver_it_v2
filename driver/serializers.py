from rest_framework import serializers
import uuid
from users.models import User
from .models import Driver
from django.contrib.gis.geos import Point
from django.contrib.auth import authenticate

class DriverSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)
    driving_license_no = serializers.CharField()
    vehicle_type = serializers.ChoiceField(choices=Driver.VEHICLE_CHOICES)
    number_plate_no = serializers.CharField()
    vehicle_speed = serializers.DecimalField(max_digits=5, decimal_places=2)
    status = serializers.ChoiceField(choices=Driver.STATUS_CHOICES, default='offline')

    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'fullname', 'contact_no', 'address', 'is_driver', 'terms_accepted',
                  'driving_license_no', 'vehicle_type', 'number_plate_no', 'vehicle_speed', 'status', 'longitude', 'latitude']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.pop('password2'):
            raise serializers.ValidationError("Passwords do not match.")
        if not attrs.get('terms_accepted'):
            raise serializers.ValidationError("You must accept the terms and conditions.")
        if not attrs.get('is_driver', False):
            raise serializers.ValidationError("Invalid user type for supplier signup.")
        return attrs

    def create(self, validated_data):
        license_no = validated_data.pop('driving_license_no', None)
        vehicle_type = validated_data.pop('vehicle_type', None)
        number_plate_no = validated_data.pop('number_plate_no', None)
        vehicle_speed = validated_data.pop('vehicle_speed', None)
        status = validated_data.pop('status', None)
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)

        if lat and lon:
            location = Point(lon, lat)

        user = User.objects.create_user(**validated_data)
        driver = Driver.objects.create(user=user, uid=uuid.uuid4(), driving_license_no=license_no,
                                        vehicle_type=vehicle_type, number_plate_no=number_plate_no,
                                        vehicle_speed=vehicle_speed, location=location, status=status)
        return user

    def update(self, instance, validated_data):
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)
        if lat and lon:
            instance.location = Point(lon, lat)
        return super().update(instance, validated_data)

class DriverSigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user is None:
            raise serializers.ValidationError('Invalid login credentials')
        if not user.is_driver:
            raise serializers.ValidationError('Not a driver account')
        data['user'] = user
        return data