import uuid
from rest_framework import serializers
from users.models import User
from .models import Customer
from django.contrib.auth import authenticate
from supplier.models import Supplier
from items.models import Item

class CustomerSignupSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    country = serializers.CharField()
    state = serializers.CharField()
    city = serializers.CharField()
    postal_code = serializers.CharField()

    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'fullname', 'contact_no', 'address', 'is_customer', 'terms_accepted',
                  'country', 'state', 'city', 'postal_code']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.pop('password2'):
            raise serializers.ValidationError("Passwords do not match.")
        if not attrs.get('terms_accepted'):
            raise serializers.ValidationError("You must accept the terms and conditions.")
        if not attrs.get('is_customer', False):
            raise serializers.ValidationError("Invalid user type for customer signup.")
        return attrs

    def create(self, validated_data):
        country = validated_data.pop("country")
        state = validated_data.pop("state")
        city = validated_data.pop("city")
        postal_code = validated_data.pop("postal_code")
        user = User.objects.create_user(**validated_data)
        Customer.objects.create(user=user, uid=uuid.uuid4(), country=country, state=state, city=city, postal_code=postal_code)
        return user


class CustomerSigninSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user is None:
            raise serializers.ValidationError('Invalid login credentials')
        if not user.is_customer:
            raise serializers.ValidationError('Not a customer account')
        data['user'] = user
        return data

class SupplierItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['uid', 'name', 'description', 'price', 'quantity']

class SupplierWithItemsSerializer(serializers.ModelSerializer):
    items = SupplierItemSerializer(source='item_set', many=True, read_only=True)
    company_name = serializers.CharField()
    supplier_name = serializers.CharField(source='user.fullname')
    company_location = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = ['uid', 'company_name', 'supplier_name', 'pan_no', 'company_location', 'items']

    def get_company_location(self, obj):
        if obj.company_location:
            return {
                'latitude': obj.company_location.y,
                'longitude': obj.company_location.x
            }
        return None