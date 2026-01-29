from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from common.models import TimeStampedModel
from common.constants import CURRENCY_CHOICES, TRANSACTION_TYPE_CHOICES, TRANSACTION_STATUS_CHOICES, TRANSACTION_PENDING

class Wallet(TimeStampedModel):
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='wallets')
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    available_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'wallets'
        unique_together = ['user', 'currency']
        verbose_name = 'Wallet'
        verbose_name_plural = 'Wallets'
    
    def __str__(self):
        return f"{self.user.email} - {self.currency} - {self.balance}"


class Transaction(TimeStampedModel):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default=TRANSACTION_PENDING)
    
    # Balances (for audit trail)
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Reference
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    
    # Related party (for transfers)
    recipient_wallet = models.ForeignKey(
        Wallet, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transactions'
    )
    recipient_email = models.EmailField(blank=True, null=True)
    
    # Metadata
    metadata = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.reference} - {self.transaction_type} - {self.amount} {self.currency}"


class TransferLimit(TimeStampedModel):
    user = models.OneToOneField('core.User', on_delete=models.CASCADE, related_name='transfer_limit')
    daily_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1000.00'))
    monthly_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('10000.00'))
    daily_used = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    monthly_used = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    last_reset_date = models.DateField(auto_now_add=True)
    
    class Meta:
        db_table = 'transfer_limits'
        verbose_name = 'Transfer Limit'
        verbose_name_plural = 'Transfer Limits'
    
    def __str__(self):
        return f"{self.user.email} - Daily: {self.daily_used}/{self.daily_limit}"


class FeeConfiguration(TimeStampedModel):
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES, unique=True)
    fee_type = models.CharField(max_length=20, choices=[
        ('FIXED', 'Fixed'),
        ('PERCENTAGE', 'Percentage'),
        ('HYBRID', 'Hybrid'),
    ])
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    minimum_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    maximum_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'fee_configurations'
        verbose_name = 'Fee Configuration'
        verbose_name_plural = 'Fee Configurations'
    
    def __str__(self):
        return f"{self.transaction_type} - {self.fee_type}"
    
    def calculate_fee(self, amount):
        """Calculate fee based on configuration"""
        if not self.is_active:
            return Decimal('0.00')
        
        fee = Decimal('0.00')
        
        if self.fee_type == 'FIXED':
            fee = self.fixed_amount
        elif self.fee_type == 'PERCENTAGE':
            fee = (amount * self.percentage) / Decimal('100')
        elif self.fee_type == 'HYBRID':
            fee = self.fixed_amount + ((amount * self.percentage) / Decimal('100'))
        
        # Apply min/max constraints
        if fee < self.minimum_fee:
            fee = self.minimum_fee
        if self.maximum_fee and fee > self.maximum_fee:
            fee = self.maximum_fee
        
        return fee

