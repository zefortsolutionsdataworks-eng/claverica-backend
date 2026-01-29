from rest_framework import serializers
from .models import LoanProduct, Loan, LoanRepayment
from decimal import Decimal

class LoanProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanProduct
        fields = ['id', 'name', 'interest_rate', 'minimum_amount', 'maximum_amount',
                  'minimum_tenure_days', 'maximum_tenure_days', 'origination_fee_percentage',
                  'is_active', 'description', 'created_at']
        read_only_fields = ['id', 'created_at']

class LoanSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    currency = serializers.CharField(source='wallet.currency', read_only=True)
    
    class Meta:
        model = Loan
        fields = ['id', 'user', 'user_email', 'wallet', 'currency', 'product', 'product_name',
                  'principal_amount', 'interest_amount', 'origination_fee', 'total_amount',
                  'amount_paid', 'balance', 'tenure_days', 'status', 'disbursement_date',
                  'due_date', 'paid_date', 'rejection_reason', 'credit_score', 'created_at']
        read_only_fields = ['id', 'user', 'interest_amount', 'origination_fee', 'total_amount',
                           'amount_paid', 'balance', 'status', 'disbursement_date', 'due_date',
                           'paid_date', 'rejection_reason', 'credit_score', 'created_at']

class ApplyForLoanSerializer(serializers.Serializer):
    product_id = serializers.UUIDField(required=True)
    wallet_id = serializers.UUIDField(required=True)
    principal_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    tenure_days = serializers.IntegerField(required=True)
    
    def validate_principal_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Loan amount must be greater than zero")
        return value
    
    def validate_tenure_days(self, value):
        if value <= 0:
            raise serializers.ValidationError("Tenure must be greater than zero")
        return value

class LoanRepaymentSerializer(serializers.ModelSerializer):
    loan_id = serializers.UUIDField(source='loan.id', read_only=True)
    
    class Meta:
        model = LoanRepayment
        fields = ['id', 'loan_id', 'amount', 'balance_before', 'balance_after',
                  'reference', 'payment_method', 'created_at']
        read_only_fields = ['id', 'balance_before', 'balance_after', 'reference', 'created_at']

class RepayLoanSerializer(serializers.Serializer):
    loan_id = serializers.UUIDField(required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    pin = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4)
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Repayment amount must be greater than zero")

class ApproveLoanSerializer(serializers.Serializer):
    approved = serializers.BooleanField(required=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
