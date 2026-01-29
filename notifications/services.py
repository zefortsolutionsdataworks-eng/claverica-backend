from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Notification, EmailLog

class NotificationService:
    @staticmethod
    def send_notification(user, notification_type, title, message, metadata=None):
        notification = Notification.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            metadata=metadata or {}
        )
        return notification
    
    @staticmethod
    def send_transaction_notification(user, transaction, notification_type):
        title_map = {'DEPOSIT': 'Money Received','WITHDRAWAL': 'Money Withdrawn','TRANSFER': 'Money Sent'}
        message_map = {'DEPOSIT': f'You received {transaction.amount} {transaction.currency}',
                       'WITHDRAWAL': f'You withdrew {transaction.amount} {transaction.currency}',
                       'TRANSFER': f'You sent {transaction.amount} {transaction.currency} to {transaction.recipient_email}'}
        return NotificationService.send_notification(
            user=user,
            notification_type=notification_type,
            title=title_map.get(notification_type, 'Transaction'),
            message=message_map.get(notification_type, 'Transaction completed'),
            metadata={'transaction_id': str(transaction.id)}
        )
