from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from common.models import TimeStampedModel
from common.constants import SAVINGS_PRODUCT_TYPE_CHOICES, SAVINGS_STATUS_CHOICES


class SavingsProduct(TimeStampedModel):
    """Savings product configuration"""
    name = models.CharField(max_length=100)
    product_type = models.CharField(max_length=20, choices=SAVINGS_PRODUCT_TYPE_CHOICES)
    description = models.TextField()
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Annual interest rate percentage"
    )
    lock_period_days = models.IntegerField(default=0, help_text="Lock-in period in days (0 for flexible)")
    early_withdrawal_penalty = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Penalty percentage for early withdrawal"
    )
    minimum_deposit = models.DecimalField(max_digits=12, decimal_places=2)
    maximum_deposit = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'savings_products'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.interest_rate}% APY"


class SavingsAccount(TimeStampedModel):
    """User savings accounts"""
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='savings_accounts')
    wallet = models.ForeignKey('wallet.Wallet', on_delete=models.CASCADE, related_name='savings_accounts')
    product = models.ForeignKey(SavingsProduct, on_delete=models.PROTECT, related_name='accounts')
    
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_interest_earned = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    status = models.CharField(max_length=20, choices=SAVINGS_STATUS_CHOICES, default='ACTIVE')
    maturity_date = models.DateTimeField(null=True, blank=True)
    last_interest_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'savings_accounts'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.product.name} - {self.balance}"


class SavingsTransaction(TimeStampedModel):
    """Savings deposit/withdrawal transactions"""
    TRANSACTION_TYPE_CHOICES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('INTEREST', 'Interest Credit'),
    ]

    savings_account = models.ForeignKey(SavingsAccount, on_delete=models.CASCADE, related_name='transactions')
    reference = models.CharField(max_length=100, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_before = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)
    penalty_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Early withdrawal penalty if applicable"
    )

    class Meta:
        db_table = 'savings_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference} - {self.transaction_type} - {self.amount}"
