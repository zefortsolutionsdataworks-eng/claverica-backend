from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import uuid
from .models import SavingsProduct, SavingsAccount, SavingsTransaction
from wallet.services import TransactionService, WalletService
from notifications.services import NotificationService
from common.constants import STATUS_COMPLETED

class SavingsService:
    @staticmethod
    def generate_reference():
        return f"SAV-{uuid.uuid4().hex[:12].upper()}"
    
    @staticmethod
    @transaction.atomic
    def create_savings_account(user, wallet, product, initial_deposit, pin):
        if not user.check_pin(pin):
            raise ValueError("Invalid PIN")
        if initial_deposit < product.minimum_deposit:
            raise ValueError(f"Minimum deposit is {product.minimum_deposit}")
        if product.maximum_deposit and initial_deposit > product.maximum_deposit:
            raise ValueError(f"Maximum deposit is {product.maximum_deposit}")
        if wallet.available_balance < initial_deposit:
            raise ValueError("Insufficient wallet balance")
        
        savings_account = SavingsAccount.objects.create(
            user=user,
            wallet=wallet,
            product=product,
            balance=Decimal('0.00'),
            status='ACTIVE',
            last_interest_date=timezone.now()
        )
        
        if product.lock_period_days > 0:
            savings_account.maturity_date = timezone.now() + timedelta(days=product.lock_period_days)
            savings_account.status = 'LOCKED'
            savings_account.save()
        
        SavingsService.deposit_to_savings(
            savings_account=savings_account,
            amount=initial_deposit,
            pin=pin,
            initial=True
        )
        
        return savings_account
    
    @staticmethod
    @transaction.atomic
    def deposit_to_savings(savings_account, amount, pin, initial=False):
        if not initial and not savings_account.user.check_pin(pin):
            raise ValueError("Invalid PIN")
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero")
        
        wallet = savings_account.wallet
        if wallet.available_balance < amount:
            raise ValueError("Insufficient wallet balance")
        
        wallet.balance -= amount
        wallet.available_balance -= amount
        wallet.save()
        
        TransactionService.create_transaction(
            wallet=wallet,
            transaction_type='SAVINGS_DEPOSIT',
            amount=amount,
            description=f"Deposit to {savings_account.product.name}",
            status=STATUS_COMPLETED
        )
        
        balance_before = savings_account.balance
        savings_account.balance += amount
        savings_account.save()
        
        savings_txn = SavingsTransaction.objects.create(
            savings_account=savings_account,
            transaction_type='DEPOSIT',
            amount=amount,
            balance_before=balance_before,
            balance_after=savings_account.balance,
            reference=SavingsService.generate_reference(),
            description='Deposit to savings'
        )
        
        NotificationService.send_notification(
            user=savings_account.user,
            notification_type='SAVINGS_DEPOSIT',
            title='Savings Deposit',
            message=f'You deposited {amount} {wallet.currency} to your {savings_account.product.name} account'
        )
        
        return savings_txn
    
    @staticmethod
    @transaction.atomic
    def withdraw_from_savings(savings_account, amount, pin):
        if not savings_account.user.check_pin(pin):
            raise ValueError("Invalid PIN")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero")
        
        penalty = Decimal('0.00')
        if savings_account.status == 'LOCKED' and savings_account.maturity_date > timezone.now():
            penalty = (amount * savings_account.product.early_withdrawal_penalty) / Decimal('100')
            if penalty > 0:
                amount -= penalty
            else:
                raise ValueError("Cannot withdraw from locked account before maturity")
        
        if savings_account.balance < amount:
            raise ValueError("Insufficient savings balance")
        
        wallet = savings_account.wallet
        balance_before = savings_account.balance
        savings_account.balance -= amount
        savings_account.save()
        
        savings_txn = SavingsTransaction.objects.create(
            savings_account=savings_account,
            transaction_type='WITHDRAWAL',
            amount=amount,
            balance_before=balance_before,
            balance_after=savings_account.balance,
            reference=SavingsService.generate_reference(),
            description='Withdrawal from savings'
        )
        
        if penalty > 0:
            SavingsTransaction.objects.create(
                savings_account=savings_account,
                transaction_type='PENALTY',
                amount=penalty,
                balance_before=savings_account.balance,
                balance_after=savings_account.balance,
                reference=SavingsService.generate_reference(),
                description=f'Early withdrawal penalty ({savings_account.product.early_withdrawal_penalty}%)'
            )
        
        wallet.balance += amount
        wallet.available_balance += amount
        wallet.save()
        
        TransactionService.create_transaction(
            wallet=wallet,
            transaction_type='SAVINGS_WITHDRAWAL',
            amount=amount,
            description=f"Withdrawal from {savings_account.product.name}",
            status=STATUS_COMPLETED
        )
        
        NotificationService.send_notification(
            user=savings_account.user,
            notification_type='WITHDRAWAL',
            title='Savings Withdrawal',
            message=f'You withdrew {amount} {wallet.currency} from your {savings_account.product.name} account'
        )
        
        return savings_txn
    
    @staticmethod
    def calculate_interest_for_all_accounts():
        accounts = SavingsAccount.objects.filter(
            status__in=['ACTIVE', 'LOCKED'],
            balance__gt=0
        )
        results = []
        for account in accounts:
            try:
                interest_txn = SavingsService.calculate_and_credit_interest(account)
                if interest_txn:
                    results.append({'account_id': account.id, 'user': account.user.email, 'interest': interest_txn.amount, 'status': 'success'})
            except Exception as e:
                results.append({'account_id': account.id, 'user': account.user.email, 'status': 'failed', 'error': str(e)})
        return results
