from django.db import models
from accounts.models import User
from director_dashboard.models import Program, Committee
from datetime import timedelta

class SportsTask(models.Model):
    """Main sports tasks for the committee"""
    TASK_TYPES = [
        ('football_volleyball', 'دوري القدم والطائرة'),
        ('sports_programs', 'البرامج الرياضية والمسابقات الحركية'),
        ('hall_meetings', 'متابعة لقاءات الصالة'),
        ('table_tennis', 'دوري تنس الطاولة'),
        ('playstation', 'دوري البلايستيشن'),
        ('intelligence_games', 'متابعة ألعاب الذكاء'),
        ('other', 'أخرى'),
    ]

    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('in_progress', 'جاري العمل'),
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

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sports_tasks')
    task_type = models.CharField(max_length=50, choices=TASK_TYPES, verbose_name='نوع المهمة')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(verbose_name='الوصف')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium',
                                verbose_name='الأولوية')  # NEW
    assigned_to_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='اسم المسؤول'
    )

    due_date = models.DateField(verbose_name='تاريخ الاستحقاق')
    start_date = models.DateField(verbose_name='تاريخ البداية', null=True, blank=True)  # NEW

    is_recurring = models.BooleanField(default=False, verbose_name='مهمة متكررة')
    recurrence_pattern = models.CharField(
        max_length=20,
        choices=RECURRENCE_PATTERNS,
        null=True,
        blank=True,
        verbose_name='نمط التكرار'
    )
    recurrence_days = models.JSONField(null=True, blank=True, verbose_name='أيام التكرار')
    recurrence_end_date = models.DateField(null=True, blank=True, verbose_name='تاريخ انتهاء التكرار')

    completion_percentage = models.IntegerField(default=0, verbose_name='نسبة الإنجاز')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='sports_tasks_created')

    from_program_manager = models.BooleanField(default=False, verbose_name='من مدير البرنامج')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'مهمة رياضية'
        verbose_name_plural = 'المهام الرياضية'

    def __str__(self):
        return self.title

    @property
    def get_assigned_to_display(self):
        if self.assigned_to_name:
            return self.assigned_to_name
        elif self.assigned_to:
            return self.assigned_to.get_full_name()
        return "غير محدد"

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status not in ['completed', 'cancelled'] and self.due_date < timezone.now().date():
            return True
        return False

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


class SportsMember(models.Model):
    """Members of the sports committee"""
    ROLE_CHOICES = [
        ('referee', 'حكم'),
        ('coordinator', 'منسق'),
        ('responsible_player', 'لاعب مسؤول'),
        ('player', 'لاعب'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sports_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sports_memberships')
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, verbose_name='الدور')
    joined_date = models.DateField(auto_now_add=True, verbose_name='تاريخ الانضمام')
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    participation_score = models.IntegerField(default=0, verbose_name='درجة المشاركة')

    class Meta:
        unique_together = ['committee', 'user']
        verbose_name = 'عضو اللجنة الرياضية'
        verbose_name_plural = 'أعضاء اللجنة الرياضية'

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_role_display()}"


class SportsFile(models.Model):
    """Library for sports files"""
    FILE_TYPES = [
        ('match_schedule', 'جدول مباريات'),
        ('results', 'نتائج'),
        ('activity_photos', 'صور الأنشطة'),
        ('other', 'أخرى'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sports_files')
    file_type = models.CharField(max_length=50, choices=FILE_TYPES, verbose_name='نوع الملف')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(blank=True, verbose_name='الوصف')
    file = models.FileField(upload_to='sports_files/%Y/%m/', verbose_name='الملف')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'ملف رياضي'
        verbose_name_plural = 'مكتبة الملفات الرياضية'

    def __str__(self):
        return self.title


class Match(models.Model):
    """Sports matches/games"""
    MATCH_TYPES = [
        ('football', 'كرة قدم'),
        ('volleyball', 'كرة طائرة'),
        ('table_tennis', 'تنس طاولة'),
        ('playstation', 'بلايستيشن'),
        ('intelligence_game', 'لعبة ذكاء'),
        ('other', 'أخرى'),
    ]

    STATUS_CHOICES = [
        ('scheduled', 'مجدولة'),
        ('ongoing', 'جارية'),
        ('completed', 'مكتملة'),
        ('cancelled', 'ملغاة'),
    ]

    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='matches')
    match_type = models.CharField(max_length=50, choices=MATCH_TYPES, verbose_name='نوع المباراة')
    title = models.CharField(max_length=255, verbose_name='العنوان')
    team1 = models.CharField(max_length=100, verbose_name='الفريق الأول')
    team2 = models.CharField(max_length=100, verbose_name='الفريق الثاني')
    date = models.DateField(verbose_name='التاريخ')
    time = models.TimeField(verbose_name='الوقت')
    location = models.CharField(max_length=255, verbose_name='المكان')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name='الحالة')
    team1_score = models.IntegerField(null=True, blank=True, verbose_name='نتيجة الفريق الأول')
    team2_score = models.IntegerField(null=True, blank=True, verbose_name='نتيجة الفريق الثاني')
    referee_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='اسم الحكم'
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'مباراة'
        verbose_name_plural = 'المباريات'

    def __str__(self):
        return f"{self.title} - {self.team1} vs {self.team2}"

    @property
    def get_referee_display(self):
        if self.referee_name:
            return self.referee_name
        elif self.referee:
            return self.referee.get_full_name()
        return "غير محدد"


class SportsReport(models.Model):
    """Weekly sports reports"""
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sports_reports')
    title = models.CharField(max_length=255, verbose_name='عنوان التقرير')
    week_start = models.DateField(verbose_name='بداية الأسبوع')
    week_end = models.DateField(verbose_name='نهاية الأسبوع')
    content = models.TextField(verbose_name='المحتوى')
    participation_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='نسبة المشاركة')
    file = models.FileField(upload_to='sports_reports/%Y/%m/', blank=True, null=True, verbose_name='ملف مرفق')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'تقرير رياضي'
        verbose_name_plural = 'التقارير الرياضية'

    def __str__(self):
        return self.title


class SportsNotification(models.Model):
    """Notifications for sports committee"""
    NOTIFICATION_TYPES = [
        ('match_scheduled', 'مباراة مجدولة'),
        ('results_uploaded', 'رفع النتائج'),
        ('task_added', 'إضافة مهمة'),
        ('task_updated', 'تعديل مهمة'),
        ('report_uploaded', 'رفع تقرير'),
        ('discussion_created', 'نقاش جديد'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sports_notifications')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='sports_notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_task = models.ForeignKey(SportsTask, on_delete=models.CASCADE, null=True, blank=True)
    related_match = models.ForeignKey(Match, on_delete=models.CASCADE, null=True, blank=True)
    related_report = models.ForeignKey(SportsReport, on_delete=models.CASCADE, null=True, blank=True)
    related_discussion = models.ForeignKey('cultural_committee_dashboard.Discussion', on_delete=models.CASCADE,
                                           null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'إشعار رياضي'
        verbose_name_plural = 'الإشعارات الرياضية'

    def __str__(self):
        return self.title
