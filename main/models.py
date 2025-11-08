from django.db import models
from accounts.models import User
from director_dashboard.models import Program, Committee
from django.utils import timezone

from django.db.models.signals import post_save
from django.dispatch import receiver
class ScheduleEvent(models.Model):
    """Combined model for tasks and activities in the schedule"""
    EVENT_TYPES = [
        ('task', 'مهمة'),
        ('activity', 'نشاط'),
        ('meeting', 'اجتماع'),
        ('exam', 'اختبار'),
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

    # Basic Info
    title = models.CharField(max_length=255, verbose_name='العنوان')
    description = models.TextField(verbose_name='الوصف')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name='نوع الحدث')

    # Program and Committee
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='schedule_events')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='schedule_events', verbose_name='اللجنة')

    # Date and Time
    start_date = models.DateField(verbose_name='تاريخ البداية')
    end_date = models.DateField(null=True, blank=True, verbose_name='تاريخ النهاية')
    start_time = models.TimeField(null=True, blank=True, verbose_name='وقت البداية')
    end_time = models.TimeField(null=True, blank=True, verbose_name='وقت النهاية')

    # Status and Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='الحالة')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium', verbose_name='الأولوية')

    # Location
    location = models.CharField(max_length=255, blank=True, verbose_name='المكان')

    # Participants
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='assigned_events', verbose_name='المسؤول')
    participants = models.ManyToManyField(User, blank=True, related_name='participating_events',
                                          verbose_name='المشاركون')

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                   related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Color coding for calendar
    color = models.CharField(max_length=7, default='#86B817', verbose_name='اللون')

    class Meta:
        ordering = ['start_date', 'start_time']
        verbose_name = 'حدث جدولة'
        verbose_name_plural = 'أحداث الجدولة'

    def __str__(self):
        return f"{self.title} - {self.start_date}"

    @property
    def is_past(self):
        return self.start_date < timezone.now().date()

    @property
    def is_today(self):
        return self.start_date == timezone.now().date()

    @property
    def duration_days(self):
        if self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 1





class EventAttendance(models.Model):
    """Track attendance for events"""
    event = models.ForeignKey(ScheduleEvent, on_delete=models.CASCADE, related_name='attendances')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_attendances')
    attended = models.BooleanField(default=False, verbose_name='حضر')
    notes = models.TextField(blank=True, verbose_name='ملاحظات')
    recorded_at = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                    related_name='recorded_attendances')

    class Meta:
        unique_together = ['event', 'user']
        verbose_name = 'حضور حدث'
        verbose_name_plural = 'حضور الأحداث'

    def __str__(self):
        return f"{self.user} - {self.event.title}"