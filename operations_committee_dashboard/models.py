from django.db import models
from accounts.models import User
from director_dashboard.models import Program, Committee


class OperationsTask(models.Model):
    """Main operational tasks for the committee"""
    TASK_TYPES = [
        ('operational_program', 'البرنامج التشغيلي'),
        ('awards_provision', 'توفير الجوائز'),
        ('individuals_families_followup', 'متابعة الأفراد والأسر'),
        ('public_program', 'البرنامج الجماهيري'),
        ('visits_coordination', 'معاون تنسيق الزيارات'),
    ]

    STATUS_CHOICES = [
        ('not_started', 'لم يبدأ'),
        ('in_progress', 'جاري'),
        ('completed', 'مكتمل'),
        ('overdue', 'متأخر'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='operations_tasks')
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, verbose_name='نوع المهمة')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(verbose_name='الوصف')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started', verbose_name='الحالة')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='الأولوية')
    assigned_to_name = models.CharField(max_length=255, blank=True, verbose_name='اسم المسؤول')
    due_date = models.DateField(verbose_name='الموعد النهائي')
    completion_percentage = models.IntegerField(default=0, verbose_name='نسبة الإنجاز')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='operations_tasks_created')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مهمة تشغيلية'
        verbose_name_plural = 'المهام التشغيلية'

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status != 'completed' and self.due_date < timezone.now().date():
            return True
        return False


class OperationsTeamMember(models.Model):
    """Members of the operations committee"""
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='operations_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operations_memberships')
    role = models.CharField(max_length=100, verbose_name='الدور', blank=True)
    joined_date = models.DateField(auto_now_add=True, verbose_name='تاريخ الانضمام')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    participation_score = models.IntegerField(default=0, verbose_name='درجة المشاركة')

    class Meta:
        unique_together = ['committee', 'user']
        verbose_name = 'عضو اللجنة'
        verbose_name_plural = 'أعضاء اللجنة'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.committee.name}"


class LogisticsResource(models.Model):
    """Logistics and resources management"""
    RESOURCE_TYPES = [
        ('equipment', 'معدات'),
        ('venue', 'مكان'),
        ('transport', 'مواصلات'),
        ('materials', 'مواد'),
        ('budget', 'ميزانية'),
        ('other', 'أخرى'),
    ]

    STATUS_CHOICES = [
        ('available', 'متوفر'),
        ('reserved', 'محجوز'),
        ('in_use', 'قيد الاستخدام'),
        ('maintenance', 'صيانة'),
        ('unavailable', 'غير متوفر'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='logistics_resources')
    resource_type = models.CharField(max_length=50, choices=RESOURCE_TYPES, verbose_name='نوع المورد')
    name = models.CharField(max_length=255, verbose_name='الاسم')
    description = models.TextField(blank=True, verbose_name='الوصف')
    quantity = models.IntegerField(default=1, verbose_name='الكمية')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='الحالة')
    location = models.CharField(max_length=255, blank=True, verbose_name='الموقع')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مورد لوجستي'
        verbose_name_plural = 'الموارد اللوجستية'

    def __str__(self):
        return self.name


class OperationsFileLibrary(models.Model):
    """File library for operational documents"""
    FILE_TYPES = [
        ('operational_plan', 'خطة تشغيلية'),
        ('preparation_list', 'قائمة تجهيز'),
        ('schedule', 'جدول زمني'),
        ('report', 'تقرير'),
        ('other', 'أخرى'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='operations_files')
    file_type = models.CharField(max_length=50, choices=FILE_TYPES, verbose_name='نوع الملف')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(blank=True, verbose_name='الوصف')
    file = models.FileField(upload_to='operations_files/%Y/%m/', verbose_name='الملف')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'ملف تشغيلي'
        verbose_name_plural = 'مكتبة الملفات'

    def __str__(self):
        return self.title


class OperationsWeeklyReport(models.Model):
    """Weekly reports on achievements and challenges"""
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='operations_weekly_reports')
    week_start_date = models.DateField(verbose_name='بداية الأسبوع')
    week_end_date = models.DateField(verbose_name='نهاية الأسبوع')
    achievements = models.TextField(verbose_name='الإنجازات')
    challenges = models.TextField(verbose_name='التحديات')
    completion_rate = models.IntegerField(default=0, verbose_name='نسبة الإنجاز %')
    tasks_completed = models.IntegerField(default=0, verbose_name='المهام المكتملة')
    tasks_pending = models.IntegerField(default=0, verbose_name='المهام المعلقة')
    notes = models.TextField(blank=True, verbose_name='ملاحظات إضافية')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_start_date']
        verbose_name = 'تقرير أسبوعي'
        verbose_name_plural = 'التقارير الأسبوعية'

    def __str__(self):
        return f"تقرير {self.week_start_date} - {self.week_end_date}"


class OperationsNotification(models.Model):
    """Notifications for operations committee"""
    NOTIFICATION_TYPES = [
        ('task_added', 'إضافة مهمة'),
        ('task_updated', 'تعديل مهمة'),
        ('task_overdue', 'مهمة متأخرة'),
        ('resource_added', 'إضافة مورد'),
        ('report_uploaded', 'رفع تقرير'),
        ('discussion_created', 'نقاش جديد'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='operations_notifications')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='operations_notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_task = models.ForeignKey(OperationsTask, on_delete=models.CASCADE, null=True, blank=True)
    related_resource = models.ForeignKey(LogisticsResource, on_delete=models.CASCADE, null=True, blank=True)
    related_discussion = models.ForeignKey('cultural_committee_dashboard.Discussion', on_delete=models.CASCADE,
                                           null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'

    def __str__(self):
        return self.title
