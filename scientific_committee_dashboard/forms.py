from django import forms
from django.utils import timezone
from .models import (ScientificTask, ScientificMember, ScientificFile,
                     Lecture, LectureAttendance, ScientificReport)
from accounts.models import User


class ScientificTaskForm(forms.ModelForm):
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
        model = ScientificTask
        fields = ['task_type', 'title', 'description', 'assigned_to_name','priority',
                  'start_date', 'due_date', 'status', 'completion_percentage',
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
            'priority': 'الأولوية',
            'assigned_to_name': 'اسم المسؤول (اختياري)',
            'start_date': 'تاريخ البداية',
            'due_date': 'تاريخ الاستحقاق',
            'status': 'الحالة',
            'completion_percentage': 'نسبة الإنجاز',
        }

    def __init__(self, *args, **kwargs):
        committee = kwargs.pop('committee', None)
        super().__init__(*args, **kwargs)
        self.fields['assigned_to_name'].required = False

        # Set min date for start_date
        today = timezone.now().date().isoformat()
        self.fields['start_date'].widget.attrs['min'] = today

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




class ScientificMemberForm(forms.ModelForm):
    class Meta:
        model = ScientificMember
        fields = ['user', 'role', 'specialization', 'is_active', 'participation_score']
        widgets = {
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
        instance = kwargs.get('instance')
        super().__init__(*args, **kwargs)

        if instance:
            # في حالة التحرير، إزالة حقل المستخدم من النموذج
            # وسنعرض المعلومات في القالب بدلاً من ذلك
            del self.fields['user']
        elif committee:
            # في حالة الإضافة، احتفظ بالسلوك الأصلي
            existing_members = ScientificMember.objects.filter(
                committee=committee
            ).values_list('user', flat=True)
            self.fields['user'].queryset = User.objects.filter(
                role='student'
            ).exclude(id__in=existing_members)
            self.fields['user'].widget.attrs.update({
                'class': 'form-select'
            })


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