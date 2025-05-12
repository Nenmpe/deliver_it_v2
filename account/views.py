import random
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .models import PasswordResetOTP
from rest_framework.permissions import IsAuthenticated

User = get_user_model()

class RequestOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist'}, status=404)

        otp = f"{random.randint(100000, 999999)}"
        PasswordResetOTP.objects.create(user=user, otp=otp)

        # Send OTP via email
        send_mail(
            subject='Your Password Reset OTP',
            message=f'Your OTP is {otp}. It expires in 10 minutes.',
            from_email='no-reply@deliverit.com',
            recipient_list=[user.email],
        )

        return Response({'message': 'OTP sent to email'}, status=200)
    

class VerifyOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        try:
            user = User.objects.get(email=email)
            otp_entry = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).latest('created_at')
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            return Response({'error': 'Invalid OTP or email'}, status=400)

        if not otp_entry.is_valid():
            return Response({'error': 'OTP expired or already used'}, status=400)

        return Response({'message': 'OTP verified'}, status=200)
    

class ResetPasswordWithOTPView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')

        if not email or not otp or not new_password or not new_password_confirm:
            return Response({'error': 'Fields are missing'}, status=400)

        if new_password != new_password_confirm:
            return Response({'error': 'Passwords do not match'}, status=400)

        try:
            user = User.objects.get(email=email)
            otp_entry = PasswordResetOTP.objects.filter(user=user, otp=otp, is_used=False).latest('created_at')
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            return Response({'error': 'Invalid OTP or email'}, status=400)

        if not otp_entry.is_valid():
            return Response({'error': 'OTP expired or already used'}, status=400)

        # Set new password
        user.set_password(new_password)
        user.save()

        # Mark OTP as used
        otp_entry.is_used = True
        otp_entry.save()

        return Response({'message': 'Password reset successful'}, status=200)
    

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')

        # Check current password
        if not user.check_password(current_password):
            return Response({'error': 'Current password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if new passwords match
        if new_password != new_password_confirm:
            return Response({'error': 'New passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        # Optional: validate password strength
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError
        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

        # Set new password
        user.set_password(new_password)
        user.save()

        return Response({'message': 'Password changed successfully. You will now be logged out of your session and login using your new password.'}, status=status.HTTP_200_OK)