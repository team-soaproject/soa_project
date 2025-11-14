from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import Equipment, Technician, MaintenanceRequest, RepairLog


# =====================================================
# Custom JWT Token Serializer
# =====================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT Serializer ที่ส่ง user data พร้อม token"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # กำหนด role อย่างชัดเจน
        if user.is_superuser:
            role = 'admin'
        elif user.is_staff:
            role = 'admin'
        elif hasattr(user, 'technician'):
            role = 'technician'
        else:
            role = 'user'
        
        # เพิ่มข้อมูล custom ลงใน token payload
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['role'] = role
        token['user_id'] = user.id
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # เพิ่มข้อมูล user ใน response
        user = self.user
        
        # กำหนด role อย่างชัดเจน
        if user.is_superuser:
            role = 'admin'
        elif user.is_staff:
            role = 'admin'
        elif hasattr(user, 'technician'):
            role = 'technician'
        else:
            role = 'user'
        
        # 🔍 Debug: แสดง role ที่กำหนดให้
        print(f"🎭 Login: {user.username} - Role: {role} (is_staff: {user.is_staff}, is_superuser: {user.is_superuser})")
        
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'full_name': user.get_full_name() or user.username,
            'role': role,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser
        }
        
        return data


# =====================================================
# User Serializers
# =====================================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer สำหรับ User พร้อมแสดงบทบาท"""
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    role_display = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'full_name', 'role', 'role_display', 'is_active', 'is_staff']
        read_only_fields = ['id']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
    
    def get_role(self, obj):
        """ส่งค่า role เป็นภาษาอังกฤษสำหรับใช้ใน logic"""
        if obj.is_superuser:
            return 'admin'
        elif obj.is_staff:
            return 'admin'
        elif hasattr(obj, 'technician'):
            return 'technician'
        else:
            return 'user'
    
    def get_role_display(self, obj):
        """ส่งค่า role เป็นภาษาไทยสำหรับแสดงผล"""
        if obj.is_superuser:
            return 'ผู้ดูแลระบบสูงสุด'
        elif obj.is_staff:
            return 'ผู้ดูแลระบบ'
        elif hasattr(obj, 'technician'):
            return 'ช่างซ่อม'
        else:
            return 'ผู้ใช้งาน'


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


# =====================================================
# Equipment Serializer
# =====================================================

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


# =====================================================
# Technician Serializer
# =====================================================

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


# =====================================================
# Maintenance Request Serializers
# =====================================================

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
    """Serializer สำหรับแจ้งซ่อม (เต็ม) - รองรับทั้ง equipment และ equipment_id"""
    requester = UserSerializer(read_only=True)
    equipment_detail = EquipmentSerializer(source='equipment', read_only=True)
    
    # ✅ รองรับทั้ง equipment_id และ equipment
    equipment_id = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        source='equipment',
        write_only=True,
        required=False  # ทำให้เป็น optional
    )
    equipment = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        write_only=True,
        required=False  # ทำให้เป็น optional
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
    
    def validate(self, data):
        """ตรวจสอบว่าต้องมี equipment_id หรือ equipment อย่างน้อย 1 อัน"""
        if 'equipment' not in data and 'equipment_id' not in self.initial_data:
            raise serializers.ValidationError({
                'equipment_id': 'กรุณาระบุอุปกรณ์'
            })
        return data
    
    def get_repair_logs(self, obj):
        logs = obj.repair_logs.all()
        return RepairLogSerializer(logs, many=True).data
    
    def create(self, validated_data):
        # กำหนด requester จาก user ที่ login
        validated_data['requester'] = self.context['request'].user
        return super().create(validated_data)


# =====================================================
# Repair Log Serializer
# =====================================================

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


# =====================================================
# Statistics Serializer
# =====================================================

class MaintenanceRequestStatsSerializer(serializers.Serializer):
    """Serializer สำหรับสถิติ"""
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    in_progress_requests = serializers.IntegerField()
    completed_requests = serializers.IntegerField()
    high_priority_requests = serializers.IntegerField()
    average_completion_time = serializers.FloatField()