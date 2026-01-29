from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, KYCDocument, UserActivity

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'kyc_level', 'is_active', 'created_at']
    list_filter = ['kyc_level', 'is_active', 'email_verified', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'date_of_birth', 'country')}),
        ('Verification', {'fields': ('kyc_level', 'email_verified', 'phone_verified')}),
        ('Limits', {'fields': ('daily_transfer_limit', 'monthly_transfer_limit')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Security', {'fields': ('two_factor_enabled',)}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'status', 'created_at', 'reviewed_at']
    list_filter = ['status', 'document_type', 'created_at']
    search_fields = ['user__email', 'document_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Document Info', {'fields': ('user', 'document_type', 'document_number', 'document_file')}),
        ('Review', {'fields': ('status', 'rejection_reason', 'reviewed_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at')}),
    )

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'ip_address', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False