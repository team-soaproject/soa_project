from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from repairs.models import Equipment, Technician, MaintenanceRequest, RepairLog
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'สร้างข้อมูลตัวอย่างสำหรับทดสอบระบบ'

    def handle(self, *args, **kwargs):
        self.stdout.write('กำลังสร้างข้อมูลตัวอย่าง...')
        
        # ลบข้อมูลเก่า
        RepairLog.objects.all().delete()
        MaintenanceRequest.objects.all().delete()
        Technician.objects.all().delete()
        Equipment.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        
        # สร้าง Users
        self.stdout.write('สร้าง Users...')
        
        # Admin user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='Admin',
                last_name='System'
            )
        
        # Regular users
        users = []
        user_data = [
            ('somchai', 'สมชาย', 'ใจดี'),
            ('suda', 'สุดา', 'สวยงาม'),
            ('manit', 'มานิต', 'รักงาน'),
            ('pranee', 'ปราณี', 'มีสุข'),
        ]
        
        for username, first_name, last_name in user_data:
            user = User.objects.create_user(
                username=username,
                email=f'{username}@company.com',
                password='password123',
                first_name=first_name,
                last_name=last_name
            )
            users.append(user)
        
        # สร้าง Technicians
        self.stdout.write('สร้าง Technicians...')
        
        technician_data = [
            ('จักรพันธ์', 'ช่างไฟฟ้า', 'T001', 'ELECTRICAL', '081-234-5678'),
            ('วิชัย', 'ช่างเครื่องกล', 'T002', 'MECHANICAL', '082-345-6789'),
            ('ประเสริฐ', 'ช่างคอมพิวเตอร์', 'T003', 'IT', '083-456-7890'),
            ('สมหมาย', 'ช่างประปา', 'T004', 'PLUMBING', '084-567-8901'),
        ]
        
        technicians = []
        for first_name, last_name, emp_id, expertise, phone in technician_data:
            user = User.objects.create_user(
                username=emp_id.lower(),
                email=f'{emp_id.lower()}@company.com',
                password='password123',
                first_name=first_name,
                last_name=last_name
            )
            technician = Technician.objects.create(
                user=user,
                employee_id=emp_id,
                expertise=expertise,
                phone=phone,
                is_available=random.choice([True, False])
            )
            technicians.append(technician)
        
        # สร้าง Equipment
        self.stdout.write('สร้าง Equipment...')
        
        equipment_list = []
        departments = ['IT', 'HR', 'Finance', 'Operations', 'Marketing']
        equipment_types = [
            ('คอมพิวเตอร์', 'PC'),
            ('เครื่องพิมพ์', 'PRINTER'),
            ('เครื่องถ่ายเอกสาร', 'COPIER'),
            ('เครื่องปรับอากาศ', 'AC'),
            ('โทรศัพท์', 'PHONE'),
            ('โปรเจคเตอร์', 'PROJECTOR'),
        ]
        
        for i in range(20):
            eq_type, prefix = random.choice(equipment_types)
            dept = random.choice(departments)
            equipment = Equipment.objects.create(
                equipment_code=f'{prefix}{i+1:03d}',
                name=f'{eq_type} {i+1}',
                department=dept,
                location=f'อาคาร A ชั้น {random.randint(1, 5)} ห้อง {random.randint(101, 505)}',
                status=random.choice(['ACTIVE', 'ACTIVE', 'ACTIVE', 'UNDER_REPAIR']),
                purchase_date=timezone.now().date() - timedelta(days=random.randint(30, 1000)),
                description=f'รายละเอียดของ {eq_type}'
            )
            equipment_list.append(equipment)
        
        # สร้าง Maintenance Requests
        self.stdout.write('สร้าง Maintenance Requests...')
        
        problems = [
            'เครื่องไม่สามารถเปิดได้',
            'มีเสียงผิดปกติ',
            'ทำงานช้ากว่าปกติ',
            'หน้าจอไม่แสดงผล',
            'เชื่อมต่อเครือข่ายไม่ได้',
            'พิมพ์เอกสารไม่ออก',
            'มีควันออกมา',
            'อุณหภูมิสูงเกินปกติ',
        ]
        
        maintenance_requests = []
        for i in range(15):
            days_ago = random.randint(0, 30)
            created_date = timezone.now() - timedelta(days=days_ago)
            
            status_choice = random.choice(['PENDING', 'IN_PROGRESS', 'COMPLETED'])
            
            request = MaintenanceRequest.objects.create(
                requester=random.choice(users),
                equipment=random.choice(equipment_list),
                problem_description=random.choice(problems),
                priority=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                status=status_choice,
                assigned_technician=random.choice(technicians) if status_choice != 'PENDING' else None,
                created_at=created_date,
                updated_at=created_date,
                completed_at=created_date + timedelta(hours=random.randint(2, 48)) if status_choice == 'COMPLETED' else None
            )
            maintenance_requests.append(request)
        
        # สร้าง Repair Logs
        self.stdout.write('สร้าง Repair Logs...')
        
        completed_requests = [r for r in maintenance_requests if r.status == 'COMPLETED']
        
        parts_list = [
            'สายไฟ, ปลั๊กไฟ',
            'หน่วยความจำ RAM 8GB',
            'ฮาร์ดดิสก์ 1TB',
            'แบตเตอรี่',
            'พัดลม',
            'หัวพิมพ์',
            'โทนเนอร์',
            'สายสัญญาณ HDMI',
        ]
        
        for request in completed_requests[:10]:
            hours = round(random.uniform(1, 8), 2)
            RepairLog.objects.create(
                maintenance_request=request,
                technician=request.assigned_technician,
                description=f'ซ่อมเรียบร้อยแล้ว: {request.problem_description}',
                parts_used=random.choice(parts_list),
                labor_hours=hours,
                cost=hours * 500 + random.randint(100, 5000),
                started_at=request.created_at + timedelta(hours=1),
                completed_at=request.completed_at,
                notes='ทดสอบการทำงานเรียบร้อย'
            )
        
        self.stdout.write(self.style.SUCCESS('✓ สร้างข้อมูลตัวอย่างเสร็จสิ้น!'))
        self.stdout.write(f'  Users: {User.objects.count()}')
        self.stdout.write(f'  Technicians: {Technician.objects.count()}')
        self.stdout.write(f'  Equipment: {Equipment.objects.count()}')
        self.stdout.write(f'  Maintenance Requests: {MaintenanceRequest.objects.count()}')
        self.stdout.write(f'  Repair Logs: {RepairLog.objects.count()}')
        self.stdout.write('')
        self.stdout.write('ข้อมูลการ Login:')
        self.stdout.write('  Admin: username=admin, password=admin123')
        self.stdout.write('  User: username=somchai, password=password123')
        self.stdout.write('  Technician: username=t001, password=password123')