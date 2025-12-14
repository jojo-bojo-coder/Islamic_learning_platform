from django.db import models
from accounts.models import User
from director_dashboard.models import Program, Committee
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from datetime import timedelta


class CulturalTask(models.Model):
    """Model representing a cultural committee task"""

    TASK_TYPE_CHOICES = [
        ('event', 'فعالية ثقافية'),
        ('workshop', 'ورشة عمل'),
        ('lecture', 'محاضرة'),
        ('competition', 'مسابقة'),
        ('exhibition', 'معرض'),
        ('activity', 'نشاط'),
        ('other', 'أخرى'),
    ]

    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'منخفضة'),
        ('medium', 'متوسطة'),
        ('high', 'عالية'),
    ]

    RECURRENCE_PATTERNS = [
        ('daily', 'يومي'),
        ('weekly', 'أسبوعي'),
        ('custom', 'مخصص'),
    ]

    committee = models.ForeignKey(
        Committee,
        on_delete=models.CASCADE,
        related_name='cultural_tasks',
        verbose_name=_('اللجنة الثقافية')
    )

    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPE_CHOICES,
        verbose_name=_('نوع المهمة')
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_('عنوان المهمة')
    )

    description = models.TextField(
        verbose_name=_('وصف المهمة')
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('الحالة')
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name=_('الأولوية')
    )

    assigned_to_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('اسم المسؤول')
    )

    due_date = models.DateField(
        verbose_name=_('تاريخ الاستحقاق')
    )

    start_date = models.DateField(
        verbose_name=_('تاريخ البداية'),
        null=True,
        blank=True
    )

    # Recurrence fields
    is_recurring = models.BooleanField(
        default=False,
        verbose_name=_('مهمة متكررة')
    )

    recurrence_pattern = models.CharField(
        max_length=20,
        choices=RECURRENCE_PATTERNS,
        null=True,
        blank=True,
        verbose_name=_('نمط التكرار')
    )

    recurrence_days = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('أيام التكرار')
    )  # [0,1,2] for Sun, Mon, Tue in Arabic calendar display

    recurrence_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('تاريخ انتهاء التكرار')
    )

    completion_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name=_('نسبة الإنجاز'),
        help_text=_('أدخل رقماً بين 0 و 100')
    )

    has_sessions = models.BooleanField(
        default=False,
        verbose_name=_('يحتوي على جلسات')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('تاريخ التحديث')
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_cultural_tasks',
        verbose_name=_('تم الإنشاء بواسطة')
    )

    class Meta:
        verbose_name = _('مهمة ثقافية')
        verbose_name_plural = _('المهام الثقافية')
        ordering = ['-created_at']

    def __str__(self):
        recurrence = " (متكررة)" if self.is_recurring else ""
        return f"{self.title} - {self.get_task_type_display()}{recurrence}"

    @property
    def is_overdue(self):
        """Check if task is overdue"""
        from django.utils import timezone
        return self.due_date < timezone.now().date() and self.status not in ['completed', 'cancelled']

    @property
    def sessions_count(self):
        """Get the number of sessions associated with this task"""
        return self.sessions.count()

    def get_occurrence_dates(self, start_date=None, end_date=None):
        """
        Get all dates when this task occurs within the given range.
        Returns a list of date objects.
        """
        if not self.is_recurring:
            return [self.start_date or self.due_date]

        dates = []
        current_date = start_date or self.start_date or self.due_date
        end = end_date or self.recurrence_end_date or self.due_date

        # Don't go before start_date
        task_start = self.start_date or self.due_date
        if current_date < task_start:
            current_date = task_start

        # Don't go past recurrence_end_date if set
        if self.recurrence_end_date and end > self.recurrence_end_date:
            end = self.recurrence_end_date

        if self.recurrence_pattern == 'daily':
            # Add every day from start to end
            while current_date <= end:
                dates.append(current_date)
                current_date += timedelta(days=1)

        elif self.recurrence_pattern == 'weekly':
            # Add every 7 days
            while current_date <= end:
                dates.append(current_date)
                current_date += timedelta(days=7)

        elif self.recurrence_pattern == 'custom' and self.recurrence_days:
            # Convert calendar weekdays to Python weekdays
            # Calendar: Sunday=0, Monday=1, ..., Saturday=6
            # Python: Monday=0, Tuesday=1, ..., Sunday=6
            calendar_to_python = {
                0: 6,  # Sunday
                1: 0,  # Monday
                2: 1,  # Tuesday
                3: 2,  # Wednesday
                4: 3,  # Thursday
                5: 4,  # Friday
                6: 5,  # Saturday
            }

            python_weekdays = [calendar_to_python[day] for day in self.recurrence_days if day in calendar_to_python]

            # Add specific weekdays
            while current_date <= end:
                if current_date.weekday() in python_weekdays:
                    dates.append(current_date)
                current_date += timedelta(days=1)

        return dates

    def get_consecutive_day_groups(self, start_date=None, end_date=None):
        """
        Group consecutive days together for display as single badge.
        Returns list of tuples: [(start_date, end_date), ...]
        """
        dates = self.get_occurrence_dates(start_date, end_date)
        if not dates:
            return []

        dates = sorted(dates)
        groups = []
        group_start = dates[0]
        group_end = dates[0]

        for i in range(1, len(dates)):
            if dates[i] == group_end + timedelta(days=1):
                # Consecutive day, extend current group
                group_end = dates[i]
            else:
                # Gap found, save current group and start new one
                groups.append((group_start, group_end))
                group_start = dates[i]
                group_end = dates[i]

        # Add the last group
        groups.append((group_start, group_end))

        return groups

