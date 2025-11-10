from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.models import User
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import Equipment, Technician, MaintenanceRequest, RepairLog
from .serializers import (
    UserSerializer, UserRegistrationSerializer,
    EquipmentSerializer, TechnicianSerializer,
    MaintenanceRequestSerializer, MaintenanceRequestListSerializer,
    RepairLogSerializer, MaintenanceRequestStatsSerializer
)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """API สำหรับลงทะเบียนผู้ใช้ใหม่"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'ลงทะเบียนสำเร็จ',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EquipmentViewSet(viewsets.ModelViewSet):
    """ViewSet สำหรับจัดการอุปกรณ์"""
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['equipment_code', 'name', 'department', 'location']
    ordering_fields = ['created_at', 'name', 'department']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by department
        department = self.request.query_params.get('department', None)
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def maintenance_history(self, request, pk=None):
        """ดูประวัติการซ่อมของอุปกรณ์"""
        equipment = self.get_object()
        requests = equipment.maintenance_requests.all()
        serializer = MaintenanceRequestListSerializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """สถิติอุปกรณ์"""
        total = Equipment.objects.count()
        active = Equipment.objects.filter(status='ACTIVE').count()
        under_repair = Equipment.objects.filter(status='UNDER_REPAIR').count()
        out_of_service = Equipment.objects.filter(status='OUT_OF_SERVICE').count()
        
        return Response({
            'total_equipment': total,
            'active': active,
            'under_repair': under_repair,
            'out_of_service': out_of_service
        })


class TechnicianViewSet(viewsets.ModelViewSet):
    """ViewSet สำหรับจัดการช่างซ่อม"""
    queryset = Technician.objects.all()
    serializer_class = TechnicianSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'employee_id']
    ordering_fields = ['created_at', 'user__first_name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by availability
        is_available = self.request.query_params.get('is_available', None)
        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')
        
        # Filter by expertise
        expertise = self.request.query_params.get('expertise', None)
        if expertise:
            queryset = queryset.filter(expertise=expertise)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def assigned_jobs(self, request, pk=None):
        """ดูงานที่มอบหมายให้ช่าง"""
        technician = self.get_object()
        requests = technician.assigned_requests.filter(
            status__in=['PENDING', 'IN_PROGRESS']
        )
        serializer = MaintenanceRequestListSerializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def work_history(self, request, pk=None):
        """ประวัติการทำงานของช่าง"""
        technician = self.get_object()
        logs = technician.repair_logs.all()
        serializer = RepairLogSerializer(logs, many=True)
        return Response(serializer.data)


class MaintenanceRequestViewSet(viewsets.ModelViewSet):
    """ViewSet สำหรับจัดการรายการแจ้งซ่อม"""
    queryset = MaintenanceRequest.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['request_code', 'problem_description', 'equipment__name']
    ordering_fields = ['created_at', 'priority', 'status']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return MaintenanceRequestListSerializer
        return MaintenanceRequestSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Filter by user's own requests
        my_requests = self.request.query_params.get('my_requests', None)
        if my_requests == 'true':
            queryset = queryset.filter(requester=user)
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by assigned technician
        technician_id = self.request.query_params.get('technician', None)
        if technician_id:
            queryset = queryset.filter(assigned_technician_id=technician_id)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def assign_technician(self, request, pk=None):
        """มอบหมายงานให้ช่าง"""
        maintenance_request = self.get_object()
        technician_id = request.data.get('technician_id')
        
        try:
            technician = Technician.objects.get(id=technician_id)
            maintenance_request.assigned_technician = technician
            maintenance_request.status = 'IN_PROGRESS'
            maintenance_request.save()
            
            serializer = self.get_serializer(maintenance_request)
            return Response({
                'message': 'มอบหมายงานสำเร็จ',
                'data': serializer.data
            })
        except Technician.DoesNotExist:
            return Response(
                {'error': 'ไม่พบช่างซ่อม'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """อัพเดทสถานะงานซ่อม"""
        maintenance_request = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(MaintenanceRequest.STATUS_CHOICES):
            return Response(
                {'error': 'สถานะไม่ถูกต้อง'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        maintenance_request.status = new_status
        if new_status == 'COMPLETED':
            maintenance_request.completed_at = timezone.now()
        maintenance_request.save()
        
        serializer = self.get_serializer(maintenance_request)
        return Response({
            'message': 'อัพเดทสถานะสำเร็จ',
            'data': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """สถิติการแจ้งซ่อม"""
        total = MaintenanceRequest.objects.count()
        pending = MaintenanceRequest.objects.filter(status='PENDING').count()
        in_progress = MaintenanceRequest.objects.filter(status='IN_PROGRESS').count()
        completed = MaintenanceRequest.objects.filter(status='COMPLETED').count()
        high_priority = MaintenanceRequest.objects.filter(priority='HIGH').count()
        
        # คำนวณเวลาเฉลี่ยในการซ่อม (ชั่วโมง)
        completed_requests = MaintenanceRequest.objects.filter(
            status='COMPLETED',
            completed_at__isnull=False
        )
        
        avg_time = 0
        if completed_requests.exists():
            total_time = sum([
                (req.completed_at - req.created_at).total_seconds() / 3600
                for req in completed_requests
            ])
            avg_time = round(total_time / completed_requests.count(), 2)
        
        data = {
            'total_requests': total,
            'pending_requests': pending,
            'in_progress_requests': in_progress,
            'completed_requests': completed,
            'high_priority_requests': high_priority,
            'average_completion_time': avg_time
        }
        
        serializer = MaintenanceRequestStatsSerializer(data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """รายการแจ้งซ่อมด่วน"""
        urgent_requests = self.get_queryset().filter(
            priority__in=['MEDIUM', 'HIGH'],
            status__in=['PENDING', 'IN_PROGRESS']
        )
        serializer = MaintenanceRequestListSerializer(urgent_requests, many=True)
        return Response(serializer.data)


class RepairLogViewSet(viewsets.ModelViewSet):
    """ViewSet สำหรับจัดการบันทึกการซ่อม"""
    queryset = RepairLog.objects.all()
    serializer_class = RepairLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['maintenance_request__request_code', 'description']
    ordering_fields = ['created_at', 'started_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by maintenance request
        request_id = self.request.query_params.get('maintenance_request', None)
        if request_id:
            queryset = queryset.filter(maintenance_request_id=request_id)
        
        # Filter by technician
        technician_id = self.request.query_params.get('technician', None)
        if technician_id:
            queryset = queryset.filter(technician_id=technician_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """สรุปข้อมูลการซ่อม"""
        total_logs = RepairLog.objects.count()
        total_hours = RepairLog.objects.aggregate(
            total=Avg('labor_hours')
        )['total'] or 0
        total_cost = RepairLog.objects.aggregate(
            total=Avg('cost')
        )['total'] or 0
        
        return Response({
            'total_repair_logs': total_logs,
            'average_labor_hours': round(total_hours, 2),
            'average_cost': round(total_cost, 2)
        })
# Create your views here.
