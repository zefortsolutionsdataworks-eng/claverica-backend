from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification, EmailLog
from .serializers import NotificationSerializer, EmailLogSerializer

class NotificationListView(generics.ListAPIView):
    """List user notifications"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

class NotificationDetailView(generics.RetrieveAPIView):
    """Get notification details"""
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class MarkNotificationReadView(APIView):
    """Mark notification as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(id=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({
                'message': 'Notification marked as read',
                'notification': NotificationSerializer(notification).data
            })
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

class MarkAllNotificationsReadView(APIView):
    """Mark all notifications as read"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        updated = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({
            'message': f'{updated} notifications marked as read',
            'count': updated
        })

class UnreadNotificationCountView(APIView):
    """Get unread notification count"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return Response({'unread_count': count})

class EmailLogListView(generics.ListAPIView):
    """List email logs (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    serializer_class = EmailLogSerializer
    queryset = EmailLog.objects.all().order_by('-created_at')
