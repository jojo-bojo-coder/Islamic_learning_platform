from django import forms
from django.utils import timezone
from .models import (SportsTask, SportsMember, SportsFile, Match, SportsReport)
from accounts.models import User


class SportsTaskForm(forms.ModelForm):
    is_recurring = forms.BooleanField(
        required=False,
        label='مهمة متكررة',
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
        label='نمط التكرار',
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
        label='أيام التكرار',
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input day-checkbox',
        })
    )

    recurrence_end_date = forms.DateField(
        required=False,
        label='تاريخ انتهاء التكرار',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_recurrence_end_date'
        })
    )

    class Meta:
        model = SportsTask
        fields = [
            'task_type', 'title', 'description', 'priority',
            'assigned_to_name', 'start_date', 'due_date', 'status',
            'completion_percentage', 'is_recurring', 'recurrence_pattern',
            'recurrence_days', 'recurrence_end_date'
        ]
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
            'priority': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_priority'
            }),
            'assigned_to_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم المسؤول (اختياري)'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_start_date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_due_date'
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
            'priority': 'الأولوية',
            'assigned_to_name': 'اسم المسؤول (اختياري)',
            'start_date': 'تاريخ البداية',
            'due_date': 'تاريخ الاستحقاق',
            'status': 'الحالة',
            'completion_percentage': 'نسبة الإنجاز (%)',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)
        self.fields['assigned_to_name'].required = False
        self.fields['completion_percentage'].required = False
        self.fields['start_date'].required = False  # Make start_date optional

        # Set min date for due_date
        self.fields['due_date'].widget.attrs['min'] = timezone.now().date().isoformat()

    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get('is_recurring')
        start_date = cleaned_data.get('start_date')
        due_date = cleaned_data.get('due_date')

        # Validate start_date and due_date
        if start_date and due_date:
            if start_date > due_date:
                raise forms.ValidationError('تاريخ البداية يجب أن يكون قبل تاريخ الاستحقاق')

        # Set start_date to due_date if not provided and not recurring
        if not start_date and due_date:
            cleaned_data['start_date'] = due_date

        if is_recurring:
            recurrence_pattern = cleaned_data.get('recurrence_pattern')
            recurrence_days = cleaned_data.get('recurrence_days')
            recurrence_end_date = cleaned_data.get('recurrence_end_date')

            if not recurrence_pattern:
                raise forms.ValidationError('يجب تحديد نمط التكرار للمهام المتكررة')

            if recurrence_pattern == 'custom' and not recurrence_days:
                raise forms.ValidationError('يجب تحديد أيام التكرار للمهام المخصصة')

            if recurrence_end_date:
                if not start_date:
                    raise forms.ValidationError('يجب تحديد تاريخ البداية عند تحديد تاريخ انتهاء التكرار')
                if recurrence_end_date < start_date:
                    raise forms.ValidationError('تاريخ انتهاء التكرار يجب أن يكون بعد تاريخ البداية')

            # Convert recurrence_days to list of integers if custom pattern
            if recurrence_pattern == 'custom' and recurrence_days:
                cleaned_data['recurrence_days'] = [int(day) for day in recurrence_days]
        else:
            # Clear recurrence fields if not recurring
            cleaned_data['recurrence_pattern'] = None
            cleaned_data['recurrence_days'] = None
            cleaned_data['recurrence_end_date'] = None

        return cleaned_data


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