from django.db import models
from accounts.models import User
from director_dashboard.models import Program, Committee


class CulturalTask(models.Model):
    """Main cultural tasks for the committee"""
    TASK_TYPES = [
        ('cultural_data', 'بيانات ومسابقات ثقافية'),
        ('weekly_program', 'البرنامج الثقافي الأسبوعي'),
        ('reading_followup', 'متابعة القراءة النافعة'),
        ('friday_lesson', 'دروس لقاء دوري (عصر الجمعة)'),
        ('courses_coordination', 'تنسيق الدورات الهادفة'),
    ]

    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('in_progress', 'جاري العمل'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='cultural_tasks')
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
                                   related_name='cultural_tasks_created')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مهمة ثقافية'
        verbose_name_plural = 'المهام الثقافية'

    def __str__(self):
        return self.title


class CommitteeMember(models.Model):
    """Members of the cultural committee"""
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='cultural_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='committee_memberships')
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


class FileLibrary(models.Model):
    """Library for cultural files"""
    FILE_TYPES = [
        ('cultural_plan', 'خطة ثقافية'),
        ('competition', 'مسابقة'),
        ('book_summary', 'ملخص كتاب'),
        ('other', 'أخرى'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='cultural_files')
    file_type = models.CharField(max_length=50, choices=FILE_TYPES, verbose_name='نوع الملف')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(blank=True, verbose_name='الوصف')
    file = models.FileField(upload_to='cultural_files/%Y/%m/', verbose_name='الملف')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'ملف ثقافي'
        verbose_name_plural = 'مكتبة الملفات'

    def __str__(self):
        return self.title


class Discussion(models.Model):
    """Discussion board for committee members"""
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='discussions')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    content = models.TextField(verbose_name='المحتوى')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='discussions_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False, verbose_name='مثبت')
    is_public_to_all_supervisors = models.BooleanField(default=False, verbose_name='مشترك بين جميع المشرفين')

    class Meta:
        ordering = ['-is_pinned', '-created_at']
        verbose_name = 'نقاش'
        verbose_name_plural = 'التعليقات والنقاشات'

    def __str__(self):
        return self.title


class DiscussionComment(models.Model):
    """Comments on discussions"""
    discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(verbose_name='التعليق')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'تعليق'
        verbose_name_plural = 'التعليقات'

    def __str__(self):
        return f"تعليق على {self.discussion.title}"


class CulturalReport(models.Model):
    """Reports for cultural activities"""
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='cultural_reports')
    title = models.CharField(max_length=255, verbose_name='عنوان التقرير')
    report_type = models.CharField(max_length=50, verbose_name='نوع التقرير')
    content = models.TextField(verbose_name='المحتوى')
    file = models.FileField(upload_to='cultural_reports/%Y/%m/', blank=True, null=True, verbose_name='ملف مرفق')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تقرير ثقافي'
        verbose_name_plural = 'التقارير الثقافية'

    def __str__(self):
        return self.title


class CulturalNotification(models.Model):
    """Notifications for cultural committee"""
    NOTIFICATION_TYPES = [
        ('task_added', 'إضافة مهمة'),
        ('task_updated', 'تعديل مهمة'),
        ('file_uploaded', 'رفع ملف'),
        ('report_uploaded', 'رفع تقرير'),
        ('discussion_created', 'نقاش جديد'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cultural_notifications')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_task = models.ForeignKey(CulturalTask, on_delete=models.CASCADE, null=True, blank=True)
    related_file = models.ForeignKey(FileLibrary, on_delete=models.CASCADE, null=True, blank=True)
    related_report = models.ForeignKey(CulturalReport, on_delete=models.CASCADE, null=True, blank=True)
    related_discussion = models.ForeignKey(Discussion, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'

    def __str__(self):
        return self.title
