from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, SetPinSerializer, VerifyPinSerializer,
    KYCDocumentSerializer, UserActivitySerializer
)
from .models import KYCDocument, UserActivity

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {'refresh': str(refresh), 'access': str(refresh.access_token)},
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        UserActivity.objects.create(user=user, activity_type='LOGIN', ip_address=request.META.get('REMOTE_ADDR'), user_agent=request.META.get('HTTP_USER_AGENT',''))
        refresh = RefreshToken.for_user(user)
        return Response({'user': UserSerializer(user).data, 'tokens': {'refresh': str(refresh), 'access': str(refresh.access_token)}, 'message': 'Login successful'})

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        try:
            UserActivity.objects.create(user=request.user, activity_type='LOGOUT', ip_address=request.META.get('REMOTE_ADDR'), user_agent=request.META.get('HTTP_USER_AGENT',''))
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    def get_object(self):
        return self.request.user

class UpdateProfileView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer
    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        UserActivity.objects.create(user=user, activity_type='PASSWORD_CHANGE', ip_address=request.META.get('REMOTE_ADDR'))
        return Response({'message': 'Password changed successfully'})

class SetPinView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = SetPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_pin(serializer.validated_data['pin'])
        UserActivity.objects.create(user=user, activity_type='PIN_CHANGE', ip_address=request.META.get('REMOTE_ADDR'))
        return Response({'message': 'PIN set successfully'})

class VerifyPinView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = VerifyPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        is_valid = user.check_pin(serializer.validated_data['pin'])
        return Response({'valid': is_valid, 'message': 'PIN is valid' if is_valid else 'Invalid PIN'})

class UploadKYCDocumentView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = KYCDocumentSerializer
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class KYCStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        documents = KYCDocument.objects.filter(user=user)
        return Response({
            'kyc_level': user.kyc_level,
            'email_verified': user.email_verified,
            'phone_verified': user.phone_verified,
            'documents_count': documents.count(),
            'pending_documents': documents.filter(status='PENDING').count(),
            'approved_documents': documents.filter(status='APPROVED').count(),
            'rejected_documents': documents.filter(status='REJECTED').count(),
        })

class KYCDocumentListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = KYCDocumentSerializer
    def get_queryset(self):
        return KYCDocument.objects.filter(user=self.request.user)

class UserActivityListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserActivitySerializer
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)
