from django.db import models
from accounts.models import User


class Program(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                limit_choices_to={'role': 'program_manager'})
    start_date = models.DateField()
    end_date = models.DateField()
    target_students = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @property
    def completion_rate(self):
        # Calculate completion rate based on student progress
        total_students = self.student_set.count()
        if total_students == 0:
            return 0
        completed_students = self.student_set.filter(progress=100).count()
        return (completed_students / total_students) * 100


class Committee(models.Model):
    name = models.CharField(max_length=255)
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   limit_choices_to={'role': 'committee_supervisor'})
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    committee = models.ForeignKey(Committee, on_delete=models.SET_NULL, null=True, blank=True)
    progress = models.IntegerField(default=0)  # 0-100%
    joined_date = models.DateField(auto_now_add=True)
    memorization_level = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username




from django.db import models
from accounts.models import User

class DirectorAlbum(models.Model):
    """Photo albums for the website"""
    title = models.CharField(max_length=255, verbose_name='عنوان الألبوم')
    description = models.TextField(blank=True, verbose_name='الوصف')
    cover_image = models.ImageField(upload_to='albums/covers/%Y/%m/', verbose_name='صورة الغلاف')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'ألبوم'
        verbose_name_plural = 'الألبومات'

    def __str__(self):
        return self.title

    @property
    def photos_count_property(self):
        return self.photos.count()

    # أو استخدم اسمًا أكثر وصفًا
    @property
    def total_photos(self):
        return self.photos.count()


class AlbumPhoto(models.Model):
    """Photos in albums"""
    album = models.ForeignKey(DirectorAlbum, on_delete=models.CASCADE, related_name='photos')
    title = models.CharField(max_length=255, verbose_name='عنوان الصورة')
    image = models.ImageField(upload_to='albums/photos/%Y/%m/', verbose_name='الصورة')
    description = models.TextField(blank=True, verbose_name='الوصف')
    order = models.IntegerField(default=0, verbose_name='ترتيب')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = 'صورة'
        verbose_name_plural = 'الصور'

    def __str__(self):
        return self.title


class DirectorFileLibrary(models.Model):
    """File library for videos, presentations, etc."""
    FILE_TYPES = [
        ('video', 'فيديو'),
        ('presentation', 'عرض تقديمي'),
        ('document', 'وثيقة'),
        ('image', 'صورة'),
        ('audio', 'ملف صوتي'),
        ('other', 'أخرى'),
    ]

    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(blank=True, verbose_name='الوصف')
    file_type = models.CharField(max_length=50, choices=FILE_TYPES, verbose_name='نوع الملف')
    file = models.FileField(upload_to='director_files/%Y/%m/', verbose_name='الملف')
    thumbnail = models.ImageField(upload_to='file_thumbnails/%Y/%m/', blank=True, null=True, verbose_name='صورة مصغرة')
    is_public = models.BooleanField(default=True, verbose_name='عام')
    download_count = models.IntegerField(default=0, verbose_name='عدد التحميلات')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'ملف'
        verbose_name_plural = 'مكتبة الملفات'

    def __str__(self):
        return self.title

    def increment_download_count(self):
        self.download_count += 1
        self.save()


