from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from common.models import TimeStampedModel
from common.constants import (
    TRANSACTION_CRYPTO_BUY,
    TRANSACTION_CRYPTO_SELL,
    TRANSACTION_STATUS_CHOICES,
    TRANSACTION_COMPLETED
)


class CryptoCurrency(TimeStampedModel):
    """Supported cryptocurrencies"""
    symbol = models.CharField(max_length=10, unique=True, help_text="e.g., BTC, ETH")
    name = models.CharField(max_length=100, help_text="e.g., Bitcoin, Ethereum")
    icon_url = models.URLField(blank=True)
    current_price_usd = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        validators=[MinValueValidator(Decimal('0.00000001'))]
    )
    market_cap = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True
    )
    volume_24h = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        null=True,
        blank=True
    )
    percent_change_24h = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'crypto_currencies'
        ordering = ['symbol']
        verbose_name_plural = 'Crypto Currencies'

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class CryptoWallet(TimeStampedModel):
    """User cryptocurrency wallets"""
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='crypto_wallets')
    currency = models.ForeignKey(CryptoCurrency, on_delete=models.PROTECT, related_name='wallets')
    balance = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.00000000'),
        validators=[MinValueValidator(Decimal('0.00000000'))]
    )
    total_invested_usd = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal('0.00')
    )
    average_buy_price = models.DecimalField(
        max_digits=20,
        decimal_places=8,
        default=Decimal('0.00000000')
    )

    class Meta:
        db_table = 'crypto_wallets'
        unique_together = ['user', 'currency']
        ordering = ['-balance']

    def __str__(self):
        return f"{self.user.email} - {self.currency.symbol}: {self.balance}"


class CryptoTransaction(TimeStampedModel):
    """Cryptocurrency buy/sell transactions"""
    TRANSACTION_TYPE_CHOICES = [
        (TRANSACTION_CRYPTO_BUY, 'Buy'),
        (TRANSACTION_CRYPTO_SELL, 'Sell'),
    ]

    wallet = models.ForeignKey(CryptoWallet, on_delete=models.CASCADE, related_name='transactions')
    fiat_wallet = models.ForeignKey('wallet.Wallet', on_delete=models.CASCADE, related_name='crypto_transactions')
    reference = models.CharField(max_length=100, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    
    # Crypto amounts
    crypto_amount = models.DecimalField(max_digits=20, decimal_places=8)
    price_per_unit = models.DecimalField(max_digits=20, decimal_places=8)
    
    # USD/Fiat amounts
    usd_amount = models.DecimalField(max_digits=20, decimal_places=2)
    fee = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    total_usd = models.DecimalField(max_digits=20, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default=TRANSACTION_COMPLETED)
    
    # Balances after transaction
    crypto_balance_after = models.DecimalField(max_digits=20, decimal_places=8)
    fiat_balance_after = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'crypto_transactions'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} {self.crypto_amount} {self.wallet.currency.symbol} @ "
