from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from common.models import TimeStampedModel
from common.constants import (
    KYC_LEVEL_CHOICES, KYC_LEVEL_0,
    KYC_DOCUMENT_TYPE_CHOICES, KYC_STATUS_CHOICES,
    ACTIVITY_TYPE_CHOICES
)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    kyc_level = models.CharField(max_length=20, choices=KYC_LEVEL_CHOICES, default=KYC_LEVEL_0)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    pin_hash = models.CharField(max_length=255, blank=True)
    two_factor_enabled = models.BooleanField(default=False)
    
    daily_transfer_limit = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    monthly_transfer_limit = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name
    
    def set_pin(self, pin):
        from django.contrib.auth.hashers import make_password
        self.pin_hash = make_password(pin)
        self.save()
    
    def check_pin(self, pin):
        from django.contrib.auth.hashers import check_password
        return check_password(pin, self.pin_hash)


class KYCDocument(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(max_length=50, choices=KYC_DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=100)
    document_file = models.FileField(upload_to='kyc_documents/')
    status = models.CharField(max_length=20, choices=KYC_STATUS_CHOICES, default='PENDING')
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'kyc_documents'
    
    def __str__(self):
        return f"{self.user.email} - {self.document_type}"


class UserActivity(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'user_activities'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity_type}"


