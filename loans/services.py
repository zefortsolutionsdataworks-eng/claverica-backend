from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import uuid
from .models import LoanProduct, Loan, LoanRepayment
from wallet.services import TransactionService
from notifications.services import NotificationService
from common.constants import (
    LOAN_PENDING, LOAN_APPROVED, LOAN_DISBURSED, LOAN_ACTIVE, 
    LOAN_PAID, LOAN_DEFAULTED, LOAN_REJECTED, STATUS_COMPLETED
)

class LoanService:
    @staticmethod
    def generate_reference():
        return f"LOAN-{uuid.uuid4().hex[:12].upper()}"
    
    @staticmethod
    def calculate_credit_score(user):
        score = 500
        wallets = user.wallets.all()
        total_balance = sum(w.balance for w in wallets)
        if total_balance > 1000: score += 100
        if total_balance > 5000: score += 100
        paid_loans = user.loans.filter(status=LOAN_PAID).count()
        score += paid_loans * 50
        defaulted_loans = user.loans.filter(status=LOAN_DEFAULTED).count()
        score -= defaulted_loans * 100
        if user.kyc_level == 'VERIFIED': score += 50
        elif user.kyc_level == 'PREMIUM': score += 100
        return max(300, min(850, score))
    
    @staticmethod
    @transaction.atomic
    def apply_for_loan(user, wallet, product, principal_amount, tenure_days):
        if principal_amount < product.minimum_amount:
            raise ValueError(f"Minimum loan amount is {product.minimum_amount}")
        if principal_amount > product.maximum_amount:
            raise ValueError(f"Maximum loan amount is {product.maximum_amount}")
        if tenure_days < product.minimum_tenure_days:
            raise ValueError(f"Minimum tenure is {product.minimum_tenure_days} days")
        if tenure_days > product.maximum_tenure_days:
            raise ValueError(f"Maximum tenure is {product.maximum_tenure_days} days")
        active_loans = user.loans.filter(status__in=[LOAN_ACTIVE, LOAN_APPROVED, LOAN_DISBURSED]).count()
        if active_loans > 0:
            raise ValueError("You have an active loan. Please repay it before applying for a new one")
        
        annual_rate = product.interest_rate / Decimal('100')
        daily_rate = annual_rate / Decimal('365')
        interest_amount = principal_amount * daily_rate * Decimal(str(tenure_days))
        origination_fee = (principal_amount * product.origination_fee_percentage) / Decimal('100')
        total_amount = principal_amount + interest_amount + origination_fee
        credit_score = LoanService.calculate_credit_score(user)
        
        loan = Loan.objects.create(
            user=user,
            wallet=wallet,
            product=product,
            principal_amount=principal_amount,
            interest_amount=interest_amount,
            origination_fee=origination_fee,
            total_amount=total_amount,
            balance=total_amount,
            tenure_days=tenure_days,
            status=LOAN_PENDING,
            credit_score=credit_score
        )
        
        if credit_score >= 650:
            LoanService.approve_loan(loan, auto_approved=True)
        
        NotificationService.send_notification(
            user=user,
            notification_type='LOAN_APPROVED',
            title='Loan Application Submitted',
            message=f'Your loan application for {principal_amount} {wallet.currency} has been submitted'
        )
        return loan
