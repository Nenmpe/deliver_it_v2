from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from users.serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsDriver
from .serializers import DriverSerializer

class DriverSignupView(APIView):
    def post(self, request):
        serializer = DriverSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Driver account created successfully. Please log in."},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DriverLoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)

        if user and user.is_driver:
            serializer = CustomTokenObtainPairSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response({"detail": "Invalid credentials or user type."}, status=status.HTTP_401_UNAUTHORIZED)


class DriverDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        return Response({
            "message": f"Welcome Driver {request.user.fullname}"
        })