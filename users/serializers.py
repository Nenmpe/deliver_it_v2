from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from users.models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add custom user fields to response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'fullname': self.user.fullname,
            'is_supplier': self.user.is_supplier,
            'is_customer': self.user.is_customer,
            'is_driver': self.user.is_driver,
        }
        return data
