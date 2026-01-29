from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import LoanProduct, Loan, LoanRepayment
from .serializers import (
    LoanProductSerializer, LoanSerializer, ApplyForLoanSerializer,
    LoanRepaymentSerializer, RepayLoanSerializer, ApproveLoanSerializer
)
from .services import LoanService
from wallet.models import Wallet

class LoanProductListView(generics.ListAPIView):
    """List all loan products"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanProductSerializer
    queryset = LoanProduct.objects.filter(is_active=True)

class LoanProductDetailView(generics.RetrieveAPIView):
    """Get loan product details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanProductSerializer
    queryset = LoanProduct.objects.filter(is_active=True)

class ApplyForLoanView(APIView):
    """Apply for a loan"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ApplyForLoanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            product = LoanProduct.objects.get(
                id=serializer.validated_data['product_id'],
                is_active=True
            )
            wallet = Wallet.objects.get(
                id=serializer.validated_data['wallet_id'],
                user=request.user,
                is_active=True
            )
            loan = LoanService.apply_for_loan(
                user=request.user,
                wallet=wallet,
                product=product,
                principal_amount=serializer.validated_data['principal_amount'],
                tenure_days=serializer.validated_data['tenure_days']
            )
            return Response({
                'message': 'Loan application submitted successfully',
                'loan': LoanSerializer(loan).data
            }, status=status.HTTP_201_CREATED)
        except (LoanProduct.DoesNotExist, Wallet.DoesNotExist) as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoanListView(generics.ListAPIView):
    """List user's loans"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanSerializer
    
    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user).order_by('-created_at')

class LoanDetailView(generics.RetrieveAPIView):
    """Get loan details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanSerializer
    
    def get_queryset(self):
        return Loan.objects.filter(user=self.request.user)

class ApproveLoanView(APIView):
    """Approve a loan (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        try:
            loan = Loan.objects.get(id=pk)
            if loan.status != 'PENDING':
                return Response({'error': 'Only pending loans can be approved'}, status=status.HTTP_400_BAD_REQUEST)
            loan = LoanService.approve_loan(loan)
            return Response({
                'message': 'Loan approved and disbursed',
                'loan': LoanSerializer(loan).data
            })
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RejectLoanView(APIView):
    """Reject a loan (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        serializer = ApproveLoanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            loan = Loan.objects.get(id=pk)
            rejection_reason = serializer.validated_data.get('rejection_reason', 'Not specified')
            loan = LoanService.reject_loan(loan, rejection_reason)
            return Response({
                'message': 'Loan rejected',
                'loan': LoanSerializer(loan).data
            })
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DisburseLoanView(APIView):
    """Disburse approved loan (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        try:
            loan = Loan.objects.get(id=pk)
            loan = LoanService.disburse_loan(loan)
            return Response({
                'message': 'Loan disbursed successfully',
                'loan': LoanSerializer(loan).data
            })
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RepayLoanView(APIView):
    """Repay a loan"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = RepayLoanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            loan = Loan.objects.get(
                id=serializer.validated_data['loan_id'],
                user=request.user
            )
            repayment = LoanService.repay_loan(
                loan=loan,
                amount=serializer.validated_data['amount'],
                pin=serializer.validated_data['pin']
            )
            return Response({
                'message': 'Repayment successful',
                'repayment': LoanRepaymentSerializer(repayment).data,
                'loan': LoanSerializer(loan).data
            }, status=status.HTTP_201_CREATED)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoanRepaymentListView(generics.ListAPIView):
    """List loan repayments"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LoanRepaymentSerializer
    
    def get_queryset(self):
        loan_id = self.kwargs.get('pk')
        return LoanRepayment.objects.filter(
            loan_id=loan_id,
            loan__user=self.request.user
        ).order_by('-created_at')

class CreditScoreView(APIView):
    """Get user's credit score"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        score = LoanService.calculate_credit_score(request.user)
        if score >= 750:
            category = 'Excellent'
        elif score >= 650:
            category = 'Good'
        elif score >= 550:
            category = 'Fair'
        else:
            category = 'Poor'
        return Response({
            'credit_score': score,
            'category': category,
            'max_loan_amount': request.user.monthly_transfer_limit
        })
