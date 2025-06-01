from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from users.models import User
from supplier.models import Supplier
from customer.models import Customer
from driver.models import Driver

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        type_data = {}

        is_supplier = self.user.is_supplier
        is_customer = self.user.is_customer
        is_driver = self.user.is_driver

        type_str = 'Supplier' if is_supplier else (
            'Customer' if is_customer else (
                'Driver' if is_driver else 'User'
            )
        )

        if is_supplier:
            try:
                supplier = Supplier.objects.get(user=self.user)
                type_data = {
                    'uid': str(supplier.uid),
                    'company_name': supplier.company_name,
                    'pan_no': supplier.pan_no,
                    'company_location': supplier.company_location.geojson if supplier.company_location else None
                }
            except Supplier.DoesNotExist:
                type_data = None

        elif is_customer:
            try:
                customer = Customer.objects.get(user=self.user)
                type_data = {
                    'uid': customer.uid,
                    'country': customer.country,
                    'state': customer.state,
                    'city': customer.city,
                    'postal_code': customer.postal_code
                }
            except Supplier.DoesNotExist:
                type_data = None

        elif is_driver:
            try:
                driver = Driver.objects.get(user=self.user)
                type_data = {
                    'uid': driver.uid,
                    'driving_license_no': driver.driving_license_no,
                    'vehicle_type': driver.vehicle_type,
                    'number_plate_no': driver.number_plate_no,
                    'vehicle_speed': driver.vehicle_speed,
                    'location': driver.location.geojson if driver.location else None,
                    'status': driver.status,
                    'last_updated': driver.last_updated.isoformat() if driver.last_updated else None
                }
            except Supplier.DoesNotExist:
                type_data = None
        

        # Add custom user fields to response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'fullname': self.user.fullname,
            'is_supplier': is_supplier,
            'is_customer': is_customer,
            'is_driver': is_driver,
            type_str: type_data
        }
        
        return data
