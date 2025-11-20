from django import forms
from django.utils import timezone
from .models import (ShariaTask, ShariaMember, ShariaFile, DailyMessage,
                     FamilyCompetition, YouthBook, ShariaReport)
from accounts.models import User


class ShariaTaskForm(forms.ModelForm):
    class Meta:
        model = ShariaTask
        fields = ['task_type', 'title', 'description', 'assigned_to_name',
                  'due_date', 'status', 'completion_percentage']
        widgets = {
            'task_type': forms.Select(attrs={
                'class': 'form-select',
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان المهمة'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف المهمة',
                'rows': 4
            }),
            'assigned_to_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم المسؤول (اختياري)'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'completion_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '5'
            }),
        }
        labels = {
            'task_type': 'نوع المهمة',
            'title': 'العنوان',
            'description': 'الوصف',
            'assigned_to_name': 'اسم المسؤول (اختياري)',
            'due_date': 'تاريخ الاستحقاق',
            'status': 'الحالة',
            'completion_percentage': 'نسبة الإنجاز',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)
        self.fields['assigned_to_name'].required = False




class ShariaMemberForm(forms.ModelForm):
    class Meta:
        model = ShariaMember
        fields = ['user', 'role', 'is_active']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select',
                'disabled': 'disabled'
            }),
            'role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: مسؤول الدقائق المشرفة'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'user': 'العضو',
            'role': 'الدور',
            'is_active': 'نشط',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)

        # إذا كان النموذج في وضع التعديل (لديه instance)
        if self.instance and self.instance.pk:
            # جعل حقل المستخدم غير قابل للتعديل
            self.fields['user'].disabled = True
            # إضافة نص مساعد للإيضاح
            self.fields['user'].help_text = 'لا يمكن تغيير المستخدم عند التعديل'

        if committee:
            existing_members = ShariaMember.objects.filter(
                committee=committee
            ).values_list('user', flat=True)

            # إذا كان في وضع الإضافة، قم بتصفية المستخدمين
            if not (self.instance and self.instance.pk):
                self.fields['user'].queryset = User.objects.filter(
                    role='student'
                ).exclude(id__in=existing_members)


class ShariaFileForm(forms.ModelForm):
    class Meta:
        model = ShariaFile
        fields = ['file_type', 'title', 'description', 'file']
        widgets = {
            'file_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان الملف'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف الملف',
                'rows': 3
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'file_type': 'نوع الملف',
            'title': 'العنوان',
            'description': 'الوصف',
            'file': 'الملف',
        }


class DailyMessageForm(forms.ModelForm):
    class Meta:
        model = DailyMessage
        fields = ['message_type', 'title', 'content', 'scheduled_date']
        widgets = {
            'message_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان الرسالة'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل محتوى الرسالة',
                'rows': 6
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
        }
        labels = {
            'message_type': 'نوع الرسالة',
            'title': 'العنوان',
            'content': 'المحتوى',
            'scheduled_date': 'تاريخ الإرسال',
        }


class FamilyCompetitionForm(forms.ModelForm):
    class Meta:
        model = FamilyCompetition
        fields = ['title', 'description', 'start_date', 'end_date', 'status', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان المسابقة'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف المسابقة',
                'rows': 5
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'عنوان المسابقة',
            'description': 'الوصف',
            'start_date': 'تاريخ البداية',
            'end_date': 'تاريخ النهاية',
            'status': 'الحالة',
            'file': 'ملف المسابقة',
        }


class YouthBookForm(forms.ModelForm):
    class Meta:
        model = YouthBook
        fields = ['title', 'author', 'description', 'assigned_to', 'status',
                  'progress_percentage', 'start_date', 'completion_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان الكتاب'
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم المؤلف'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف الكتاب',
                'rows': 3
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'progress_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '5'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'completion_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'title': 'عنوان الكتاب',
            'author': 'المؤلف',
            'description': 'الوصف',
            'assigned_to': 'مكلف به',
            'status': 'الحالة',
            'progress_percentage': 'نسبة الإنجاز',
            'start_date': 'تاريخ البداية',
            'completion_date': 'تاريخ الإكمال',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)

        if committee:
            member_users = ShariaMember.objects.filter(
                committee=committee,
                is_active=True
            ).values_list('user', flat=True)
            self.fields['assigned_to'].queryset = User.objects.filter(id__in=member_users)


class ShariaReportForm(forms.ModelForm):
    class Meta:
        model = ShariaReport
        fields = ['title', 'report_type', 'content', 'interaction_rate', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان التقرير'
            }),
            'report_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: تقرير شهري'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل محتوى التقرير',
                'rows': 8
            }),
            'interaction_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'عنوان التقرير',
            'report_type': 'نوع التقرير',
            'content': 'المحتوى',
            'interaction_rate': 'نسبة التفاعل (%)',
            'file': 'ملف مرفق (اختياري)',
        }