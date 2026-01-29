from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from common.models import TimeStampedModel
from common.constants import LOAN_STATUS_CHOICES, LOAN_PENDING


class LoanProduct(TimeStampedModel):
    """Loan product configuration"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
        help_text="Annual interest rate percentage"
    )
    minimum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    maximum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    minimum_tenure_days = models.IntegerField(help_text="Minimum loan duration in days")
    maximum_tenure_days = models.IntegerField(help_text="Maximum loan duration in days")
    origination_fee_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="One-time origination fee percentage"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'loan_products'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.interest_rate}% APR)"


class Loan(TimeStampedModel):
    """User loan applications and active loans"""
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='loans')
    wallet = models.ForeignKey('wallet.Wallet', on_delete=models.CASCADE, related_name='loans')
    product = models.ForeignKey(LoanProduct, on_delete=models.PROTECT, related_name='loans')
    
    # Loan amounts
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    origination_fee = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Repayment tracking
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Loan terms
    tenure_days = models.IntegerField(help_text="Loan duration in days")
    
    # Status and dates
    status = models.CharField(max_length=20, choices=LOAN_STATUS_CHOICES, default=LOAN_PENDING)
    disbursement_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    # Credit assessment
    credit_score = models.IntegerField(null=True, blank=True, help_text="Internal credit score")
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'loans'
        ordering = ['-created_at']

    def __str__(self):
        return f"Loan #{self.id} - {self.user.email} - {self.status}"


class LoanRepayment(TimeStampedModel):
    """Loan repayment transactions"""
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    reference = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'loan_repayments'
        ordering = ['-created_at']

    def __str__(self):
        return f"Repayment {self.reference} - {self.amount}"
