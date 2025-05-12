import uuid
from rest_framework import serializers
from users.models import User
from supplier.models import Supplier
from django.contrib.gis.geos import Point
from django.contrib.auth import authenticate

class SupplierSignupSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    company_name = serializers.CharField()
    pan_no = serializers.CharField()
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)


    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'fullname', 'contact_no', 'address', 'is_supplier', 'terms_accepted',
                  'company_name', 'pan_no', 'longitude', 'latitude']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.pop('password2'):
            raise serializers.ValidationError("Passwords do not match.")
        if not attrs.get('terms_accepted'):
            raise serializers.ValidationError("You must accept the terms and conditions.")
        if not attrs.get('is_supplier', False):
            raise serializers.ValidationError("Invalid user type for supplier signup.")
        return attrs

    def create(self, validated_data):
        company_name = validated_data.pop('company_name')
        pan_no = validated_data.pop('pan_no')
        lat = validated_data.pop('latitude', None)
        lon = validated_data.pop('longitude', None)

        if lat and lon:
            location = Point(lon, lat)
        user = User.objects.create_user(**validated_data)
        Supplier.objects.create(user=user, uid=uuid.uuid4(), company_name=company_name, pan_no=pan_no, company_location=location)
        return user


class SupplierSigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user is None:
            raise serializers.ValidationError('Invalid login credentials')
        if not user.is_supplier:
            raise serializers.ValidationError('Not a supplier account')
        data['user'] = user
        return data