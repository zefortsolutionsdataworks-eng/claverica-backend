from django.contrib import admin
from .models import Wallet, Transaction, TransferLimit, FeeConfiguration

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'currency', 'balance', 'available_balance', 'is_active', 'is_primary']
    list_filter = ['currency', 'is_active', 'is_primary', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Wallet Info', {'fields': ('user', 'currency', 'is_primary', 'is_active')}),
        ('Balances', {'fields': ('balance', 'available_balance')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['reference', 'wallet', 'transaction_type', 'amount', 'fee', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'currency', 'created_at']
    search_fields = ['reference', 'wallet__user__email', 'description']
    readonly_fields = ['created_at', 'updated_at', 'reference']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Transaction Info', {'fields': ('reference', 'wallet', 'transaction_type', 'status')}),
        ('Amounts', {'fields': ('amount', 'fee', 'currency')}),
        ('Balances', {'fields': ('balance_before', 'balance_after')}),
        ('Transfer Details', {'fields': ('recipient_wallet', 'recipient_email', 'description')}),
        ('Metadata', {'fields': ('metadata',)}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    
    def has_add_permission(self, request):
        return False

@admin.register(TransferLimit)
class TransferLimitAdmin(admin.ModelAdmin):
    list_display = ['user', 'daily_limit', 'daily_used', 'monthly_limit', 'monthly_used', 'last_reset_date']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(FeeConfiguration)
class FeeConfigurationAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'fee_type', 'fixed_amount', 'percentage', 'is_active']
    list_filter = ['fee_type', 'is_active', 'transaction_type']
    
    fieldsets = (
        ('Configuration', {'fields': ('transaction_type', 'fee_type', 'is_active')}),
        ('Fee Structure', {'fields': ('fixed_amount', 'percentage', 'minimum_fee', 'maximum_fee')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )
    readonly_fields = ['created_at', 'updated_at']