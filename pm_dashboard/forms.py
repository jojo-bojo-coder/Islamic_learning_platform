from django import forms
from django.utils import timezone
from director_dashboard.models import Committee, Program
from accounts.models import User
from .models import Task, Activity, StudentAttendance


class CommitteeForm(forms.ModelForm):
    class Meta:
        model = Committee
        fields = ['name', 'supervisor', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم اللجنة'
            }),
            'supervisor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف اللجنة',
                'rows': 4
            }),
        }
        labels = {
            'name': 'اسم اللجنة',
            'supervisor': 'المشرف',
            'description': 'الوصف',
        }

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)

        if program:
            # Filter supervisors who are linked to this program
            program_supervisors = User.objects.filter(
                role='committee_supervisor',
                programsupervisor__program=program
            ).distinct()
            self.fields['supervisor'].queryset = program_supervisors

from django.db.models import Q


class TaskForm(forms.ModelForm):
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
        model = Task
        fields = ['title', 'description', 'committee', 'assigned_to', 'status', 'priority',
                  'start_date', 'due_date', 'is_recurring', 'recurrence_pattern',
                  'recurrence_days', 'recurrence_end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان المهمة'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف المهمة',
                'rows': 4
            }),
            'committee': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_committee'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_assigned_to'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
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
        }
        labels = {
            'title': 'عنوان المهمة',
            'description': 'الوصف',
            'committee': 'اللجنة',
            'assigned_to': 'المسؤول',
            'status': 'الحالة',
            'priority': 'الأولوية',
            'start_date': 'تاريخ البداية',
            'due_date': 'تاريخ الاستحقاق',
        }

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)

        if program:
            # Filter committees belonging to the program
            self.fields['committee'].queryset = Committee.objects.filter(program=program)

            # Filter users who can be assigned tasks (supervisors and program managers)
            assigned_to_queryset = User.objects.filter(
                Q(role='committee_supervisor', programsupervisor__program=program) |
                Q(role='program_manager')
            ).distinct()

            # Modify the choices to include committee information
            choices = []
            for user in assigned_to_queryset:
                if user.role == 'committee_supervisor':
                    # Get committees supervised by this user in this program
                    committees = Committee.objects.filter(
                        program=program,
                        supervisor=user
                    )
                    if committees.exists():
                        committee_names = ", ".join([committee.name for committee in committees])
                        display_name = f"{user.get_full_name()} - {committee_names}"
                    else:
                        display_name = f"{user.get_full_name()} - لا توجد لجان"
                else:
                    display_name = f"{user.get_full_name()} - مدير البرنامج"

                choices.append((user.id, display_name))

            self.fields['assigned_to'].choices = [('', 'اختر المسؤول...')] + choices

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


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['name', 'description', 'committee', 'date', 'time', 'location']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم النشاط'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف النشاط',
                'rows': 4
            }),
            'committee': forms.Select(attrs={
                'class': 'form-select'
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
                'placeholder': 'أدخل مكان النشاط'
            }),
        }
        labels = {
            'name': 'اسم النشاط',
            'description': 'الوصف',
            'committee': 'اللجنة',
            'date': 'التاريخ',
            'time': 'الوقت',
            'location': 'المكان',
        }

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)

        if program:
            # Filter committees belonging to the program
            self.fields['committee'].queryset = Committee.objects.filter(program=program)


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = StudentAttendance
        fields = ['student', 'activity', 'attended', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-select'
            }),
            'activity': forms.Select(attrs={
                'class': 'form-select'
            }),
            'attended': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل ملاحظات حول الحضور',
                'rows': 3
            }),
        }
        labels = {
            'student': 'الطالب',
            'activity': 'النشاط',
            'attended': 'حضر',
            'notes': 'ملاحظات',
        }


class AddSupervisorForm(forms.ModelForm):
    supervisor_type = forms.ChoiceField(
        choices=[
            ('cultural', 'مشرف لجنة ثقافية'),
            ('sports', 'مشرف لجنة رياضية'),
            ('sharia', 'مشرف اللجنة الشرعية'),
            ('scientific', 'مشرف اللجنة العلمية'),
            ('operations', 'مشرف اللجنة التشغيلية'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='نوع المشرف',
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'supervisor_type']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم المستخدم'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل البريد الإلكتروني'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل الاسم الأول'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم العائلة'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل رقم الهاتف'
            }),
        }
        labels = {
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
            'phone': 'رقم الهاتف',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'committee_supervisor'
        if commit:
            user.save()
        return user