from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('director', 'مدير النظام'),
        ('program_manager', 'مدير برنامج'),
        ('committee_supervisor', 'مشرف لجنة'),
        ('student', 'طالب/عضو'),
    ]

    SUPERVISOR_TYPE_CHOICES = [
        ('cultural', 'مشرف لجنة ثقافية'),
        ('sports', 'مشرف لجنة رياضية'),
        ('sharia', 'مشرف اللجنة الشرعية'),
        ('scientific', 'مشرف اللجنة العلمية'),
        ('operations', 'مشرف اللجنة التشغيلية'),
        ('', 'غير محدد'),
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='student')
    supervisor_type = models.CharField(
        max_length=20,
        choices=SUPERVISOR_TYPE_CHOICES,
        blank=True,
        verbose_name='نوع المشرف'
    )
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "User Activities"

    def __str__(self):
        return f"{self.user.username} - {self.action}"


class ProgramSupervisor(models.Model):
    program = models.ForeignKey('director_dashboard.Program', on_delete=models.CASCADE)
    supervisor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'committee_supervisor'})
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_supervisors')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['program', 'supervisor']
        verbose_name = 'مشرف برنامج'
        verbose_name_plural = 'مشرفي البرامج'

    def __str__(self):
        return f"{self.supervisor} - {self.program}"


from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.username}"

    class Meta:
        verbose_name = 'رمز إعادة تعيين كلمة المرور'
        verbose_name_plural = 'رموز إعادة تعيين كلمة المرور'