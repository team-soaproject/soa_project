from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'equipment', views.EquipmentViewSet, basename='equipment')
router.register(r'technicians', views.TechnicianViewSet, basename='technician')
router.register(r'maintenance-requests', views.MaintenanceRequestViewSet, basename='maintenance-request')
router.register(r'repair-logs', views.RepairLogViewSet, basename='repair-log')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', views.register, name='register'),
]