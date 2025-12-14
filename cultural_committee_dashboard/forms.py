from django import forms
from django.utils import timezone
from .models import (CulturalTask, CommitteeMember, FileLibrary,
                     Discussion, DiscussionComment, CulturalReport,DailyPhrase,TaskSession)
from accounts.models import User
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _


class CulturalTaskForm(forms.ModelForm):
    """Form for creating and editing cultural tasks with recurrence"""

    is_recurring = forms.BooleanField(
        required=False,
        label=_('مهمة متكررة'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_is_recurring'
        })
    )

    recurrence_pattern = forms.ChoiceField(
        choices=[
            ('', 'اختر نمط التكرار'),
            ('daily', 'يومي'),
            ('weekly', 'أسبوعي'),
            ('custom', 'مخصص'),
        ],
        required=False,
        label=_('نمط التكرار'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_recurrence_pattern'
        })
    )

    recurrence_days = forms.MultipleChoiceField(
        choices=[
            (0, 'الأحد'),  # Sunday = 0 in calendar display (6 in Python weekday())
            (1, 'الاثنين'),  # Monday = 1 (0 in Python)
            (2, 'الثلاثاء'),  # Tuesday = 2 (1 in Python)
            (3, 'الأربعاء'),  # Wednesday = 3 (2 in Python)
            (4, 'الخميس'),  # Thursday = 4 (3 in Python)
            (5, 'الجمعة'),  # Friday = 5 (4 in Python)
            (6, 'السبت'),  # Saturday = 6 (5 in Python)
        ],
        required=False,
        label=_('أيام التكرار'),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input day-checkbox',
        })
    )

    recurrence_end_date = forms.DateField(
        required=False,
        label=_('تاريخ انتهاء التكرار'),
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_recurrence_end_date'
        })
    )

    class Meta:
        model = CulturalTask
        fields = [
            'task_type',
            'title',
            'description',
            'status',
            'priority',
            'assigned_to_name',
            'start_date',
            'due_date',
            'completion_percentage',
            'is_recurring',
            'recurrence_pattern',
            'recurrence_days',
            'recurrence_end_date',
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
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'assigned_to_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'اسم الشخص المسؤول عن المهمة',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
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
        self.fields['task_type'].label = _('نوع المهمة')
        self.fields['title'].label = _('عنوان المهمة')
        self.fields['description'].label = _('وصف المهمة')
        self.fields['status'].label = _('حالة المهمة')
        self.fields['priority'].label = _('الأولوية')
        self.fields['assigned_to_name'].label = _('المسؤول عن المهمة')
        self.fields['start_date'].label = _('تاريخ البداية')
        self.fields['due_date'].label = _('تاريخ الاستحقاق')
        self.fields['completion_percentage'].label = _('نسبة الإنجاز (%)')

        # Set initial recurrence_days if editing
        if self.instance and self.instance.pk and self.instance.recurrence_days:
            self.initial['recurrence_days'] = self.instance.recurrence_days

    def clean(self):
        """Validate form data including recurrence"""
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get('is_recurring')
        start_date = cleaned_data.get('start_date')
        due_date = cleaned_data.get('due_date')

        # Validate start_date and due_date
        if start_date and due_date:
            if start_date > due_date:
                raise forms.ValidationError(_('تاريخ البداية يجب أن يكون قبل تاريخ الاستحقاق'))

        # Set start_date to due_date if not provided and not recurring
        if not start_date and due_date:
            cleaned_data['start_date'] = due_date

        if is_recurring:
            recurrence_pattern = cleaned_data.get('recurrence_pattern')
            recurrence_days = cleaned_data.get('recurrence_days')
            recurrence_end_date = cleaned_data.get('recurrence_end_date')

            if not recurrence_pattern:
                raise forms.ValidationError(_('يجب تحديد نمط التكرار للمهام المتكررة'))

            if recurrence_pattern == 'custom' and not recurrence_days:
                raise forms.ValidationError(_('يجب تحديد أيام التكرار للمهام المخصصة'))

            if recurrence_end_date:
                if not start_date:
                    raise forms.ValidationError(_('يجب تحديد تاريخ البداية عند تحديد تاريخ انتهاء التكرار'))
                if recurrence_end_date < start_date:
                    raise forms.ValidationError(_('تاريخ انتهاء التكرار يجب أن يكون بعد تاريخ البداية'))

            # Convert recurrence_days to list of integers if custom pattern
            if recurrence_pattern == 'custom' and recurrence_days:
                cleaned_data['recurrence_days'] = [int(day) for day in recurrence_days]
        else:
            # Clear recurrence fields if not recurring
            cleaned_data['recurrence_pattern'] = None
            cleaned_data['recurrence_days'] = None
            cleaned_data['recurrence_end_date'] = None

        return cleaned_data

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
    """Form for creating and editing daily phrases by day of week"""

    class Meta:
        model = DailyPhrase
        fields = ['phrase', 'author', 'category', 'day_of_week', 'is_active']
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
            'day_of_week': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'phrase': 'العبارة',
            'author': 'المؤلف',
            'category': 'التصنيف',
            'day_of_week': 'يوم الأسبوع',
            'is_active': 'نشط',
        }

    def __init__(self, *args, **kwargs):
        self.committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)

        self.fields['author'].required = False
        self.fields['category'].required = False

        # Disable day_of_week field if editing and it's "all"
        if self.instance and self.instance.pk and self.instance.day_of_week == 'all':
            self.fields['day_of_week'].disabled = True
            self.fields['day_of_week'].help_text = 'لا يمكن تغيير "جميع الأيام" بعد الإنشاء'

    def clean(self):
        """Validate that only one phrase per day exists"""
        cleaned_data = super().clean()
        day_of_week = cleaned_data.get('day_of_week')

        if self.committee and day_of_week:
            # Check if there's already a phrase for this day
            existing_phrase = DailyPhrase.objects.filter(
                committee=self.committee,
                day_of_week=day_of_week
            ).exclude(pk=self.instance.pk if self.instance else None)

            if existing_phrase.exists():
                day_name = dict(DailyPhrase.DAY_CHOICES)[day_of_week]
                raise forms.ValidationError(f'يوجد بالفعل عبارة ليوم {day_name}')

        return cleaned_data