class DirectorAlert(models.Model):
    """Alerts/Notifications for director"""
    ALERT_TYPES = [
        ('supervisor_added', 'إضافة مشرف لجنة'),
        ('task_added', 'إضافة مهمة'),
        ('program_created', 'إنشاء برنامج'),
        ('committee_created', 'إنشاء لجنة'),
        ('report_submitted', 'تسليم تقرير'),
        ('system_alert', 'تنبيه نظام'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'منخفض'),
        ('medium', 'متوسط'),
        ('high', 'عالي'),
    ]

    title = models.CharField(max_length=255, verbose_name='العنوان')
    message = models.TextField(verbose_name='الرسالة')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES, verbose_name='نوع التنبيه')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='الأولوية')
    is_read = models.BooleanField(default=False, verbose_name='مقروء')
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='caused_alerts', verbose_name='المستخدم المرتبط')
    related_program = models.ForeignKey('Program', on_delete=models.SET_NULL, null=True, blank=True,
                                      verbose_name='البرنامج المرتبط')
    related_committee = models.ForeignKey('Committee', on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name='اللجنة المرتبطة')
    created_at = models.DateTimeField(auto_now_add=True)
    action_url = models.CharField(max_length=500, blank=True, verbose_name='رابط الإجراء')
    related_discussion = models.ForeignKey('cultural_committee_dashboard.Discussion', on_delete=models.CASCADE,
                                           null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تنبيه'
        verbose_name_plural = 'التنبيهات'

    def __str__(self):
        return self.title

    def mark_as_read(self):
        self.is_read = True
        self.save()

# ============================================
# نماذج حاسبة النقاط - Points Calculator
# ============================================

class PointsCalculatorSettings(models.Model):
    """
    إعدادات حاسبة النقاط - يمكن تخصيصها لكل مستخدم
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="points_settings",
        verbose_name="المستخدم",
        null=True,
        blank=True
    )

    # إعدادات عامة
    program_name = models.CharField(
        max_length=200,
        default="عشائر آل سلطان",
        verbose_name="اسم البرنامج"
    )

    # اللجان (JSON)
    committees = models.JSONField(
        default=list,
        verbose_name="اللجان",
        help_text="قائمة بأسماء اللجان، مثال: ['الثقافية', 'الإعلامية', 'العلمية']"
    )

    # الدفعات (JSON) - كل دفعة لها اسم وعدد طلاب وأسماء الطلاب
    batches = models.JSONField(
        default=list,
        verbose_name="الدفعات",
        help_text="قائمة بالدفعات، مثال: [{'name': 'ثالث', 'student_count': 8, 'emoji': '🎯', 'students': ['اسم1', 'اسم2']}, ...]"
    )

    # رقم الأسبوع الحالي
    current_week = models.IntegerField(
        default=1,
        verbose_name="رقم الأسبوع الحالي",
        help_text="رقم الأسبوع الذي سيظهر في القالب"
    )

    # إعدادات إضافية
    default_committee_name = models.CharField(
        max_length=200,
        default="[يكتب هنا اسم اللجنة]",
        verbose_name="النص الافتراضي لاسم اللجنة"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'إعدادات حاسبة النقاط'
        verbose_name_plural = 'إعدادات حاسبة النقاط'

    def __str__(self):
        if self.user:
            return f"إعدادات {self.user.email}"
        return "إعدادات عامة"

    @staticmethod
    def get_default_settings():
        """إرجاع الإعدادات الافتراضية مع أسماء عربية عشوائية"""
        random_names_batch1 = [
            'أحمد محمد', 'خالد عبدالله', 'سعد علي', 'فهد ناصر',
            'عبدالرحمن صالح', 'محمد يوسف', 'عبدالعزيز حسن', 'تركي ماجد'
        ]
        random_names_batch2 = [
            'عمر إبراهيم', 'يوسف حمد', 'عبدالله سعيد', 'مشعل فيصل',
            'نواف راشد', 'عبدالمجيد خالد', 'صالح عبدالرحمن', 'علي فهد', 'مازن سعد'
        ]
        random_names_batch3 = [
            'عبداللطيف محمد', 'عزام خالد', 'أنس فهد', 'عبدالعزيز ناصر',
            'محمد عبدالله', 'عبدالرحمن صالح', 'مازن علي', 'عمار يوسف',
            'فهد سعد', 'خالد عبدالعزيز', 'عبدالله محمد', 'صالح ناصر', 'علي فهد'
        ]

        return {
            'program_name': 'عشائر آل سلطان',
            'committees': ['الثقافية', 'الإعلامية', 'العلمية', 'الاجتماعية', 'الرياضية', 'التحفيزية'],
            'batches': [
                {
                    'name': 'ثالث',
                    'student_count': 8,
                    'emoji': '🎯',
                    'students': random_names_batch1
                },
                {
                    'name': 'ثاني',
                    'student_count': 9,
                    'emoji': '🌟',
                    'students': random_names_batch2
                },
                {
                    'name': 'أول',
                    'student_count': 13,
                    'emoji': '🏅',
                    'students': random_names_batch3
                }
            ],
            'default_committee_name': '[يكتب هنا اسم اللجنة]',
            'current_week': 1
        }

import uuid
class PointsResult(models.Model):
    """
    حفظ نتائج حساب النقاط مع رابط مشاركة
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="points_results",
        verbose_name="المستخدم",
        null=True,
        blank=True
    )

    # بيانات النتائج (JSON)
    summary_data = models.JSONField(
        default=dict,
        verbose_name="بيانات الملخص"
    )

    # معلومات إضافية
    week_number = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="رقم الأسبوع"
    )
    program_name = models.CharField(
        max_length=200,
        default="عشائر آل سلطان",
        verbose_name="اسم البرنامج"
    )

    # رابط المشاركة
    share_url = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="رابط المشاركة"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاريخ انتهاء الصلاحية"
    )

    # صور الطلاب (مستقبلاً) - JSON يحفظ {student_name: image_url}
    student_images = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="صور الطلاب",
        help_text="قاموس يحفظ صور الطلاب: {'اسم الطالب': 'رابط الصورة'}"
    )

    class Meta:
        verbose_name = 'نتيجة حساب النقاط'
        verbose_name_plural = 'نتائج حساب النقاط'
        ordering = ['-created_at']

    def __str__(self):
        return f"نتيجة {self.program_name} - الأسبوع {self.week_number or 'غير محدد'}"

    def save(self, *args, **kwargs):
        if not self.share_url:
            self.share_url = str(self.id)
        super().save(*args, **kwargs)