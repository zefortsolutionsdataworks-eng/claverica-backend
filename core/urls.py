from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'core'

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/update/', views.UpdateProfileView.as_view(), name='update_profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('set-pin/', views.SetPinView.as_view(), name='set_pin'),
    path('verify-pin/', views.VerifyPinView.as_view(), name='verify_pin'),
    
    # KYC
    path('kyc/upload/', views.UploadKYCDocumentView.as_view(), name='kyc_upload'),
    path('kyc/status/', views.KYCStatusView.as_view(), name='kyc_status'),
    path('kyc/documents/', views.KYCDocumentListView.as_view(), name='kyc_documents'),
    
    # User Activity
    path('activity/', views.UserActivityListView.as_view(), name='user_activity'),
]
