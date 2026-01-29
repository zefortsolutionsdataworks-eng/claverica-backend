from rest_framework import serializers
from .models import Notification, EmailLog

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message', 'is_read', 
                  'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']

class EmailLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = EmailLog
        fields = ['id', 'user', 'user_email', 'recipient_email', 'subject', 'body',
                  'status', 'error_message', 'sent_at', 'created_at']
        read_only_fields = ['id', 'status', 'error_message', 'sent_at', 'created_at']
