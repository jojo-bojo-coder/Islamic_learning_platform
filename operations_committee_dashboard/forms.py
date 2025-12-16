from django import forms
from django.utils import timezone
from .models import (OperationsTask, OperationsTeamMember, LogisticsResource,
                     OperationsFileLibrary, OperationsWeeklyReport)
from accounts.models import User


class OperationsTaskForm(forms.ModelForm):
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
            (0, 'الأحد'),
            (1, 'الاثنين'),
            (2, 'الثلاثاء'),
            (3, 'الأربعاء'),
            (4, 'الخميس'),
            (5, 'الجمعة'),
            (6, 'السبت'),
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
        model = OperationsTask
        fields = ['task_type', 'title', 'description', 'assigned_to_name',
                  'start_date', 'due_date', 'status', 'priority', 'completion_percentage',
                  'is_recurring', 'recurrence_pattern', 'recurrence_days', 'recurrence_end_date']
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
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'id': 'id_start_date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'min': timezone.now().date().isoformat(),
                'id': 'id_due_date'
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
            'start_date': 'تاريخ البداية',
            'due_date': 'الموعد النهائي',
            'status': 'الحالة',
            'priority': 'الأولوية',
            'completion_percentage': 'نسبة الإنجاز',
            'is_recurring': 'مهمة متكررة',
            'recurrence_pattern': 'نمط التكرار',
            'recurrence_days': 'أيام التكرار',
            'recurrence_end_date': 'تاريخ انتهاء التكرار',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)

        if not self.instance.pk:  # New task
            self.fields['start_date'].initial = timezone.now().date()
            self.fields['due_date'].initial = timezone.now().date()

        self.fields['assigned_to_name'].required = False

    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get('is_recurring')
        start_date = cleaned_data.get('start_date')
        due_date = cleaned_data.get('due_date')

        # Validate start_date and due_date
        if start_date and due_date:
            if start_date > due_date:
                raise forms.ValidationError('تاريخ البداية يجب أن يكون قبل الموعد النهائي')

        # Set start_date to due_date if not provided
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