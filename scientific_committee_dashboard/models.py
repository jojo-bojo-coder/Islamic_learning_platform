from django.db import models
from accounts.models import User
from director_dashboard.models import Program, Committee


class ScientificTask(models.Model):
    """Main scientific tasks for the committee"""
    TASK_TYPES = [
        ('supervisor_lessons', 'دروس مشرفين'),
        ('hosting_coordination', 'تنسيق الاستضافات'),
        ('lessons_officer', 'مسؤول الدروس'),
        ('adhan_officer', 'مسؤول الأذان'),
        ('shoulders_adhan_prayer', 'الكتافات والأذان والصلاة'),
        ('scientific_data', 'بيانات علمية (ضربات)'),
    ]

    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('in_progress', 'جاري العمل'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='scientific_tasks')
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
                                   related_name='scientific_tasks_created')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مهمة علمية'
        verbose_name_plural = 'المهام العلمية'

    def __str__(self):
        return self.title


class ScientificMember(models.Model):
    """Members of the scientific committee"""
    ROLE_CHOICES = [
        ('lecturer', 'محاضر'),
        ('coordinator', 'منسق'),
        ('researcher', 'باحث'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='scientific_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scientific_memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, verbose_name='الدور')
    joined_date = models.DateField(auto_now_add=True, verbose_name='تاريخ الانضمام')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    participation_score = models.IntegerField(default=0, verbose_name='درجة المشاركة')
    specialization = models.CharField(max_length=255, blank=True, verbose_name='التخصص')

    class Meta:
        unique_together = ['committee', 'user']
        verbose_name = 'عضو اللجنة العلمية'
        verbose_name_plural = 'أعضاء اللجنة العلمية'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"


class ScientificFile(models.Model):
    """Library for scientific files"""
    FILE_TYPES = [
        ('research_paper', 'ورقة علمية'),
        ('presentation', 'عرض تقديمي'),
        ('lecture_notes', 'ملاحظات محاضرة'),
        ('workshop_material', 'مواد ورشة عمل'),
        ('other', 'أخرى'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='scientific_files')
    file_type = models.CharField(max_length=50, choices=FILE_TYPES, verbose_name='نوع الملف')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(blank=True, verbose_name='الوصف')
    author = models.CharField(max_length=255, blank=True, verbose_name='المؤلف')
    file = models.FileField(upload_to='scientific_files/%Y/%m/', verbose_name='الملف')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'ملف علمي'
        verbose_name_plural = 'مكتبة الملفات العلمية'

    def __str__(self):
        return self.title


class Lecture(models.Model):
    """Lectures and workshops"""
    LECTURE_TYPES = [
        ('lecture', 'محاضرة'),
        ('workshop', 'ورشة عمل'),
        ('seminar', 'ندوة'),
        ('hosting', 'استضافة'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'مجدولة'),
        ('ongoing', 'جارية'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='lectures')
    lecture_type = models.CharField(max_length=20, choices=LECTURE_TYPES, verbose_name='نوع المحاضرة')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(verbose_name='الوصف')
    lecturer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='lectures_given', verbose_name='المحاضر')
    guest_lecturer = models.CharField(max_length=255, blank=True, verbose_name='محاضر ضيف')
    date = models.DateField(verbose_name='التاريخ')
    time = models.TimeField(verbose_name='الوقت')
    location = models.CharField(max_length=255, verbose_name='المكان')
    duration_minutes = models.IntegerField(verbose_name='المدة (بالدقائق)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='الحالة')
    attendance_count = models.IntegerField(default=0, verbose_name='عدد الحضور')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='lectures_created')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'محاضرة'
        verbose_name_plural = 'المحاضرات والورش'

    def __str__(self):
        return f"{self.title} - {self.date}"


class LectureAttendance(models.Model):
    """Attendance tracking for lectures"""
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='attendances')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lecture_attendances')
    attended = models.BooleanField(default=False, verbose_name='حضر')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    rating = models.IntegerField(null=True, blank=True, verbose_name='التقييم')
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='recorded_lecture_attendances')

    class Meta:
        unique_together = ['lecture', 'user']
        verbose_name = 'حضور محاضرة'
        verbose_name_plural = 'حضور المحاضرات'

    def __str__(self):
        return f"{self.user} - {self.lecture.title}"


class ScientificReport(models.Model):
    """Reports for scientific activities"""
    REPORT_TYPES = [
        ('attendance', 'تقرير حضور'),
        ('hosting_evaluation', 'تقييم الاستضافات'),
        ('monthly', 'تقرير شهري'),
        ('activity_summary', 'ملخص الأنشطة'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='scientific_reports')
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES, verbose_name='نوع التقرير')
    title = models.CharField(max_length=255, verbose_name='عنوان التقرير')
    content = models.TextField(verbose_name='المحتوى')
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                         verbose_name='نسبة الحضور')
    evaluation_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                          verbose_name='درجة التقييم')
    file = models.FileField(upload_to='scientific_reports/%Y/%m/', blank=True, null=True,
                           verbose_name='ملف مرفق')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تقرير علمي'
        verbose_name_plural = 'التقارير العلمية'

    def __str__(self):
        return self.title


class ScientificNotification(models.Model):
    """Notifications for scientific committee"""
    NOTIFICATION_TYPES = [
        ('task_added', 'إضافة مهمة'),
        ('task_updated', 'تعديل مهمة'),
        ('lecture_scheduled', 'محاضرة مجدولة'),
        ('workshop_added', 'إضافة ورشة عمل'),
        ('file_uploaded', 'رفع ملف'),
        ('report_uploaded', 'رفع تقرير'),
        ('discussion_created', 'نقاش جديد'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scientific_notifications')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='scientific_notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_task = models.ForeignKey(ScientificTask, on_delete=models.CASCADE, null=True, blank=True)
    related_lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, null=True, blank=True)
    related_file = models.ForeignKey(ScientificFile, on_delete=models.CASCADE, null=True, blank=True)
    related_report = models.ForeignKey(ScientificReport, on_delete=models.CASCADE, null=True, blank=True)
    related_discussion = models.ForeignKey('cultural_committee_dashboard.Discussion', on_delete=models.CASCADE,
                                           null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'إشعار علمي'
        verbose_name_plural = 'الإشعارات العلمية'

    def __str__(self):
        return self.title
