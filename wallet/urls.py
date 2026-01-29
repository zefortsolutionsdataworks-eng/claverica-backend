from django.urls import path
from . import views

app_name = 'wallet'

urlpatterns = [
    # Wallets
    path('', views.WalletListView.as_view(), name='wallet_list'),
    path('<uuid:pk>/', views.WalletDetailView.as_view(), name='wallet_detail'),
    path('create/', views.CreateWalletView.as_view(), name='create_wallet'),
    path('balance/', views.WalletBalanceView.as_view(), name='wallet_balance'),
    
    # Transactions
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/<uuid:pk>/', views.TransactionDetailView.as_view(), name='transaction_detail'),
    path('transactions/export/', views.ExportTransactionsView.as_view(), name='export_transactions'),
    
    # Transfers
    path('transfer/', views.TransferView.as_view(), name='transfer'),
    path('deposit/', views.DepositView.as_view(), name='deposit'),
    path('withdraw/', views.WithdrawView.as_view(), name='withdraw'),
    
    # Limits
    path('limits/', views.TransferLimitsView.as_view(), name='transfer_limits'),
    
    # Fees
    path('fees/', views.FeeConfigurationListView.as_view(), name='fee_list'),
    path('calculate-fee/', views.CalculateFeeView.as_view(), name='calculate_fee'),
]
