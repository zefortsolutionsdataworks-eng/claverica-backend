from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notifications
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification_detail'),
    path('<uuid:pk>/mark-read/', views.MarkNotificationReadView.as_view(), name='mark_read'),
    path('mark-all-read/', views.MarkAllNotificationsReadView.as_view(), name='mark_all_read'),
    path('unread-count/', views.UnreadNotificationCountView.as_view(), name='unread_count'),
    
    # Email Logs (Admin)
    path('emails/', views.EmailLogListView.as_view(), name='email_list'),
]
