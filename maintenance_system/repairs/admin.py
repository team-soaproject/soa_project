from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Equipment, Technician, MaintenanceRequest, RepairLog


# ยกเลิกการลงทะเบียน User เดิม
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Custom User Admin พร้อมแสดงบทบาท"""
    
    list_display = ['username', 'email', 'get_role_display', 'first_name', 
                    'last_name', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    def get_role_display(self, obj):
        """แสดงบทบาทในรูปแบบภาษาไทย"""
        if obj.is_superuser:
            return '🔴 ผู้ดูแลระบบสูงสุด'
        elif obj.is_staff:
            return '🟡 ผู้ดูแลระบบ'
        elif hasattr(obj, 'technician'):
            return '🔧 ช่างซ่อม'
        else:
            return '👤 ผู้ใช้งาน'
    
    get_role_display.short_description = 'บทบาท'
    get_role_display.admin_order_field = 'is_staff'


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """Admin สำหรับอุปกรณ์"""
    list_display = ['equipment_code', 'name', 'department', 'location', 
                    'status', 'created_at']
    list_filter = ['status', 'department']
    search_fields = ['equipment_code', 'name', 'department', 'location']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('ข้อมูลทั่วไป', {
            'fields': ('equipment_code', 'name', 'description')
        }),
        ('รายละเอียด', {
            'fields': ('department', 'location', 'status')
        }),
        ('วันที่', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    """Admin สำหรับช่างซ่อม"""
    list_display = ['employee_id', 'get_user_name', 'expertise', 
                    'is_available', 'created_at']
    list_filter = ['expertise', 'is_available']
    search_fields = ['employee_id', 'user__username', 'user__first_name', 
                     'user__last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    
    get_user_name.short_description = 'ชื่อผู้ใช้'
    get_user_name.admin_order_field = 'user__username'


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    """Admin สำหรับการแจ้งซ่อม"""
    list_display = ['request_code', 'get_requester', 'get_equipment', 
                    'priority', 'status', 'get_technician', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['request_code', 'problem_description', 
                     'equipment__name', 'requester__username']
    ordering = ['-created_at']
    readonly_fields = ['request_code', 'created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('ข้อมูลคำขอ', {
            'fields': ('request_code', 'requester', 'equipment')
        }),
        ('รายละเอียดปัญหา', {
            'fields': ('problem_description', 'priority', 'status')
        }),
        ('การมอบหมาย', {
            'fields': ('assigned_technician',)
        }),
        ('วันเวลา', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_requester(self, obj):
        return obj.requester.get_full_name() or obj.requester.username
    
    def get_equipment(self, obj):
        return obj.equipment.name
    
    def get_technician(self, obj):
        if obj.assigned_technician:
            return obj.assigned_technician.user.get_full_name() or \
                   obj.assigned_technician.user.username
        return '-'
    
    get_requester.short_description = 'ผู้แจ้ง'
    get_equipment.short_description = 'อุปกรณ์'
    get_technician.short_description = 'ช่างที่รับผิดชอบ'


@admin.register(RepairLog)
class RepairLogAdmin(admin.ModelAdmin):
    """Admin สำหรับบันทึกการซ่อม"""
    list_display = ['get_request_code', 'get_technician', 'started_at', 
                    'completed_at', 'labor_hours', 'cost']
    list_filter = ['started_at', 'completed_at']
    search_fields = ['maintenance_request__request_code', 
                     'technician__user__username', 'description']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def get_request_code(self, obj):
        return obj.maintenance_request.request_code
    
    def get_technician(self, obj):
        return obj.technician.user.get_full_name() or \
               obj.technician.user.username
    
    get_request_code.short_description = 'รหัสคำขอ'
    get_technician.short_description = 'ช่างซ่อม'


# ปรับแต่ง Admin Site
admin.site.site_header = 'ระบบแจ้งซ่อมอุปกรณ์'
admin.site.site_title = 'ระบบแจ้งซ่อม'
admin.site.index_title = 'จัดการระบบแจ้งซ่อมอุปกรณ์'