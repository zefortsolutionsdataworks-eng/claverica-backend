from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import SavingsProduct, SavingsAccount, SavingsTransaction
from .serializers import (
    SavingsProductSerializer, SavingsAccountSerializer,
    CreateSavingsAccountSerializer, SavingsTransactionSerializer,
    DepositToSavingsSerializer, WithdrawFromSavingsSerializer
)
from .services import SavingsService
from wallet.models import Wallet

class SavingsProductListView(generics.ListAPIView):
    """List all savings products"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavingsProductSerializer
    queryset = SavingsProduct.objects.filter(is_active=True)

class SavingsProductDetailView(generics.RetrieveAPIView):
    """Get savings product details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavingsProductSerializer
    queryset = SavingsProduct.objects.filter(is_active=True)

class SavingsAccountListView(generics.ListAPIView):
    """List user's savings accounts"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavingsAccountSerializer
    
    def get_queryset(self):
        return SavingsAccount.objects.filter(user=self.request.user)

class SavingsAccountDetailView(generics.RetrieveAPIView):
    """Get savings account details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavingsAccountSerializer
    
    def get_queryset(self):
        return SavingsAccount.objects.filter(user=self.request.user)

class CreateSavingsAccountView(APIView):
    """Create a new savings account"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = CreateSavingsAccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            product = SavingsProduct.objects.get(
                id=serializer.validated_data['product_id'],
                is_active=True
            )
            wallet = Wallet.objects.get(
                id=serializer.validated_data['wallet_id'],
                user=request.user,
                is_active=True
            )
            account = SavingsService.create_savings_account(
                user=request.user,
                wallet=wallet,
                product=product,
                initial_deposit=serializer.validated_data['initial_deposit'],
                pin=serializer.validated_data['pin']
            )
            return Response({
                'message': 'Savings account created successfully',
                'account': SavingsAccountSerializer(account).data
            }, status=status.HTTP_201_CREATED)
        except (SavingsProduct.DoesNotExist, Wallet.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CloseSavingsAccountView(APIView):
    """Close a savings account"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            account = SavingsAccount.objects.get(id=pk, user=request.user)
            if account.status == 'CLOSED':
                return Response({'error': 'Account already closed'}, status=status.HTTP_400_BAD_REQUEST)
            if account.balance > 0:
                pin = request.data.get('pin')
                if not pin:
                    return Response({'error': 'PIN required'}, status=status.HTTP_400_BAD_REQUEST)
                SavingsService.withdraw_from_savings(account, account.balance, pin)
            account.status = 'CLOSED'
            account.save()
            return Response({
                'message': 'Savings account closed successfully',
                'account': SavingsAccountSerializer(account).data
            })
        except SavingsAccount.DoesNotExist:
            return Response({'error': 'Savings account not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DepositToSavingsView(APIView):
    """Deposit to savings account"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = DepositToSavingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            account = SavingsAccount.objects.get(
                id=serializer.validated_data['savings_account_id'],
                user=request.user
            )
            transaction = SavingsService.deposit_to_savings(
                savings_account=account,
                amount=serializer.validated_data['amount'],
                pin=serializer.validated_data['pin']
            )
            return Response({
                'message': 'Deposit successful',
                'transaction': SavingsTransactionSerializer(transaction).data,
                'account': SavingsAccountSerializer(account).data
            }, status=status.HTTP_201_CREATED)
        except SavingsAccount.DoesNotExist:
            return Response({'error': 'Savings account not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class WithdrawFromSavingsView(APIView):
    """Withdraw from savings account"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = WithdrawFromSavingsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            account = SavingsAccount.objects.get(
                id=serializer.validated_data['savings_account_id'],
                user=request.user
            )
            transaction = SavingsService.withdraw_from_savings(
                savings_account=account,
                amount=serializer.validated_data['amount'],
                pin=serializer.validated_data['pin']
            )
            return Response({
                'message': 'Withdrawal successful',
                'transaction': SavingsTransactionSerializer(transaction).data,
                'account': SavingsAccountSerializer(account).data
            }, status=status.HTTP_201_CREATED)
        except SavingsAccount.DoesNotExist:
            return Response({'error': 'Savings account not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SavingsTransactionListView(generics.ListAPIView):
    """List savings transactions"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SavingsTransactionSerializer
    
    def get_queryset(self):
        return SavingsTransaction.objects.filter(
            savings_account__user=self.request.user
        ).order_by('-created_at')

class CalculateInterestView(APIView):
    """Calculate interest for all accounts (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        results = SavingsService.calculate_interest_for_all_accounts()
        return Response({
            'message': 'Interest calculation completed',
            'results': results,
            'total_processed': len(results)
        })