from django.utils import timezone
from datetime import datetime
class TaskSession(models.Model):
    """Model representing a session within a cultural task"""

    task = models.ForeignKey(
        CulturalTask,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('المهمة')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('اسم الجلسة')
    )

    date = models.DateField(
        verbose_name=_('تاريخ الجلسة')
    )

    time = models.TimeField(
        verbose_name=_('وقت الجلسة')
    )

    session_order = models.IntegerField(
        default=1,
        verbose_name=_('ترتيب الجلسة')
    )

    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('مكتملة')
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('ملاحظات')
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('تاريخ الإنشاء')
    )

    class Meta:
        verbose_name = _('جلسة')
        verbose_name_plural = _('الجلسات')
        ordering = ['date', 'time', 'session_order']
        unique_together = ['task', 'session_order']

    def __str__(self):
        return f"{self.name} - {self.date} {self.time}"

    @property
    def is_upcoming(self):
        """Check if session is upcoming"""
        # Make both datetimes timezone-aware
        session_datetime = datetime.combine(self.date, self.time)
        session_datetime = timezone.make_aware(session_datetime)
        return session_datetime > timezone.now() and not self.is_completed

    @property
    def is_past(self):
        """Check if session has passed"""
        # Make both datetimes timezone-aware
        session_datetime = datetime.combine(self.date, self.time)
        session_datetime = timezone.make_aware(session_datetime)
        return session_datetime < timezone.now()


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
    related_daily_phrase = models.ForeignKey('DailyPhrase', on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'إشعار'
        verbose_name_plural = 'الإشعارات'

    def __str__(self):
        return self.title

from django.utils import timezone

class DailyPhrase(models.Model):
    """Phrase of the Day model - Based on days of the week"""

    DAY_CHOICES = [
        ('all', 'جميع الأيام'),
        ('saturday', 'السبت'),
        ('sunday', 'الأحد'),
        ('monday', 'الإثنين'),
        ('tuesday', 'الثلاثاء'),
        ('wednesday', 'الأربعاء'),
        ('thursday', 'الخميس'),
        ('friday', 'الجمعة'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='daily_phrases')
    phrase = models.TextField(verbose_name='العبارة')
    author = models.CharField(max_length=255, blank=True, verbose_name='المؤلف (اختياري)')
    category = models.CharField(max_length=100, blank=True, verbose_name='التصنيف (اختياري)')
    day_of_week = models.CharField(
        max_length=20,
        choices=DAY_CHOICES,
        verbose_name='يوم الأسبوع',
        default='all'
    )
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week']
        verbose_name = 'عبارة اليوم'
        verbose_name_plural = 'عبارات الأسبوع'
        constraints = [
            models.UniqueConstraint(
                fields=['committee', 'day_of_week'],
                name='unique_daily_phrase_per_day'
            )
        ]

    def __str__(self):
        day_name = self.get_day_of_week_display()
        return f"عبارة {day_name}"

    def get_today_phrase():
        """Get today's phrase based on current day of week"""
        from django.utils import timezone
        import datetime

        today = timezone.now().date()
        # Get day name in Arabic matching our choices
        day_mapping = {
            5: 'saturday',  # Monday = 0, Saturday = 5
            6: 'sunday',  # Sunday = 6
            0: 'monday',  # Monday = 0
            1: 'tuesday',  # Tuesday = 1
            2: 'wednesday',  # Wednesday = 2
            3: 'thursday',  # Thursday = 3
            4: 'friday',  # Friday = 4
        }

        current_day = day_mapping.get(today.weekday(), 'all')

        # First try to get phrase for specific day
        phrase = DailyPhrase.objects.filter(
            is_active=True,
            day_of_week=current_day
        ).first()

        # If no specific day phrase, get the "all days" phrase
        if not phrase:
            phrase = DailyPhrase.objects.filter(
                is_active=True,
                day_of_week='all'
            ).first()

        return phrase

    @property
    def is_today_phrase(self):
        """Check if this phrase should be displayed today"""
        from django.utils import timezone
        import datetime

        today = timezone.now().date()
        day_mapping = {
            5: 'saturday',
            6: 'sunday',
            0: 'monday',
            1: 'tuesday',
            2: 'wednesday',
            3: 'thursday',
            4: 'friday',
        }

        current_day = day_mapping.get(today.weekday(), 'all')

        # If phrase is for all days or matches today's day
        return self.day_of_week == 'all' or self.day_of_week == current_day