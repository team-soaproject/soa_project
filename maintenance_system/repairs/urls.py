# repairs/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views
from .serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# Custom Token View ที่ใช้ CustomTokenObtainPairSerializer
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Router สำหรับ ViewSets
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'equipment', views.EquipmentViewSet, basename='equipment')
router.register(r'technicians', views.TechnicianViewSet, basename='technician')
router.register(r'maintenance-requests', views.MaintenanceRequestViewSet, basename='maintenance-request')
router.register(r'repair-logs', views.RepairLogViewSet, basename='repair-log')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Authentication URLs
    path('auth/register/', views.register, name='register'),
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]