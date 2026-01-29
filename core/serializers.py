from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, KYCDocument, UserActivity
from wallet.models import Wallet
from common.constants import KYC_BASIC

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 
            'phone_number', 'date_of_birth', 'country', 'kyc_level',
            'email_verified', 'phone_verified', 'is_active', 
            'daily_transfer_limit', 'monthly_transfer_limit',
            'two_factor_enabled', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email_verified', 'phone_verified', 'kyc_level', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'password', 'password2', 'first_name', 'last_name', 'phone_number', 'country']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number', ''),
            country=validated_data.get('country', ''),
            kyc_level=KYC_BASIC,
        )
        
        # Create default USD wallet
        Wallet.objects.create(
            user=user,
            currency='USD',
            is_primary=True
        )
        
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid email or password')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
        else:
            raise serializers.ValidationError('Must include "email" and "password"')
        
        attrs['user'] = user
        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "New password fields didn't match."})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value

class SetPinSerializer(serializers.Serializer):
    pin = serializers.CharField(required=True, write_only=True, min_length=4, max_length=4)
    pin2 = serializers.CharField(required=True, write_only=True, min_length=4, max_length=4)
    
    def validate(self, attrs):
        if attrs['pin'] != attrs['pin2']:
            raise serializers.ValidationError({"pin": "PIN fields didn't match."})
        
        if not attrs['pin'].isdigit():
            raise serializers.ValidationError({"pin": "PIN must contain only digits."})
        
        return attrs

class VerifyPinSerializer(serializers.Serializer):
    pin = serializers.CharField(required=True, write_only=True, min_length=4, max_length=4)

class KYCDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KYCDocument
        fields = ['id', 'document_type', 'document_number', 'document_file', 'status', 
                  'rejection_reason', 'created_at', 'reviewed_at']
        read_only_fields = ['id', 'status', 'rejection_reason', 'reviewed_at', 'created_at']

class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['id', 'activity_type', 'ip_address', 'user_agent', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']
