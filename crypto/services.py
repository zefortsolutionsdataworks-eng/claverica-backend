from django.db import transaction
from decimal import Decimal
import uuid
from .models import CryptoCurrency, CryptoWallet, CryptoTransaction
from wallet.services import TransactionService, WalletService
from notifications.services import NotificationService
from common.constants import STATUS_COMPLETED
import random

class CryptoService:
    @staticmethod
    def generate_reference():
        return f"CRYPTO-{uuid.uuid4().hex[:12].upper()}"
