from django import forms
from django.utils import timezone
from .models import (ScientificTask, ScientificMember, ScientificFile,
                     Lecture, LectureAttendance, ScientificReport)
from accounts.models import User


class ScientificTaskForm(forms.ModelForm):
    class Meta:
        model = ScientificTask
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




class ScientificMemberForm(forms.ModelForm):
    class Meta:
        model = ScientificMember
        fields = ['user', 'role', 'specialization', 'is_active', 'participation_score']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'role': forms.Select(attrs={
                'class': 'form-select'
            }),
            'specialization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: الفقه الإسلامي'
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
            'specialization': 'التخصص',
            'is_active': 'نشط',
            'participation_score': 'درجة المشاركة',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)

        if committee:
            existing_members = ScientificMember.objects.filter(
                committee=committee
            ).values_list('user', flat=True)
            self.fields['user'].queryset = User.objects.filter(
                role='student'
            ).exclude(id__in=existing_members)


class ScientificFileForm(forms.ModelForm):
    class Meta:
        model = ScientificFile
        fields = ['file_type', 'title', 'description', 'author', 'file']
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
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المؤلف'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'file_type': 'نوع الملف',
            'title': 'العنوان',
            'description': 'الوصف',
            'author': 'المؤلف',
            'file': 'الملف',
        }


class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = ['lecture_type', 'title', 'description', 'lecturer', 'guest_lecturer',
                  'date', 'time', 'location', 'duration_minutes', 'status']
        widgets = {
            'lecture_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان المحاضرة'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف المحاضرة',
                'rows': 4
            }),
            'lecturer': forms.Select(attrs={
                'class': 'form-select'
            }),
            'guest_lecturer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المحاضر الضيف (اختياري)'
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
                'placeholder': 'مكان المحاضرة'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '15',
                'step': '15',
                'placeholder': '60'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'lecture_type': 'نوع المحاضرة',
            'title': 'العنوان',
            'description': 'الوصف',
            'lecturer': 'المحاضر',
            'guest_lecturer': 'محاضر ضيف',
            'date': 'التاريخ',
            'time': 'الوقت',
            'location': 'المكان',
            'duration_minutes': 'المدة (بالدقائق)',
            'status': 'الحالة',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)

        if committee:
            lecturer_users = ScientificMember.objects.filter(
                committee=committee,
                role='lecturer',
                is_active=True
            ).values_list('user', flat=True)
            self.fields['lecturer'].queryset = User.objects.filter(id__in=lecturer_users)


class LectureAttendanceForm(forms.ModelForm):
    class Meta:
        model = LectureAttendance
        fields = ['attended', 'notes', 'rating']
        widgets = {
            'attended': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل ملاحظات حول الحضور',
                'rows': 3
            }),
            'rating': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5',
                'placeholder': 'من 1 إلى 5'
            }),
        }
        labels = {
            'attended': 'حضر',
            'notes': 'ملاحظات',
            'rating': 'التقييم',
        }


class ScientificReportForm(forms.ModelForm):
    class Meta:
        model = ScientificReport
        fields = ['report_type', 'title', 'content', 'attendance_rate', 'evaluation_score', 'file']
        widgets = {
            'report_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان التقرير'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل محتوى التقرير',
                'rows': 8
            }),
            'attendance_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': 'نسبة الحضور %'
            }),
            'evaluation_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '5',
                'step': '0.1',
                'placeholder': 'من 1 إلى 5'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'report_type': 'نوع التقرير',
            'title': 'عنوان التقرير',
            'content': 'المحتوى',
            'attendance_rate': 'نسبة الحضور (%)',
            'evaluation_score': 'درجة التقييم',
            'file': 'ملف مرفق (اختياري)',
        }