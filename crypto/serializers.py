from rest_framework import serializers
from .models import CryptoCurrency, CryptoWallet, CryptoTransaction
from decimal import Decimal

class CryptoCurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoCurrency
        fields = ['id', 'symbol', 'name', 'current_price_usd', 'market_cap', 'volume_24h',
                  'percent_change_24h', 'is_active', 'icon_url', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class CryptoWalletSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    current_price = serializers.DecimalField(source='currency.current_price_usd', 
                                            max_digits=20, decimal_places=8, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    current_value = serializers.SerializerMethodField()
    profit_loss = serializers.SerializerMethodField()
    profit_loss_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = CryptoWallet
        fields = ['id', 'user', 'user_email', 'currency', 'currency_symbol', 'currency_name',
                  'balance', 'current_price', 'total_invested_usd', 'average_buy_price',
                  'current_value', 'profit_loss', 'profit_loss_percentage', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'balance', 'total_invested_usd', 'average_buy_price',
                           'created_at', 'updated_at']
    
    def get_current_value(self, obj):
        return float(obj.current_value_usd())
    
    def get_profit_loss(self, obj):
        return float(obj.profit_loss_usd())
    
    def get_profit_loss_percentage(self, obj):
        if obj.total_invested_usd > 0:
            return float((obj.profit_loss_usd() / obj.total_invested_usd) * 100)
        return 0.0

class CryptoTransactionSerializer(serializers.ModelSerializer):
    currency_symbol = serializers.CharField(source='wallet.currency.symbol', read_only=True)
    user_email = serializers.EmailField(source='wallet.user.email', read_only=True)
    
    class Meta:
        model = CryptoTransaction
        fields = ['id', 'wallet', 'user_email', 'currency_symbol', 'transaction_type',
                  'crypto_amount', 'usd_amount', 'price_per_unit', 'fee', 'balance_before',
                  'balance_after', 'reference', 'status', 'created_at']
        read_only_fields = ['id', 'balance_before', 'balance_after', 'reference', 
                           'status', 'created_at']

class BuyCryptoSerializer(serializers.Serializer):
    currency_id = serializers.UUIDField(required=True)
    usd_amount = serializers.DecimalField(max_digits=15, decimal_places=2, required=True)
    pin = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4)
    
    def validate_usd_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")

class SellCryptoSerializer(serializers.Serializer):
    wallet_id = serializers.UUIDField(required=True)
    crypto_amount = serializers.DecimalField(max_digits=20, decimal_places=8, required=True)
    pin = serializers.CharField(write_only=True, required=True, min_length=4, max_length=4)
    
    def validate_crypto_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
