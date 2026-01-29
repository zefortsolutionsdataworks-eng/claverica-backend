from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CryptoCurrency, CryptoWallet, CryptoTransaction
from .serializers import (
    CryptoCurrencySerializer, CryptoWalletSerializer,
    CryptoTransactionSerializer, BuyCryptoSerializer, SellCryptoSerializer
)
from .services import CryptoService

class CryptoCurrencyListView(generics.ListAPIView):
    """List all cryptocurrencies"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CryptoCurrencySerializer
    queryset = CryptoCurrency.objects.filter(is_active=True)

class CryptoCurrencyDetailView(generics.RetrieveAPIView):
    """Get cryptocurrency details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CryptoCurrencySerializer
    queryset = CryptoCurrency.objects.filter(is_active=True)

class UpdateCryptoPricesView(APIView):
    """Update crypto prices (Admin/System)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        currencies = CryptoService.update_mock_prices()
        serializer = CryptoCurrencySerializer(currencies, many=True)
        return Response({
            'message': 'Prices updated successfully',
            'currencies': serializer.data
        })

class CryptoWalletListView(generics.ListAPIView):
    """List user's crypto wallets"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CryptoWalletSerializer
    
    def get_queryset(self):
        return CryptoWallet.objects.filter(user=self.request.user, balance__gt=0)

class CryptoWalletDetailView(generics.RetrieveAPIView):
    """Get crypto wallet details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CryptoWalletSerializer
    
    def get_queryset(self):
        return CryptoWallet.objects.filter(user=self.request.user)

class CryptoPortfolioView(APIView):
    """Get user's crypto portfolio"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        wallets = CryptoWallet.objects.filter(user=request.user, balance__gt=0)
        total_invested = sum(w.total_invested_usd for w in wallets)
        total_value = sum(w.current_value_usd() for w in wallets)
        total_profit_loss = total_value - total_invested
        profit_loss_percentage = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
        return Response({
            'wallets': CryptoWalletSerializer(wallets, many=True).data,
            'summary': {
                'total_invested_usd': float(total_invested),
                'total_value_usd': float(total_value),
                'total_profit_loss_usd': float(total_profit_loss),
                'profit_loss_percentage': float(profit_loss_percentage)
            }
        })

class BuyCryptoView(APIView):
    """Buy cryptocurrency"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = BuyCryptoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            currency = CryptoCurrency.objects.get(
                id=serializer.validated_data['currency_id'],
                is_active=True
            )
            transaction = CryptoService.buy_crypto(
                user=request.user,
                currency=currency,
                usd_amount=serializer.validated_data['usd_amount'],
                pin=serializer.validated_data['pin']
            )
            return Response({
                'message': 'Purchase successful',
                'transaction': CryptoTransactionSerializer(transaction).data
            }, status=status.HTTP_201_CREATED)
        except CryptoCurrency.DoesNotExist:
            return Response({'error': 'Cryptocurrency not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SellCryptoView(APIView):
    """Sell cryptocurrency"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = SellCryptoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            crypto_wallet = CryptoWallet.objects.get(
                id=serializer.validated_data['wallet_id'],
                user=request.user
            )
            transaction = CryptoService.sell_crypto(
                user=request.user,
                crypto_wallet=crypto_wallet,
                crypto_amount=serializer.validated_data['crypto_amount'],
                pin=serializer.validated_data['pin']
            )
            return Response({
                'message': 'Sale successful',
                'transaction': CryptoTransactionSerializer(transaction).data
            }, status=status.HTTP_201_CREATED)
        except CryptoWallet.DoesNotExist:
            return Response({'error': 'Crypto wallet not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CryptoTransactionListView(generics.ListAPIView):
    """List crypto transactions"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CryptoTransactionSerializer
    
    def get_queryset(self):
        return CryptoTransaction.objects.filter(wallet__user=self.request.user).order_by('-created_at')

class CryptoTransactionDetailView(generics.RetrieveAPIView):
    """Get crypto transaction details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CryptoTransactionSerializer
    
    def get_queryset(self):
        return CryptoTransaction.objects.filter(wallet__user=self.request.user)
