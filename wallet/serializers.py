from rest_framework import serializers
from decimal import Decimal
from .models import Wallet, Transaction, TransferLimit, FeeConfiguration
from core.models import User

class WalletSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'user_email', 'currency', 'balance', 
                  'available_balance', 'is_active', 'is_primary', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'balance', 'available_balance', 'created_at', 'updated_at']

class TransactionSerializer(serializers.ModelSerializer):
    wallet_currency = serializers.CharField(source='wallet.currency', read_only=True)
    user_email = serializers.EmailField(source='wallet.user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'wallet', 'wallet_currency', 'user_email', 'transaction_type', 
                  'amount', 'fee', 'currency', 'status', 'balance_before', 'balance_after',
                  'reference', 'description', 'recipient_email', 'metadata', 'created_at']
        read_only_fields = ['id', 'balance_before', 'balance_after', 'reference', 'created_at']

class TransferSerializer(serializers.Serializer):
    recipient_email = serializers.EmailField(required=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    currency = serializers.CharField(max_length=3, default='USD')
    description = serializers.CharField(required=False, allow_blank=True)
    pin = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate_recipient_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Recipient not found")
        request = self.context.get('request')
        if request and request.user.email == value:
            raise serializers.ValidationError("Cannot transfer to yourself")
        return value

class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    currency = serializers.CharField(max_length=3, default='USD')
    description = serializers.CharField(required=False, allow_blank=True)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    currency = serializers.CharField(max_length=3, default='USD')
    description = serializers.CharField(required=False, allow_blank=True)
    pin = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

class TransferLimitSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    daily_remaining = serializers.SerializerMethodField()
    monthly_remaining = serializers.SerializerMethodField()
    
    class Meta:
        model = TransferLimit
        fields = ['id', 'user_email', 'daily_limit', 'monthly_limit', 'daily_used', 
                  'monthly_used', 'daily_remaining', 'monthly_remaining', 'last_reset_date']
        read_only_fields = ['id', 'daily_used', 'monthly_used', 'last_reset_date']
    
    def get_daily_remaining(self, obj):
        return obj.daily_limit - obj.daily_used
    
    def get_monthly_remaining(self, obj):
        return obj.monthly_limit - obj.monthly_used

class FeeConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeConfiguration
        fields = ['id', 'transaction_type', 'fee_type', 'fixed_amount', 'percentage', 
                  'minimum_fee', 'maximum_fee', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class CalculateFeeSerializer(serializers.Serializer):
    transaction_type = serializers.CharField(required=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
