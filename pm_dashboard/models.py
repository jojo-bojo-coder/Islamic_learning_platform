from django.db import models
from accounts.models import User
from director_dashboard.models import Program, Committee, Student
from datetime import timedelta


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

    RECURRENCE_PATTERNS = [
        ('daily', 'يومي'),
        ('weekly', 'أسبوعي'),
        ('custom', 'مخصص'),
    ]

    title = models.CharField(max_length=255, verbose_name='عنوان المهمة')
    description = models.TextField(verbose_name='الوصف')
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='tasks')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    # Date fields
    due_date = models.DateField(verbose_name='تاريخ الاستحقاق')
    start_date = models.DateField(verbose_name='تاريخ البداية', null=True, blank=True)

    # Recurrence fields
    is_recurring = models.BooleanField(default=False, verbose_name='مهمة متكررة')
    recurrence_pattern = models.CharField(max_length=20, choices=RECURRENCE_PATTERNS, null=True, blank=True,
                                          verbose_name='نمط التكرار')
    recurrence_days = models.JSONField(null=True, blank=True, verbose_name='أيام التكرار')  # [0,1,2] for Sun, Mon, Tue
    recurrence_end_date = models.DateField(null=True, blank=True, verbose_name='تاريخ انتهاء التكرار')

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

    @property
    def completion_percentage(self):
        """Calculate completion percentage for consistency with other task models"""
        if self.status == 'completed':
            return 100
        elif self.status == 'pending':
            return 50
        else:  # overdue
            return 0

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
