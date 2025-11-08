from django.db import models
from accounts.models import User
from director_dashboard.models import Program, Committee, Student


class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('completed', 'مكتملة'),
        ('overdue', 'متأخرة'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
    ]

    title = models.CharField(max_length=255, verbose_name='عنوان المهمة')
    description = models.TextField(verbose_name='الوصف')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='tasks')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(verbose_name='تاريخ الاستحقاق')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')

    is_scientific_task = models.BooleanField(default=False, verbose_name='مهمة علمية')
    scientific_task_ref = models.ForeignKey('scientific_committee_dashboard.ScientificTask', on_delete=models.SET_NULL,
                                            null=True, blank=True, verbose_name='المهمة العلمية المرجعية')

    is_sports_task = models.BooleanField(default=False, verbose_name='مهمة رياضية')
    sports_task_ref = models.ForeignKey('sports_committee_dashboard.SportsTask', on_delete=models.SET_NULL,
                                        null=True, blank=True, verbose_name='المهمة الرياضية المرجعية')

    is_sharia_task = models.BooleanField(default=False, verbose_name='مهمة شرعية')
    sharia_task_ref = models.ForeignKey('sharia_committee_dashboard.ShariaTask', on_delete=models.SET_NULL,
                                        null=True, blank=True, verbose_name='المهمة الشرعية المرجعية')

    is_cultural_task = models.BooleanField(default=False, verbose_name='مهمة ثقافية')
    cultural_task_ref = models.ForeignKey('cultural_committee_dashboard.CulturalTask', on_delete=models.SET_NULL,
                                          null=True, blank=True, verbose_name='المهمة الثقافية المرجعية')

    is_operations_task = models.BooleanField(default=False, verbose_name='مهمة تشغيلية')
    operations_task_ref = models.ForeignKey('operations_committee_dashboard.OperationsTask', on_delete=models.SET_NULL,
                                            null=True, blank=True, verbose_name='المهمة التشغيلية المرجعية')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مهمة'
        verbose_name_plural = 'المهام'

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status != 'completed' and self.due_date < timezone.now().date():
            return True
        return False


class Activity(models.Model):
    name = models.CharField(max_length=255, verbose_name='اسم النشاط')
    description = models.TextField(verbose_name='الوصف')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='activities')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    date = models.DateField(verbose_name='تاريخ النشاط')
    time = models.TimeField(verbose_name='وقت النشاط', null=True, blank=True)
    location = models.CharField(max_length=255, verbose_name='المكان', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'نشاط'
        verbose_name_plural = 'الأنشطة'

    def __str__(self):
        return self.name


class StudentAttendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendances')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='attendances')
    attended = models.BooleanField(default=False, verbose_name='حضر')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['student', 'activity']
        verbose_name = 'حضور طالب'
        verbose_name_plural = 'حضور الطلاب'

    def __str__(self):
        return f"{self.student} - {self.activity}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_added', 'مهمة جديدة'),
        ('committee_delayed', 'تأخر لجنة'),
        ('task_overdue', 'مهمة متأخرة'),
        ('activity_reminder', 'تذكير بنشاط'),
        ('discussion_created', 'نقاش جديد'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    related_committee = models.ForeignKey(Committee, on_delete=models.CASCADE, null=True, blank=True)
    related_discussion = models.ForeignKey('cultural_committee_dashboard.Discussion', on_delete=models.CASCADE,
                                           null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'

    def __str__(self):
        return self.title
