from django import forms
from django.utils import timezone
from .models import (CulturalTask, CommitteeMember, FileLibrary,
                     Discussion, DiscussionComment, CulturalReport,DailyPhrase,TaskSession)
from accounts.models import User


class CulturalTaskForm(forms.ModelForm):
    """Form for creating and editing cultural tasks"""

    class Meta:
        model = CulturalTask
        fields = [
            'task_type',
            'title',
            'description',
            'status',
            'assigned_to_name',
            'due_date',
            'completion_percentage',
        ]
        widgets = {
            'task_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان المهمة',
                'required': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصفاً تفصيلياً للمهمة',
                'rows': 5,
                'required': True,
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'assigned_to_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الشخص المسؤول عن المهمة',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'completion_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'value': 0,
                'required': True,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Customize field labels
        self.fields['task_type'].label = 'نوع المهمة'
        self.fields['title'].label = 'عنوان المهمة'
        self.fields['description'].label = 'وصف المهمة'
        self.fields['status'].label = 'حالة المهمة'
        self.fields['assigned_to_name'].label = 'المسؤول عن المهمة'
        self.fields['due_date'].label = 'تاريخ الاستحقاق'
        self.fields['completion_percentage'].label = 'نسبة الإنجاز (%)'

    def clean_completion_percentage(self):
        """Validate completion percentage"""
        percentage = self.cleaned_data.get('completion_percentage')
        if percentage < 0 or percentage > 100:
            raise forms.ValidationError(_('يجب أن تكون نسبة الإنجاز بين 0 و 100'))
        return percentage


class TaskSessionForm(forms.ModelForm):
    """Form for individual task sessions"""

    class Meta:
        model = TaskSession
        fields = ['name', 'date', 'time', 'session_order', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: محاضرة تعريفية، ورشة عمل، ندوة...',
                'required': True,
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True,
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True,
            }),
            'session_order': forms.HiddenInput(),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'ملاحظات إضافية (اختياري)',
                'rows': 3,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].label = 'اسم الجلسة'
        self.fields['date'].label = 'تاريخ الجلسة'
        self.fields['time'].label = 'وقت الجلسة'
        self.fields['notes'].label = 'ملاحظات'
        self.fields['notes'].required = False



class CommitteeMemberForm(forms.ModelForm):
    class Meta:
        model = CommitteeMember
        fields = ['user', 'role', 'is_active']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'role': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'مثال: منسق المسابقات'
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
            existing_members = CommitteeMember.objects.filter(
                committee=committee
            ).values_list('user', flat=True)
            self.fields['user'].queryset = User.objects.filter(
                role='student'
            ).exclude(id__in=existing_members)


class FileLibraryForm(forms.ModelForm):
    class Meta:
        model = FileLibrary
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


class DiscussionForm(forms.ModelForm):
    class Meta:
        model = Discussion
        fields = ['title', 'content', 'is_pinned', 'is_public_to_all_supervisors']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان النقاش'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل محتوى النقاش',
                'rows': 6
            }),
            'is_pinned': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'is_public_to_all_supervisors': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'id': 'is_public_to_all_supervisors'
            }),
        }
        labels = {
            'title': 'العنوان',
            'content': 'المحتوى',
            'is_pinned': 'تثبيت النقاش',
            'is_public_to_all_supervisors': 'مشترك بين جميع المشرفين والمديرين',
        }


class DiscussionCommentForm(forms.ModelForm):
    class Meta:
        model = DiscussionComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'اكتب تعليقك هنا...',
                'rows': 3
            }),
        }
        labels = {
            'content': 'التعليق',
        }


class CulturalReportForm(forms.ModelForm):
    class Meta:
        model = CulturalReport
        fields = ['title', 'report_type', 'content', 'file']
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
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'عنوان التقرير',
            'report_type': 'نوع التقرير',
            'content': 'المحتوى',
            'file': 'ملف مرفق (اختياري)',
        }

class DailyPhraseForm(forms.ModelForm):
    class Meta:
        model = DailyPhrase
        fields = ['phrase', 'author', 'category', 'display_date', 'is_active']
        widgets = {
            'phrase': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عبارة اليوم...',
                'rows': 4
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم المؤلف (اختياري)'
            }),
            'category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'التصنيف (اختياري)'
            }),
            'display_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'phrase': 'العبارة',
            'author': 'المؤلف',
            'category': 'التصنيف',
            'display_date': 'تاريخ العرض',
            'is_active': 'نشط',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set minimum date to today
        self.fields['display_date'].widget.attrs['min'] = timezone.now().date().isoformat()
        self.fields['author'].required = False
        self.fields['category'].required = False