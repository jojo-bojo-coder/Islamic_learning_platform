from django import forms
from django.utils import timezone
from .models import (SportsTask, SportsMember, SportsFile, Match, SportsReport)
from accounts.models import User


class SportsTaskForm(forms.ModelForm):
    class Meta:
        model = SportsTask
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


class SportsMemberForm(forms.ModelForm):
    class Meta:
        model = SportsMember
        fields = ['user', 'role', 'is_active', 'participation_score']  # Added participation_score
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'participation_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100'
            }),
        }
        labels = {
            'user': 'العضو',
            'role': 'الدور',
            'is_active': 'نشط',
            'participation_score': 'درجة المشاركة',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)

        if committee:
            # Show only students not already in this committee
            existing_members = SportsMember.objects.filter(
                committee=committee
            ).values_list('user', flat=True)
            self.fields['user'].queryset = User.objects.filter(
                role='student'
            ).exclude(id__in=existing_members)


class SportsFileForm(forms.ModelForm):
    class Meta:
        model = SportsFile
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


class MatchForm(forms.ModelForm):
    class Meta:
        model = Match
        fields = ['match_type', 'title', 'team1', 'team2', 'date', 'time',
                  'location', 'referee_name', 'status', 'team1_score', 'team2_score']
        widgets = {
            'match_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان المباراة'
            }),
            'team1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الفريق الأول'
            }),
            'team2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الفريق الثاني'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat()
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مكان المباراة'
            }),
            'referee_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم الحكم (اختياري)'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'team1_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'team2_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }
        labels = {
            'match_type': 'نوع المباراة',
            'title': 'العنوان',
            'team1': 'الفريق الأول',
            'team2': 'الفريق الثاني',
            'date': 'التاريخ',
            'time': 'الوقت',
            'location': 'المكان',
            'referee_name': 'اسم الحكم (اختياري)',
            'status': 'الحالة',
            'team1_score': 'نتيجة الفريق الأول',
            'team2_score': 'نتيجة الفريق الثاني',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)
        self.fields['referee_name'].required = False




class SportsReportForm(forms.ModelForm):
    class Meta:
        model = SportsReport
        fields = ['title', 'week_start', 'week_end', 'content', 'participation_rate', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان التقرير'
            }),
            'week_start': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'week_end': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل محتوى التقرير',
                'rows': 8
            }),
            'participation_rate': forms.NumberInput(attrs={
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
            'week_start': 'بداية الأسبوع',
            'week_end': 'نهاية الأسبوع',
            'content': 'المحتوى',
            'participation_rate': 'نسبة المشاركة (%)',
            'file': 'ملف مرفق (اختياري)',
        }