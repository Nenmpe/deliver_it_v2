from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from supplier.serializers import SupplierSignupSerializer, CustomerListSerializer, DriverListSerializer
from users.serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsSupplier
from users.models import User

class SupplierSignupView(APIView):
    def post(self, request):
        serializer = SupplierSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Supplier account created successfully. Please log in."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SupplierLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)

        if user and user.is_supplier:
            serializer = CustomTokenObtainPairSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid credentials or user type."}, status=status.HTTP_401_UNAUTHORIZED)


class SupplierDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsSupplier]

    def get(self, request):
        return Response({
            "message": f"Welcome Supplier {request.user.fullname}"
        })


class CustomerListView(APIView):
    permission_classes = [IsAuthenticated, IsSupplier]

    def get(self, request):
        customers = User.objects.filter(is_customer=True)
        serializer = CustomerListSerializer(customers, many=True)
        return Response({
            'status': 'success',
            'message': 'Customers retrieved successfully',
            'data': serializer.data
        })


class DriverListView(APIView):
    permission_classes = [IsAuthenticated, IsSupplier]

    def get(self, request):
        drivers = User.objects.filter(is_driver=True, driver__status='available')
        serializer = DriverListSerializer(drivers, many=True, context={'request': request})
        return Response({
            'status': 'success',
            'message': 'Drivers retrieved successfully',
            'data': serializer.data
        })