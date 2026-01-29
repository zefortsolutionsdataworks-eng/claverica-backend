from django.urls import path
from . import views

app_name = 'crypto'

urlpatterns = [
    # Cryptocurrencies
    path('currencies/', views.CryptoCurrencyListView.as_view(), name='currency_list'),
    path('currencies/<uuid:pk>/', views.CryptoCurrencyDetailView.as_view(), name='currency_detail'),
    path('currencies/update-prices/', views.UpdateCryptoPricesView.as_view(), name='update_prices'),
    
    # Crypto Wallets
    path('wallets/', views.CryptoWalletListView.as_view(), name='wallet_list'),
    path('wallets/<uuid:pk>/', views.CryptoWalletDetailView.as_view(), name='wallet_detail'),
    path('portfolio/', views.CryptoPortfolioView.as_view(), name='portfolio'),
    
    # Trading
    path('buy/', views.BuyCryptoView.as_view(), name='buy'),
    path('sell/', views.SellCryptoView.as_view(), name='sell'),
    path('transactions/', views.CryptoTransactionListView.as_view(), name='transaction_list'),
    path('transactions/<uuid:pk>/', views.CryptoTransactionDetailView.as_view(), name='transaction_detail'),
]
