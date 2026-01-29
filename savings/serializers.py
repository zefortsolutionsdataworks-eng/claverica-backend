from rest_framework import serializers
from .models import SavingsProduct, SavingsAccount, SavingsTransaction
from decimal import Decimal

class SavingsProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavingsProduct
        fields = ['id', 'name', 'product_type', 'interest_rate', 'lock_period_days',
                  'early_withdrawal_penalty', 'minimum_deposit', 'maximum_deposit',
                  'is_active', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

class SavingsAccountSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    interest_rate = serializers.DecimalField(source='product.interest_rate', max_digits=5, 
                                             decimal_places=2, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    currency = serializers.CharField(source='wallet.currency', read_only=True)
    
    class Meta:
        model = SavingsAccount
        fields = ['id', 'user', 'user_email', 'wallet', 'currency', 'product', 'product_name',
                  'interest_rate', 'balance', 'total_interest_earned', 'status', 
                  'maturity_date', 'last_interest_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'balance', 'total_interest_earned', 'status',
                           'maturity_date', 'last_interest_date', 'created_at', 'updated_at']

class CreateSavingsAccountSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=True)
    wallet_id = serializers.UUIDField(required=True)
    initial_deposit = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    pin = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4)
    
    def validate_initial_deposit(self, value):
        if value <= 0:
            raise serializers.ValidationError("Initial deposit must be greater than zero")
        return value

class SavingsTransactionSerializer(serializers.ModelSerializer):
    account_id = serializers.UUIDField(source='savings_account.id', read_only=True)
    
    class Meta:
        model = SavingsTransaction
        fields = ['id', 'account_id', 'transaction_type', 'amount', 'balance_before',
                  'balance_after', 'reference', 'description', 'created_at']
        read_only_fields = ['id', 'balance_before', 'balance_after', 'reference', 'created_at']

class DepositToSavingsSerializer(serializers.Serializer):
    savings_account_id = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    pin = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

class WithdrawFromSavingsSerializer(serializers.Serializer):
    savings_account_id = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    pin = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
