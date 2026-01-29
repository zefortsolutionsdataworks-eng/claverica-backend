from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="ClaveRica API",
        default_version='v1',
        description="Banking for the Digital Age",
        terms_of_service="https://www.claverica.com/terms/",
        contact=openapi.Contact(email="contact@claverica.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # API Endpoints
    path('api/auth/', include('core.urls')),
    path('api/wallet/', include('wallet.urls')),
    path('api/savings/', include('savings.urls')),
    path('api/loans/', include('loans.urls')),
    path('api/crypto/', include('crypto.urls')),
    path('api/notifications/', include('notifications.urls')),
]
