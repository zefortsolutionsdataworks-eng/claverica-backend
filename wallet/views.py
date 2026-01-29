from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from .models import Wallet, Transaction, TransferLimit, FeeConfiguration
from .serializers import (
    WalletSerializer, TransactionSerializer, TransferSerializer,
    DepositSerializer, WithdrawSerializer, TransferLimitSerializer,
    FeeConfigurationSerializer, CalculateFeeSerializer
)
from .services import WalletService, TransactionService, TransferLimitService

class WalletListView(generics.ListAPIView):
    """List all user wallets"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletSerializer
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user, is_active=True)

class WalletDetailView(generics.RetrieveAPIView):
    """Get wallet details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletSerializer
    
    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

class CreateWalletView(APIView):
    """Create a new wallet"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        currency = request.data.get('currency', 'USD')
        if Wallet.objects.filter(user=request.user, currency=currency).exists():
            return Response(
                {'error': f'{currency} wallet already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        wallet = WalletService.get_or_create_wallet(request.user, currency)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class WalletBalanceView(APIView):
    """Get total balance across all wallets"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        wallets = Wallet.objects.filter(user=request.user, is_active=True)
        total_balance = {
            'wallets': WalletSerializer(wallets, many=True).data,
            'total_usd': sum(w.balance for w in wallets if w.currency == 'USD'),
        }
        return Response(total_balance)

class TransactionListView(generics.ListAPIView):
    """List user transactions"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(wallet__user=self.request.user)
        transaction_type = self.request.query_params.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        currency = self.request.query_params.get('currency')
        if currency:
            queryset = queryset.filter(currency=currency)
        return queryset.order_by('-created_at')

class TransactionDetailView(generics.RetrieveAPIView):
    """Get transaction details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TransactionSerializer
    
    def get_queryset(self):
        return Transaction.objects.filter(wallet__user=self.request.user)

class ExportTransactionsView(APIView):
    """Export transactions (returns JSON for now, can be enhanced to CSV/PDF)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        transactions = Transaction.objects.filter(wallet__user=request.user).order_by('-created_at')
        serializer = TransactionSerializer(transactions, many=True)
        return Response({
            'total_transactions': transactions.count(),
            'transactions': serializer.data
        })

class TransferView(APIView):
    """Transfer money to another user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = TransferSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:
            currency = serializer.validated_data.get('currency', 'USD')
            sender_wallet = WalletService.get_or_create_wallet(request.user, currency)
            transaction = TransactionService.transfer(
                sender_wallet=sender_wallet,
                recipient_email=serializer.validated_data['recipient_email'],
                amount=serializer.validated_data['amount'],
                pin=serializer.validated_data['pin'],
                description=serializer.validated_data.get('description', '')
            )
            return Response({
                'message': 'Transfer successful',
                'transaction': TransactionSerializer(transaction).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DepositView(APIView):
    """Deposit money into wallet (simulated)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            currency = serializer.validated_data.get('currency', 'USD')
            wallet = WalletService.get_or_create_wallet(request.user, currency)
            transaction = TransactionService.deposit(
                wallet=wallet,
                amount=serializer.validated_data['amount'],
                description=serializer.validated_data.get('description', 'Deposit')
            )
            return Response({
                'message': 'Deposit successful',
                'transaction': TransactionSerializer(transaction).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class WithdrawView(APIView):
    """Withdraw money from wallet"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = WithdrawSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            currency = serializer.validated_data.get('currency', 'USD')
            wallet = WalletService.get_or_create_wallet(request.user, currency)
            transaction = TransactionService.withdraw(
                wallet=wallet,
                amount=serializer.validated_data['amount'],
                pin=serializer.validated_data['pin'],
                description=serializer.validated_data.get('description', 'Withdrawal')
            )
            return Response({
                'message': 'Withdrawal successful',
                'transaction': TransactionSerializer(transaction).data
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TransferLimitsView(APIView):
    """Get user's transfer limits"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        limit = TransferLimitService.get_or_create_limit(request.user)
        serializer = TransferLimitSerializer(limit)
        return Response(serializer.data)

class FeeConfigurationListView(generics.ListAPIView):
    """List all fee configurations"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FeeConfigurationSerializer
    queryset = FeeConfiguration.objects.filter(is_active=True)

class CalculateFeeView(APIView):
    """Calculate fee for a transaction"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CalculateFeeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fee = TransactionService.calculate_fee(
            transaction_type=serializer.validated_data['transaction_type'],
            amount=serializer.validated_data['amount']
        )
        return Response({
            'transaction_type': serializer.validated_data['transaction_type'],
            'amount': serializer.validated_data['amount'],
            'fee': fee,
            'total': serializer.validated_data['amount'] + fee
        })
