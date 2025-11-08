from django import forms
from django.utils import timezone
from .models import ScheduleEvent, EventAttendance
from director_dashboard.models import Committee, Program
from accounts.models import User


class ScheduleEventForm(forms.ModelForm):
    class Meta:
        model = ScheduleEvent
        fields = ['title', 'description', 'event_type', 'committee', 'start_date',
                  'end_date', 'start_time', 'end_time', 'location', 'assigned_to',
                  'status', 'priority', 'color']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان الحدث'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف الحدث',
                'rows': 4
            }),
            'event_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'committee': forms.Select(attrs={
                'class': 'form-select'
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
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل مكان الحدث'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
        }
        labels = {
            'title': 'العنوان',
            'description': 'الوصف',
            'event_type': 'نوع الحدث',
            'committee': 'اللجنة',
            'start_date': 'تاريخ البداية',
            'end_date': 'تاريخ النهاية',
            'start_time': 'وقت البداية',
            'end_time': 'وقت النهاية',
            'location': 'المكان',
            'assigned_to': 'المسؤول',
            'status': 'الحالة',
            'priority': 'الأولوية',
            'color': 'اللون',
        }

    def __init__(self, *args, **kwargs):
        program = kwargs.pop('program', None)
        super().__init__(*args, **kwargs)

        if program:
            # Filter committees belonging to the program
            self.fields['committee'].queryset = Committee.objects.filter(program=program)

            # Filter users who can be assigned
            self.fields['assigned_to'].queryset = User.objects.filter(
                role__in=['committee_supervisor', 'program_manager']
            )


class EventAttendanceForm(forms.ModelForm):
    class Meta:
        model = EventAttendance
        fields = ['attended', 'notes']
        widgets = {
            'attended': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل ملاحظات',
                'rows': 3
            }),
        }
        labels = {
            'attended': 'حضر',
            'notes': 'ملاحظات',
        }


class ProgramSelectionForm(forms.Form):
    program = forms.ModelChoiceField(
        queryset=Program.objects.all(),
        label='اختر البرنامج',
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'onchange': 'this.form.submit()'
        })
    )