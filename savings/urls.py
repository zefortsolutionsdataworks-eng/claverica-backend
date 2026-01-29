from django.urls import path
from . import views

app_name = 'savings'

urlpatterns = [
    # Savings Products
    path('products/', views.SavingsProductListView.as_view(), name='product_list'),
    path('products/<uuid:pk>/', views.SavingsProductDetailView.as_view(), name='product_detail'),
    
    # Savings Accounts
    path('accounts/', views.SavingsAccountListView.as_view(), name='account_list'),
    path('accounts/<uuid:pk>/', views.SavingsAccountDetailView.as_view(), name='account_detail'),
    path('accounts/create/', views.CreateSavingsAccountView.as_view(), name='create_account'),
    path('accounts/<uuid:pk>/close/', views.CloseSavingsAccountView.as_view(), name='close_account'),
    
    # Transactions
    path('deposit/', views.DepositToSavingsView.as_view(), name='deposit'),
    path('withdraw/', views.WithdrawFromSavingsView.as_view(), name='withdraw'),
    path('transactions/', views.SavingsTransactionListView.as_view(), name='transaction_list'),
    
    # Interest Calculation (Admin/System)
    path('calculate-interest/', views.CalculateInterestView.as_view(), name='calculate_interest'),
]
