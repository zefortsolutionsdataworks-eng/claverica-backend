from django.db import transaction, models
from django.utils import timezone
from decimal import Decimal
import uuid
from .models import Wallet, Transaction, TransferLimit, FeeConfiguration
from notifications.services import NotificationService
from core.models import User
from common.constants import (
    TRANSACTION_TRANSFER, TRANSACTION_DEPOSIT, TRANSACTION_WITHDRAWAL,
    STATUS_COMPLETED, STATUS_FAILED, STATUS_PENDING
)

class WalletService:
    @staticmethod
    def get_or_create_wallet(user, currency='USD'):
        wallet, created = Wallet.objects.get_or_create(
            user=user,
            currency=currency,
            defaults={'is_primary': currency == 'USD'}
        )
        return wallet
    
    @staticmethod
    def get_user_wallets(user):
        return Wallet.objects.filter(user=user, is_active=True)
    
    @staticmethod
    def get_wallet_balance(wallet):
        return {
            'balance': wallet.balance,
            'available_balance': wallet.available_balance,
            'currency': wallet.currency
        }

class TransactionService:
    @staticmethod
    def generate_reference():
        return f"TXN-{uuid.uuid4().hex[:12].upper()}"
    
    @staticmethod
    def calculate_fee(transaction_type, amount):
        try:
            fee_config = FeeConfiguration.objects.get(
                transaction_type=transaction_type,
                is_active=True
            )
            return fee_config.calculate_fee(amount)
        except FeeConfiguration.DoesNotExist:
            return Decimal('0.00')
    
    @staticmethod
    @transaction.atomic
    def create_transaction(wallet, transaction_type, amount, **kwargs):
        fee = kwargs.get('fee', Decimal('0.00'))
        balance_before = wallet.balance
        if transaction_type in [TRANSACTION_DEPOSIT, 'LOAN_DISBURSEMENT', 'INTEREST_CREDIT']:
            balance_after = balance_before + amount
        elif transaction_type in [TRANSACTION_WITHDRAWAL, TRANSACTION_TRANSFER, 'LOAN_REPAYMENT', 'SAVINGS_DEPOSIT']:
            balance_after = balance_before - (amount + fee)
        else:
            balance_after = balance_before
        txn = Transaction.objects.create(
            wallet=wallet,
            transaction_type=transaction_type,
            amount=amount,
            fee=fee,
            currency=wallet.currency,
            balance_before=balance_before,
            balance_after=balance_after,
            reference=kwargs.get('reference', TransactionService.generate_reference()),
            description=kwargs.get('description', ''),
            recipient_wallet=kwargs.get('recipient_wallet'),
            recipient_email=kwargs.get('recipient_email'),
            status=kwargs.get('status', STATUS_PENDING),
            metadata=kwargs.get('metadata', {})
        )
        return txn
    
    @staticmethod
    @transaction.atomic
    def deposit(wallet, amount, description=''):
        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero")
        txn = TransactionService.create_transaction(
            wallet=wallet,
            transaction_type=TRANSACTION_DEPOSIT,
            amount=amount,
            description=description,
            status=STATUS_COMPLETED
        )
        wallet.balance += amount
        wallet.available_balance += amount
        wallet.save()
        NotificationService.send_transaction_notification(
            user=wallet.user,
            transaction=txn,
            notification_type='DEPOSIT'
        )
        return txn
    
    @staticmethod
    @transaction.atomic
    def withdraw(wallet, amount, pin, description=''):
        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero")
        if not wallet.user.check_pin(pin):
            raise ValueError("Invalid PIN")
        fee = TransactionService.calculate_fee(TRANSACTION_WITHDRAWAL, amount)
        total_deduction = amount + fee
        if wallet.available_balance < total_deduction:
            raise ValueError("Insufficient balance")
        txn = TransactionService.create_transaction(
            wallet=wallet,
            transaction_type=TRANSACTION_WITHDRAWAL,
            amount=amount,
            fee=fee,
            description=description,
            status=STATUS_COMPLETED
        )
        wallet.balance -= total_deduction
        wallet.available_balance -= total_deduction
        wallet.save()
        NotificationService.send_transaction_notification(
            user=wallet.user,
            transaction=txn,
            notification_type='WITHDRAWAL'
        )
        return txn
    
    @staticmethod
    @transaction.atomic
    def transfer(sender_wallet, recipient_email, amount, pin, description=''):
        if amount <= 0:
            raise ValueError("Transfer amount must be greater than zero")
        if not sender_wallet.user.check_pin(pin):
            raise ValueError("Invalid PIN")
        try:
            recipient_user = User.objects.get(email=recipient_email)
        except User.DoesNotExist:
            raise ValueError("Recipient not found")
        if sender_wallet.user == recipient_user:
            raise ValueError("Cannot transfer to yourself")
        recipient_wallet = WalletService.get_or_create_wallet(
            user=recipient_user,
            currency=sender_wallet.currency
        )
        fee = TransactionService.calculate_fee(TRANSACTION_TRANSFER, amount)
        total_deduction = amount + fee
        if sender_wallet.available_balance < total_deduction:
            raise ValueError("Insufficient balance")
        TransferLimitService.check_and_update_limits(sender_wallet.user, amount)
        sender_txn = TransactionService.create_transaction(
            wallet=sender_wallet,
            transaction_type=TRANSACTION_TRANSFER,
            amount=amount,
            fee=fee,
            description=description or f"Transfer to {recipient_email}",
            recipient_wallet=recipient_wallet,
            recipient_email=recipient_email,
            status=STATUS_COMPLETED
        )
        sender_wallet.balance -= total_deduction
        sender_wallet.available_balance -= total_deduction
        sender_wallet.save()
        recipient_txn = TransactionService.create_transaction(
            wallet=recipient_wallet,
            transaction_type=TRANSACTION_DEPOSIT,
            amount=amount,
            description=description or f"Transfer from {sender_wallet.user.email}",
            recipient_email=sender_wallet.user.email,
            status=STATUS_COMPLETED
        )
        recipient_wallet.balance += amount
        recipient_wallet.available_balance += amount
        recipient_wallet.save()
        NotificationService.send_transaction_notification(
            user=sender_wallet.user,
            transaction=sender_txn,
            notification_type='TRANSFER'
        )
        NotificationService.send_transaction_notification(
            user=recipient_user,
            transaction=recipient_txn,
            notification_type='DEPOSIT'
        )
        return sender_txn

class TransferLimitService:
    @staticmethod
    def get_or_create_limit(user):
        limit, created = TransferLimit.objects.get_or_create(
            user=user,
            defaults={
                'daily_limit': user.daily_transfer_limit,
                'monthly_limit': user.monthly_transfer_limit
            }
        )
        if limit.last_reset_date < timezone.now().date():
            limit.daily_used = Decimal('0.00')
            limit.last_reset_date = timezone.now().date()
            limit.save()
        if timezone.now().day == 1 and limit.monthly_used > 0:
            limit.monthly_used = Decimal('0.00')
            limit.save()
        return limit
    
    @staticmethod
    @transaction.atomic
    def check_and_update_limits(user, amount):
        limit = TransferLimitService.get_or_create_limit(user)
        if limit.daily_used + amount > limit.daily_limit:
            raise ValueError(f"Daily transfer limit exceeded. Remaining: {limit.daily_limit - limit.daily_used}")
        if limit.monthly_used + amount > limit.monthly_limit:
            raise ValueError(f"Monthly transfer limit exceeded. Remaining: {limit.monthly_limit - limit.monthly_used}")
        limit.daily_used += amount
        limit.monthly_used += amount
        limit.save()
        return limit
