from django.contrib import admin
from .models import Equipment, Technician, MaintenanceRequest, RepairLog


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['equipment_code', 'name', 'department', 'location', 
                    'status', 'created_at']
    list_filter = ['status', 'department', 'created_at']
    search_fields = ['equipment_code', 'name', 'department', 'location']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('ข้อมูลพื้นฐาน', {
            'fields': ('equipment_code', 'name', 'department', 'location')
        }),
        ('สถานะและรายละเอียด', {
            'fields': ('status', 'description', 'purchase_date')
        }),
        ('ข้อมูลระบบ', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'get_full_name', 'expertise', 
                    'phone', 'is_available', 'created_at']
    list_filter = ['expertise', 'is_available', 'created_at']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name', 'phone']
    readonly_fields = ['created_at']
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'ชื่อ-สกุล'
    
    fieldsets = (
        ('ข้อมูลส่วนตัว', {
            'fields': ('user', 'employee_id', 'phone')
        }),
        ('ข้อมูลการทำงาน', {
            'fields': ('expertise', 'is_available')
        }),
        ('ข้อมูลระบบ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ['request_code', 'equipment', 'requester', 'priority', 
                    'status', 'assigned_technician', 'created_at']
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['request_code', 'problem_description', 
                     'equipment__name', 'requester__username']
    readonly_fields = ['request_code', 'created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('ข้อมูลการแจ้งซ่อม', {
            'fields': ('request_code', 'requester', 'equipment')
        }),
        ('รายละเอียดปัญหา', {
            'fields': ('problem_description', 'problem_image', 'priority')
        }),
        ('การจัดการ', {
            'fields': ('status', 'assigned_technician')
        }),
        ('ข้อมูลระบบ', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # New object
            obj.requester = request.user
        super().save_model(request, obj, form, change)


@admin.register(RepairLog)
class RepairLogAdmin(admin.ModelAdmin):
    list_display = ['maintenance_request', 'technician', 'labor_hours', 
                    'cost', 'started_at', 'completed_at']
    list_filter = ['technician', 'started_at', 'completed_at']
    search_fields = ['maintenance_request__request_code', 'description', 
                     'parts_used', 'technician__user__first_name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('ข้อมูลงานซ่อม', {
            'fields': ('maintenance_request', 'technician')
        }),
        ('รายละเอียดการซ่อม', {
            'fields': ('description', 'parts_used', 'notes')
        }),
        ('เวลาและค่าใช้จ่าย', {
            'fields': ('started_at', 'completed_at', 'labor_hours', 'cost')
        }),
        ('ข้อมูลระบบ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# Customize Admin Site
admin.site.site_header = 'ระบบแจ้งซ่อมอุปกรณ์'
admin.site.site_title = 'Maintenance System Admin'
admin.site.index_title = 'จัดการระบบแจ้งซ่อม'
# Register your models here.
