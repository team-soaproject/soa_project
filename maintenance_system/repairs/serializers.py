from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Equipment, Technician, MaintenanceRequest, RepairLog


class UserSerializer(serializers.ModelSerializer):
    """Serializer สำหรับ User"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer สำหรับการลงทะเบียน"""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 
                  'first_name', 'last_name']
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("รหัสผ่านไม่ตรงกัน")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class EquipmentSerializer(serializers.ModelSerializer):
    """Serializer สำหรับอุปกรณ์"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_maintenance_requests = serializers.SerializerMethodField()
    
    class Meta:
        model = Equipment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_maintenance_requests(self, obj):
        return obj.maintenance_requests.count()


class TechnicianSerializer(serializers.ModelSerializer):
    """Serializer สำหรับช่างซ่อม"""
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    expertise_display = serializers.CharField(source='get_expertise_display', read_only=True)
    active_jobs = serializers.SerializerMethodField()
    
    class Meta:
        model = Technician
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_active_jobs(self, obj):
        return obj.assigned_requests.filter(
            status__in=['PENDING', 'IN_PROGRESS']
        ).count()


class MaintenanceRequestListSerializer(serializers.ModelSerializer):
    """Serializer สำหรับแสดงรายการแจ้งซ่อม (ย่อ)"""
    requester = UserSerializer(read_only=True)
    equipment = EquipmentSerializer(read_only=True)
    assigned_technician = TechnicianSerializer(read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MaintenanceRequest
        fields = ['id', 'request_code', 'requester', 'equipment', 
                  'problem_description', 'priority', 'priority_display',
                  'status', 'status_display', 'assigned_technician',
                  'created_at', 'updated_at']


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    """Serializer สำหรับแจ้งซ่อม (เต็ม)"""
    requester = UserSerializer(read_only=True)
    equipment_detail = EquipmentSerializer(source='equipment', read_only=True)
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True
    )
    assigned_technician_detail = TechnicianSerializer(
        source='assigned_technician', 
        read_only=True
    )
    assigned_technician_id = serializers.PrimaryKeyRelatedField(
        queryset=Technician.objects.all(),
        source='assigned_technician',
        write_only=True,
        required=False,
        allow_null=True
    )
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    repair_logs = serializers.SerializerMethodField()
    
    class Meta:
        model = MaintenanceRequest
        fields = '__all__'
        read_only_fields = ['request_code', 'requester', 'created_at', 
                            'updated_at', 'completed_at']
    
    def get_repair_logs(self, obj):
        logs = obj.repair_logs.all()
        return RepairLogSerializer(logs, many=True).data
    
    def create(self, validated_data):
        # กำหนด requester จาก user ที่ login
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)


class RepairLogSerializer(serializers.ModelSerializer):
    """Serializer สำหรับบันทึกการซ่อม"""
    maintenance_request_detail = MaintenanceRequestListSerializer(
        source='maintenance_request', 
        read_only=True
    )
    maintenance_request_id = serializers.PrimaryKeyRelatedField(
        queryset=MaintenanceRequest.objects.all(),
        source='maintenance_request',
        write_only=True
    )
    technician_detail = TechnicianSerializer(source='technician', read_only=True)
    technician_id = serializers.PrimaryKeyRelatedField(
        queryset=Technician.objects.all(),
        source='technician',
        write_only=True
    )
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = RepairLog
        fields = '__all__'
        read_only_fields = ['created_at']
    
    def get_duration_hours(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return round(delta.total_seconds() / 3600, 2)
        return None


class MaintenanceRequestStatsSerializer(serializers.Serializer):
    """Serializer สำหรับสถิติ"""
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    in_progress_requests = serializers.IntegerField()
    completed_requests = serializers.IntegerField()
    high_priority_requests = serializers.IntegerField()
    average_completion_time = serializers.FloatField()