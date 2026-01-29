from django.db import models
from common.models import TimeStampedModel
from core.models import User

class Notification(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=[
        ('TRANSFER', 'Transfer'),
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('LOAN_APPROVED', 'Loan Approved'),
        ('LOAN_DISBURSED', 'Loan Disbursed'),
        ('SAVINGS_INTEREST', 'Savings Interest'),
        ('KYC_APPROVED', 'KYC Approved'),
        ('KYC_REJECTED', 'KYC Rejected'),
        ('SECURITY_ALERT', 'Security Alert'),
    ])
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(blank=True, null=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"

class EmailLog(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_logs', null=True, blank=True)
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ], default='PENDING')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'email_logs'
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'
    
    def __str__(self):
        return f"{self.recipient_email} - {self.subject} - {self.status}"