from django.db import models
from accounts.models import User
from director_dashboard.models import Program, Committee


class ShariaTask(models.Model):
    """Main sharia tasks for the committee"""
    TASK_TYPES = [
        ('honorable_minutes', 'برنامج الدقائق المشرفة'),
        ('youth_achievement', 'متابعة إنجاز الشباب'),
        ('daily_message', 'رسالة يومية/أسبوعية'),
        ('family_competition', 'مسابقة أسرية'),
        ('weekly_article', 'مقال للقراءة الأسبوعية'),
        ('youth_books', 'متابعة الكتب الشبابية'),
    ]

    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('in_progress', 'جاري العمل'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sharia_tasks')
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, verbose_name='نوع المهمة')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(verbose_name='الوصف')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    assigned_to_name = models.CharField(max_length=255, blank=True, verbose_name='اسم المسؤول')
    due_date = models.DateField(verbose_name='تاريخ الاستحقاق')
    completion_percentage = models.IntegerField(default=0, verbose_name='نسبة الإنجاز')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='sharia_tasks_created')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مهمة شرعية'
        verbose_name_plural = 'المهام الشرعية'

    def __str__(self):
        return self.title


class ShariaMember(models.Model):
    """Members of the sharia committee"""
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sharia_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sharia_memberships')
    role = models.CharField(max_length=100, verbose_name='الدور', blank=True)
    joined_date = models.DateField(auto_now_add=True, verbose_name='تاريخ الانضمام')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    participation_score = models.IntegerField(default=0, verbose_name='درجة المشاركة')

    class Meta:
        unique_together = ['committee', 'user']
        verbose_name = 'عضو اللجنة الشرعية'
        verbose_name_plural = 'أعضاء اللجنة الشرعية'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.committee.name}"


class ShariaFile(models.Model):
    """Library for sharia files"""
    FILE_TYPES = [
        ('lesson', 'درس'),
        ('article', 'مقال'),
        ('brochure', 'مطوية'),
        ('competition', 'مسابقة'),
        ('book', 'كتاب'),
        ('other', 'أخرى'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sharia_files')
    file_type = models.CharField(max_length=50, choices=FILE_TYPES, verbose_name='نوع الملف')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(blank=True, verbose_name='الوصف')
    file = models.FileField(upload_to='sharia_files/%Y/%m/', verbose_name='الملف')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'ملف شرعي'
        verbose_name_plural = 'مكتبة الملفات الشرعية'

    def __str__(self):
        return self.title


class DailyMessage(models.Model):
    """Daily/Weekly messages"""
    MESSAGE_TYPES = [
        ('daily', 'يومية'),
        ('weekly', 'أسبوعية'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='daily_messages')
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, verbose_name='نوع الرسالة')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    content = models.TextField(verbose_name='المحتوى')
    scheduled_date = models.DateField(verbose_name='تاريخ الإرسال')
    is_sent = models.BooleanField(default=False, verbose_name='تم الإرسال')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_date']
        verbose_name = 'رسالة'
        verbose_name_plural = 'الرسائل اليومية والأسبوعية'

    def __str__(self):
        return self.title


class FamilyCompetition(models.Model):
    """Family competitions"""
    STATUS_CHOICES = [
        ('upcoming', 'قادمة'),
        ('active', 'نشطة'),
        ('completed', 'مكتملة'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='family_competitions')
    title = models.CharField(max_length=255, verbose_name='عنوان المسابقة')
    description = models.TextField(verbose_name='الوصف')
    start_date = models.DateField(verbose_name='تاريخ البداية')
    end_date = models.DateField(verbose_name='تاريخ النهاية')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming', verbose_name='الحالة')
    file = models.FileField(upload_to='competitions/%Y/%m/', blank=True, null=True, verbose_name='ملف المسابقة')
    participants_count = models.IntegerField(default=0, verbose_name='عدد المشاركين')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مسابقة أسرية'
        verbose_name_plural = 'المسابقات الأسرية'

    def __str__(self):
        return self.title


class YouthBook(models.Model):
    """Youth books tracking"""
    STATUS_CHOICES = [
        ('reading', 'قيد القراءة'),
        ('completed', 'مكتمل'),
        ('pending', 'قيد الانتظار'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='youth_books')
    title = models.CharField(max_length=255, verbose_name='عنوان الكتاب')
    author = models.CharField(max_length=255, verbose_name='المؤلف')
    description = models.TextField(blank=True, verbose_name='الوصف')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_books', verbose_name='مكلف به')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    progress_percentage = models.IntegerField(default=0, verbose_name='نسبة الإنجاز')
    start_date = models.DateField(null=True, blank=True, verbose_name='تاريخ البداية')
    completion_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الإكمال')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='created_books')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'كتاب شبابي'
        verbose_name_plural = 'الكتب الشبابية'

    def __str__(self):
        return self.title


class ShariaReport(models.Model):
    """Reports for sharia activities"""
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sharia_reports')
    title = models.CharField(max_length=255, verbose_name='عنوان التقرير')
    report_type = models.CharField(max_length=50, verbose_name='نوع التقرير')
    content = models.TextField(verbose_name='المحتوى')
    interaction_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='نسبة التفاعل')
    file = models.FileField(upload_to='sharia_reports/%Y/%m/', blank=True, null=True, verbose_name='ملف مرفق')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تقرير شرعي'
        verbose_name_plural = 'التقارير الشرعية'

    def __str__(self):
        return self.title


class ShariaNotification(models.Model):
    """Notifications for sharia committee"""
    NOTIFICATION_TYPES = [
        ('task_added', 'إضافة مهمة'),
        ('task_updated', 'تعديل مهمة'),
        ('lesson_scheduled', 'موعد درس'),
        ('competition_uploaded', 'مسابقة جديدة'),
        ('message_sent', 'إرسال رسالة'),
        ('report_uploaded', 'رفع تقرير'),
        ('discussion_created', 'نقاش جديد'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sharia_notifications')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sharia_notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_task = models.ForeignKey(ShariaTask, on_delete=models.CASCADE, null=True, blank=True)
    related_competition = models.ForeignKey(FamilyCompetition, on_delete=models.CASCADE, null=True, blank=True)
    related_report = models.ForeignKey(ShariaReport, on_delete=models.CASCADE, null=True, blank=True)
    related_discussion = models.ForeignKey('cultural_committee_dashboard.Discussion', on_delete=models.CASCADE,
                                           null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'إشعار شرعي'
        verbose_name_plural = 'الإشعارات الشرعية'

    def __str__(self):
        return self.title
