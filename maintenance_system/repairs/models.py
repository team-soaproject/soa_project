from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


class Equipment(models.Model):
    """Model สำหรับอุปกรณ์"""
    STATUS_CHOICES = [
        ('ACTIVE', 'ใช้งานได้'),
        ('UNDER_REPAIR', 'กำลังซ่อม'),
        ('OUT_OF_SERVICE', 'เสีย'),
    ]
    
    equipment_code = models.CharField(max_length=50, unique=True, verbose_name='รหัสอุปกรณ์')
    name = models.CharField(max_length=200, verbose_name='ชื่ออุปกรณ์')
    department = models.CharField(max_length=100, verbose_name='แผนก')
    location = models.CharField(max_length=200, verbose_name='สถานที่ตั้ง')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='ACTIVE',
        verbose_name='สถานะ'
    )
    purchase_date = models.DateField(null=True, blank=True, verbose_name='วันที่ซื้อ')
    description = models.TextField(blank=True, verbose_name='รายละเอียด')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไข')
    
    class Meta:
        verbose_name = 'อุปกรณ์'
        verbose_name_plural = 'อุปกรณ์ทั้งหมด'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.equipment_code} - {self.name}"


class Technician(models.Model):
    """Model สำหรับช่างซ่อม"""
    EXPERTISE_CHOICES = [
        ('ELECTRICAL', 'ไฟฟ้า'),
        ('MECHANICAL', 'เครื่องกล'),
        ('IT', 'คอมพิวเตอร์/IT'),
        ('PLUMBING', 'ประปา'),
        ('GENERAL', 'ทั่วไป'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='ผู้ใช้')
    employee_id = models.CharField(max_length=50, unique=True, verbose_name='รหัสพนักงาน')
    expertise = models.CharField(
        max_length=20, 
        choices=EXPERTISE_CHOICES,
        verbose_name='ความเชี่ยวชาญ'
    )
    phone = models.CharField(max_length=20, verbose_name='เบอร์โทร')
    is_available = models.BooleanField(default=True, verbose_name='ว่าง')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')
    
    class Meta:
        verbose_name = 'ช่างซ่อม'
        verbose_name_plural = 'ช่างซ่อมทั้งหมด'
        ordering = ['user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_expertise_display()}"


class MaintenanceRequest(models.Model):
    """Model สำหรับรายการแจ้งซ่อม"""
    PRIORITY_CHOICES = [
        ('LOW', 'ปกติ'),
        ('MEDIUM', 'ด่วน'),
        ('HIGH', 'ด่วนมาก'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'รอดำเนินการ'),
        ('IN_PROGRESS', 'กำลังดำเนินการ'),
        ('COMPLETED', 'เสร็จสิ้น'),
        ('CANCELLED', 'ยกเลิก'),
    ]
    
    request_code = models.CharField(max_length=50, unique=True, verbose_name='รหัสแจ้งซ่อม')
    requester = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='maintenance_requests',
        verbose_name='ผู้แจ้ง'
    )
    equipment = models.ForeignKey(
        Equipment, 
        on_delete=models.CASCADE, 
        related_name='maintenance_requests',
        verbose_name='อุปกรณ์'
    )
    problem_description = models.TextField(verbose_name='รายละเอียดปัญหา')
    problem_image = models.ImageField(
        upload_to='maintenance_images/', 
        null=True, 
        blank=True,
        verbose_name='รูปภาพปัญหา'
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='LOW',
        verbose_name='ความเร่งด่วน'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='PENDING',
        verbose_name='สถานะ'
    )
    assigned_technician = models.ForeignKey(
        Technician, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_requests',
        verbose_name='ช่างที่รับผิดชอบ'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่แจ้ง')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='วันที่แก้ไข')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='วันที่เสร็จสิ้น')
    
    class Meta:
        verbose_name = 'รายการแจ้งซ่อม'
        verbose_name_plural = 'รายการแจ้งซ่อมทั้งหมด'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.request_code} - {self.equipment.name}"
    
    def save(self, *args, **kwargs):
        # สร้างรหัสแจ้งซ่อมอัตโนมัติ
        if not self.request_code:
            from datetime import datetime
            today = datetime.now().strftime('%Y%m%d')
            last_request = MaintenanceRequest.objects.filter(
                request_code__startswith=f'REQ{today}'
            ).order_by('-request_code').first()
            
            if last_request:
                last_number = int(last_request.request_code[-4:])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.request_code = f'REQ{today}{new_number:04d}'
        
        # อัพเดทสถานะอุปกรณ์
        if self.status == 'IN_PROGRESS':
            self.equipment.status = 'UNDER_REPAIR'
            self.equipment.save()
        elif self.status == 'COMPLETED':
            self.equipment.status = 'ACTIVE'
            self.equipment.save()
            if not self.completed_at:
                from django.utils import timezone
                self.completed_at = timezone.now()
        
        super().save(*args, **kwargs)


class RepairLog(models.Model):
    """Model สำหรับบันทึกการซ่อม"""
    maintenance_request = models.ForeignKey(
        MaintenanceRequest, 
        on_delete=models.CASCADE, 
        related_name='repair_logs',
        verbose_name='งานซ่อม'
    )
    technician = models.ForeignKey(
        Technician, 
        on_delete=models.CASCADE, 
        related_name='repair_logs',
        verbose_name='ช่าง'
    )
    description = models.TextField(verbose_name='รายละเอียดการซ่อม')
    parts_used = models.TextField(blank=True, verbose_name='อะไหล่ที่ใช้')
    labor_hours = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        validators=[MinValueValidator(0)],
        verbose_name='ชั่วโมงการทำงาน'
    )
    cost = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='ค่าใช้จ่าย'
    )
    started_at = models.DateTimeField(verbose_name='เวลาเริ่มซ่อม')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='เวลาเสร็จสิ้น')
    notes = models.TextField(blank=True, verbose_name='หมายเหตุ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่สร้าง')
    
    class Meta:
        verbose_name = 'บันทึกการซ่อม'
        verbose_name_plural = 'บันทึกการซ่อมทั้งหมด'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.maintenance_request.request_code} - {self.technician.user.get_full_name()}"
# Create your models here.
