from django import forms
from django.utils import timezone
from .models import (OperationsTask, OperationsTeamMember, LogisticsResource,
                     OperationsFileLibrary, OperationsWeeklyReport)
from accounts.models import User


class OperationsTaskForm(forms.ModelForm):
    class Meta:
        model = OperationsTask
        fields = ['task_type', 'title', 'description', 'assigned_to_name',
                  'due_date', 'status', 'priority', 'completion_percentage']
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
            'priority': forms.Select(attrs={
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
            'due_date': 'الموعد النهائي',
            'status': 'الحالة',
            'priority': 'الأولوية',
            'completion_percentage': 'نسبة الإنجاز',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)
        self.fields['assigned_to_name'].required = False



class OperationsTeamMemberForm(forms.ModelForm):
    class Meta:
        model = OperationsTeamMember
        fields = ['user', 'role', 'is_active']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: منسق الجوائز'
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

        if committee:
            # Show only students not already in this committee
            existing_members = OperationsTeamMember.objects.filter(
                committee=committee
            ).values_list('user', flat=True)
            self.fields['user'].queryset = User.objects.filter(
                role='student'
            ).exclude(id__in=existing_members)


class LogisticsResourceForm(forms.ModelForm):
    class Meta:
        model = LogisticsResource
        fields = ['resource_type', 'name', 'description', 'quantity', 'status', 'location', 'notes']
        widgets = {
            'resource_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم المورد'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف المورد',
                'rows': 3
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل موقع المورد'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'ملاحظات إضافية',
                'rows': 3
            }),
        }
        labels = {
            'resource_type': 'نوع المورد',
            'name': 'الاسم',
            'description': 'الوصف',
            'quantity': 'الكمية',
            'status': 'الحالة',
            'location': 'الموقع',
            'notes': 'ملاحظات',
        }


class OperationsFileLibraryForm(forms.ModelForm):
    class Meta:
        model = OperationsFileLibrary
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


class OperationsWeeklyReportForm(forms.ModelForm):
    class Meta:
        model = OperationsWeeklyReport
        fields = ['week_start_date', 'week_end_date', 'achievements', 'challenges',
                  'completion_rate', 'tasks_completed', 'tasks_pending', 'notes']
        widgets = {
            'week_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'week_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'achievements': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'اذكر الإنجازات المحققة خلال الأسبوع',
                'rows': 5
            }),
            'challenges': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'اذكر التحديات والصعوبات التي واجهتها',
                'rows': 5
            }),
            'completion_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100'
            }),
            'tasks_completed': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'tasks_pending': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'ملاحظات إضافية',
                'rows': 3
            }),
        }
        labels = {
            'week_start_date': 'بداية الأسبوع',
            'week_end_date': 'نهاية الأسبوع',
            'achievements': 'الإنجازات',
            'challenges': 'التحديات',
            'completion_rate': 'نسبة الإنجاز %',
            'tasks_completed': 'المهام المكتملة',
            'tasks_pending': 'المهام المعلقة',
            'notes': 'ملاحظات إضافية',
        }