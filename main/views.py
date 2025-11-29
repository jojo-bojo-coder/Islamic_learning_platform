from django.shortcuts import render
from director_dashboard.models import Program, Committee, Student
from accounts.models import User

from django.shortcuts import render, redirect
from director_dashboard.models import Program, Committee, Student
from accounts.models import User
from director_dashboard.models import AlbumPhoto

def home(request):
    # Check if user is authenticated
    if request.user.is_authenticated:
        # Redirect based on user role
        if request.user.role == 'director':
            return redirect('dashboard')  # Director dashboard
        elif request.user.role == 'program_manager':
            return redirect('pm_dashboard')  # Program manager dashboard
        elif request.user.role == 'committee_supervisor':
            # REDIRECT BASED ON SUPERVISOR TYPE
            if request.user.supervisor_type == 'cultural':
                return redirect('cultural_dashboard')
            elif request.user.supervisor_type == 'sports':
                return redirect('sports_dashboard')  # You'll create this later
            elif request.user.supervisor_type == 'sharia':
                return redirect('sharia_dashboard')
            elif request.user.supervisor_type == 'scientific':
                return redirect('scientific_dashboard')
            elif request.user.supervisor_type == 'operations':
                return redirect('operations_dashboard')
            else:
                return redirect('home')

    recent_photos = AlbumPhoto.objects.select_related('album').filter(
        album__is_active=True
    ).order_by('-created_at')[:10]


    # If not authenticated, show the public homepage
    context = {
        'total_programs': Program.objects.count(),
        'total_committees': Committee.objects.count(),
        'total_students': Student.objects.count(),
        'total_users': User.objects.count(),
        'recent_photos': recent_photos,
    }
    return render(request, 'main/home.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange
from accounts.models import User, UserActivity
from director_dashboard.models import Program, Committee
from .models import ScheduleEvent, EventAttendance
from .forms import ScheduleEventForm, EventAttendanceForm, ProgramSelectionForm


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from calendar import monthrange

from accounts.models import User, UserActivity
from director_dashboard.models import Program, Committee
from .models import ScheduleEvent, EventAttendance
from .forms import ScheduleEventForm, EventAttendanceForm, ProgramSelectionForm
from pm_dashboard.models import Task, Activity, StudentAttendance
from cultural_committee_dashboard.models import CulturalTask, CulturalReport,TaskSession
from operations_committee_dashboard.models import OperationsTask
from scientific_committee_dashboard.models import ScientificTask, Lecture
from sharia_committee_dashboard.models import ShariaTask, FamilyCompetition
from sports_committee_dashboard.models import SportsTask, Match


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def schedule_calendar(request, program_id=None):
    """Main calendar view for all users with monthly/weekly toggle - includes all committee tasks"""
    user = request.user

    # Director selects program
    if user.role == 'director':
        if not program_id:
            programs = Program.objects.all()
            if programs.count() == 1:
                return redirect('schedule_calendar', program_id=programs.first().id)

            form = ProgramSelectionForm(request.GET or None)
            if request.GET.get('program'):
                return redirect('schedule_calendar', program_id=request.GET.get('program'))

            context = {
                'form': form,
                'programs': programs,
            }
            return render(request, 'schedule/select_program.html', context)

        program = get_object_or_404(Program, id=program_id)

    # Program Manager
    elif user.role == 'program_manager':
        try:
            program = Program.objects.get(manager=user)
        except Program.DoesNotExist:
            messages.error(request, 'لم يتم تعيين برنامج لك بعد')
            return redirect('home')

    # Committee Supervisor
    elif user.role == 'committee_supervisor':
        try:
            committee = Committee.objects.get(supervisor=user)
            program = committee.program
        except Committee.DoesNotExist:
            messages.error(request, 'لم يتم تعيين لجنة لك بعد')
            return redirect('home')

    else:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # Get view type (monthly or weekly)
    view_type = request.GET.get('view', 'monthly')

    # Get month, year, and week from query params
    now = timezone.now()
    year = int(request.GET.get('year', now.year))
    month = int(request.GET.get('month', now.month))
    week_number = int(request.GET.get('week', now.isocalendar()[1]))

    # Calculate previous and next month
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    if view_type == 'weekly':
        # Weekly view logic
        jan_1 = datetime(year, 1, 1).date()
        week_start = jan_1 + timedelta(weeks=week_number - 1)
        week_start = week_start - timedelta(days=(week_start.weekday() + 1) % 7)
        week_end = week_start + timedelta(days=6)

        prev_week = week_number - 1 if week_number > 1 else 52
        prev_week_year = year if week_number > 1 else year - 1
        next_week = week_number + 1 if week_number < 52 else 1
        next_week_year = year if week_number < 52 else year + 1

        # Get all events and tasks for the week
        events = ScheduleEvent.objects.filter(
            program=program,
            start_date__gte=week_start,
            start_date__lte=week_end
        ).select_related('committee', 'created_by').order_by('start_date', 'start_time')

        tasks = Task.objects.filter(
            program=program,
            due_date__gte=week_start,
            due_date__lte=week_end
        ).select_related('committee')

        activities = Activity.objects.filter(
            program=program,
            date__gte=week_start,
            date__lte=week_end
        ).select_related('committee', 'created_by')

        cultural_tasks = CulturalTask.objects.filter(
            committee__program=program,
            due_date__gte=week_start,
            due_date__lte=week_end
        ).select_related('committee')

        task_sessions = TaskSession.objects.filter(
            task__committee__program=program,
            date__gte=week_start,
            date__lte=week_end
        ).select_related('task', 'task__committee')

        operations_tasks = OperationsTask.objects.filter(
            committee__program=program,
            due_date__gte=week_start,
            due_date__lte=week_end
        ).select_related('committee')

        scientific_tasks = ScientificTask.objects.filter(
            committee__program=program,
            due_date__gte=week_start,
            due_date__lte=week_end
        ).select_related('committee')

        lectures = Lecture.objects.filter(
            committee__program=program,
            date__gte=week_start,
            date__lte=week_end
        ).select_related('committee', 'created_by')

        sharia_tasks = ShariaTask.objects.filter(
            committee__program=program,
            due_date__gte=week_start,
            due_date__lte=week_end
        ).select_related('committee')

        family_competitions = FamilyCompetition.objects.filter(
            committee__program=program,
            start_date__lte=week_end,
            end_date__gte=week_start
        ).select_related('committee')

        sports_tasks = SportsTask.objects.filter(
            committee__program=program,
            due_date__gte=week_start,
            due_date__lte=week_end
        ).select_related('committee')

        matches = Match.objects.filter(
            committee__program=program,
            date__gte=week_start,
            date__lte=week_end
        ).select_related('committee', 'created_by')

        # Filter by committee if supervisor
        if user.role == 'committee_supervisor':
            events = events.filter(Q(committee=committee) | Q(committee__isnull=True))
            tasks = tasks.filter(Q(committee=committee) | Q(committee__isnull=True))
            activities = activities.filter(Q(committee=committee) | Q(committee__isnull=True))
            cultural_tasks = cultural_tasks.filter(committee=committee)
            task_sessions = task_sessions.filter(task__committee=committee)
            operations_tasks = operations_tasks.filter(committee=committee)
            scientific_tasks = scientific_tasks.filter(committee=committee)
            lectures = lectures.filter(committee=committee)
            sharia_tasks = sharia_tasks.filter(committee=committee)
            family_competitions = family_competitions.filter(committee=committee)
            sports_tasks = sports_tasks.filter(committee=committee)
            matches = matches.filter(committee=committee)

        # Build week days
        week_days = []
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_events = events.filter(start_date=day_date)
            day_tasks = tasks.filter(due_date=day_date)
            day_activities = activities.filter(date=day_date)
            day_cultural_tasks = cultural_tasks.filter(due_date=day_date)
            day_task_sessions = task_sessions.filter(date=day_date)
            day_operations_tasks = operations_tasks.filter(due_date=day_date)
            day_scientific_tasks = scientific_tasks.filter(due_date=day_date)
            day_lectures = lectures.filter(date=day_date)
            day_sharia_tasks = sharia_tasks.filter(due_date=day_date)
            day_family_competitions = family_competitions.filter(
                start_date__lte=day_date,
                end_date__gte=day_date
            )
            day_sports_tasks = sports_tasks.filter(due_date=day_date)
            day_matches = matches.filter(date=day_date)

            total_count = (
                day_events.count() + day_tasks.count() + day_activities.count() +
                day_cultural_tasks.count() + day_task_sessions.count() + day_operations_tasks.count() +
                day_scientific_tasks.count() + day_lectures.count() +
                day_sharia_tasks.count() + day_family_competitions.count() +
                day_sports_tasks.count() + day_matches.count()
            )

            week_days.append({
                'date': day_date,
                'day': day_date.day,
                'is_today': day_date == now.date(),
                'events': day_events,
                'tasks': day_tasks,
                'activities': day_activities,
                'cultural_tasks': day_cultural_tasks,
                'operations_tasks': day_operations_tasks,
                'task_sessions': day_task_sessions,
                'scientific_tasks': day_scientific_tasks,
                'lectures': day_lectures,
                'sharia_tasks': day_sharia_tasks,
                'family_competitions': day_family_competitions,
                'sports_tasks': day_sports_tasks,
                'matches': day_matches,
                'total_events': total_count,
            })

        weeks = [week_days]

        month_names = [
            'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
            'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
        ]

        context_extra = {
            'view_type': 'weekly',
            'week_number': week_number,
            'week_start': week_start,
            'week_end': week_end,
            'prev_week': prev_week,
            'prev_week_year': prev_week_year,
            'next_week': next_week,
            'next_week_year': next_week_year,
            'month_name': f"{month_names[week_start.month - 1]} - {month_names[week_end.month - 1]}" if week_start.month != week_end.month else month_names[week_start.month - 1],
        }

    else:
        # Monthly view logic
        first_day = datetime(year, month, 1).date()
        last_day = datetime(year, month, monthrange(year, month)[1]).date()

        events = ScheduleEvent.objects.filter(
            program=program,
            start_date__lte=last_day,
            start_date__gte=first_day
        ).select_related('committee', 'created_by').order_by('start_date', 'start_time')

        tasks = Task.objects.filter(
            program=program,
            due_date__lte=last_day,
            due_date__gte=first_day
        ).select_related('committee')

        activities = Activity.objects.filter(
            program=program,
            date__lte=last_day,
            date__gte=first_day
        ).select_related('committee', 'created_by')

        cultural_tasks = CulturalTask.objects.filter(
            committee__program=program,
            due_date__lte=last_day,
            due_date__gte=first_day
        ).select_related('committee')

        task_sessions = TaskSession.objects.filter(
            task__committee__program=program,
            date__lte=last_day,
            date__gte=first_day
        ).select_related('task', 'task__committee')

        operations_tasks = OperationsTask.objects.filter(
            committee__program=program,
            due_date__lte=last_day,
            due_date__gte=first_day
        ).select_related('committee')

        scientific_tasks = ScientificTask.objects.filter(
            committee__program=program,
            due_date__lte=last_day,
            due_date__gte=first_day
        ).select_related('committee')

        lectures = Lecture.objects.filter(
            committee__program=program,
            date__lte=last_day,
            date__gte=first_day
        ).select_related('committee', 'created_by')

        sharia_tasks = ShariaTask.objects.filter(
            committee__program=program,
            due_date__lte=last_day,
            due_date__gte=first_day
        ).select_related('committee')

        family_competitions = FamilyCompetition.objects.filter(
            committee__program=program,
            start_date__lte=last_day,
            end_date__gte=first_day
        ).select_related('committee')

        sports_tasks = SportsTask.objects.filter(
            committee__program=program,
            due_date__lte=last_day,
            due_date__gte=first_day
        ).select_related('committee')

        matches = Match.objects.filter(
            committee__program=program,
            date__lte=last_day,
            date__gte=first_day
        ).select_related('committee', 'created_by')

        if user.role == 'committee_supervisor':
            events = events.filter(Q(committee=committee) | Q(committee__isnull=True))
            tasks = tasks.filter(Q(committee=committee) | Q(committee__isnull=True))
            activities = activities.filter(Q(committee=committee) | Q(committee__isnull=True))
            cultural_tasks = cultural_tasks.filter(committee=committee)
            task_sessions = task_sessions.filter(task__committee=committee)
            operations_tasks = operations_tasks.filter(committee=committee)
            scientific_tasks = scientific_tasks.filter(committee=committee)
            lectures = lectures.filter(committee=committee)
            sharia_tasks = sharia_tasks.filter(committee=committee)
            family_competitions = family_competitions.filter(committee=committee)
            sports_tasks = sports_tasks.filter(committee=committee)
            matches = matches.filter(committee=committee)

        cal_data = []
        first_weekday = first_day.weekday()
        first_weekday = (first_weekday + 1) % 7

        if first_weekday > 0:
            prev_month_days = monthrange(prev_year, prev_month)[1]
            for i in range(first_weekday):
                day = prev_month_days - first_weekday + i + 1
                cal_data.append({
                    'day': day,
                    'date': datetime(prev_year, prev_month, day).date(),
                    'is_current_month': False,
                    'events': []
                })

        days_in_month = monthrange(year, month)[1]
        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day).date()
            day_events = events.filter(start_date=date)
            day_tasks = tasks.filter(due_date=date)
            day_activities = activities.filter(date=date)
            day_cultural_tasks = cultural_tasks.filter(due_date=date)
            day_task_sessions = task_sessions.filter(date=date)
            day_operations_tasks = operations_tasks.filter(due_date=date)
            day_scientific_tasks = scientific_tasks.filter(due_date=date)
            day_lectures = lectures.filter(date=date)
            day_sharia_tasks = sharia_tasks.filter(due_date=date)
            day_family_competitions = family_competitions.filter(
                start_date__lte=date,
                end_date__gte=date
            )
            day_sports_tasks = sports_tasks.filter(due_date=date)
            day_matches = matches.filter(date=date)

            total_count = (
                day_events.count() + day_tasks.count() + day_activities.count() +
                day_cultural_tasks.count() + day_task_sessions.count() + day_operations_tasks.count() +
                day_scientific_tasks.count() + day_lectures.count() +
                day_sharia_tasks.count() + day_family_competitions.count() +
                day_sports_tasks.count() + day_matches.count()
            )

            cal_data.append({
                'day': day,
                'date': date,
                'is_current_month': True,
                'is_today': date == now.date(),
                'events': day_events,
                'tasks': day_tasks,
                'activities': day_activities,
                'cultural_tasks': day_cultural_tasks,
                'operations_tasks': day_operations_tasks,
                'scientific_tasks': day_scientific_tasks,
                'task_sessions':day_task_sessions,
                'lectures': day_lectures,
                'sharia_tasks': day_sharia_tasks,
                'family_competitions': day_family_competitions,
                'sports_tasks': day_sports_tasks,
                'matches': day_matches,
                'total_events': total_count,
            })

        remaining = 42 - len(cal_data)
        for day in range(1, remaining + 1):
            date = datetime(next_year, next_month, day).date()
            cal_data.append({
                'day': day,
                'date': date,
                'is_current_month': False,
                'events': []
            })

        weeks = []
        for i in range(0, len(cal_data), 7):
            weeks.append(cal_data[i:i + 7])

        month_names = [
            'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
            'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'
        ]
        month_name = month_names[month - 1]

        context_extra = {
            'view_type': 'monthly',
            'month_name': month_name,
            'prev_year': prev_year,
            'prev_month': prev_month,
            'next_year': next_year,
            'next_month': next_month,
        }

    # Determine base template
    if user.role == 'director':
        base_template = 'director_base.html'
    elif user.role == 'program_manager':
        base_template = 'program_manager_base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'cultural':
        base_template = 'cultural_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sports':
        base_template = 'sports_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sharia':
        base_template = 'sharia_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'operations':
        base_template = 'operations_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'scientific':
        base_template = 'scientific_committee/base.html'
    else:
        base_template = 'base.html'

    context = {
        'program': program,
        'weeks': weeks,
        'year': year,
        'month': month,
        'today': now.date(),
        'base_template': base_template,
    }
    context.update(context_extra)

    return render(request, 'schedule/calendar.html', context)


@login_required
def day_events(request, program_id, year, month, day):
    """Show all events for a specific day - includes all committee tasks"""
    program = get_object_or_404(Program, id=program_id)
    user = request.user

    # Check permissions
    if not has_permission_for_program(user, program):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    date = datetime(year, month, day).date()

    # Get all events for this day
    events = ScheduleEvent.objects.filter(
        program=program,
        start_date=date
    ).select_related('committee', 'created_by').order_by('start_time')

    tasks = Task.objects.filter(
        program=program,
        due_date=date
    ).select_related('committee')

    activities = Activity.objects.filter(
        program=program,
        date=date
    ).select_related('committee', 'created_by')

    cultural_tasks = CulturalTask.objects.filter(
        committee__program=program,
        due_date=date
    ).select_related('committee')

    task_sessions = TaskSession.objects.filter(
        task__committee__program=program,
        date=date
    ).select_related('task', 'task__committee')

    operations_tasks = OperationsTask.objects.filter(
        committee__program=program,
        due_date=date
    ).select_related('committee')

    scientific_tasks = ScientificTask.objects.filter(
        committee__program=program,
        due_date=date
    ).select_related('committee')

    lectures = Lecture.objects.filter(
        committee__program=program,
        date=date
    ).select_related('committee', 'created_by')

    sharia_tasks = ShariaTask.objects.filter(
        committee__program=program,
        due_date=date
    ).select_related('committee')

    family_competitions = FamilyCompetition.objects.filter(
        committee__program=program,
        start_date__lte=date,
        end_date__gte=date
    ).select_related('committee')

    sports_tasks = SportsTask.objects.filter(
        committee__program=program,
        due_date=date
    ).select_related('committee')

    matches = Match.objects.filter(
        committee__program=program,
        date=date
    ).select_related('committee', 'created_by')

    # Filter by committee if supervisor
    if user.role == 'committee_supervisor':
        try:
            committee = Committee.objects.get(supervisor=user)
            events = events.filter(Q(committee=committee) | Q(committee__isnull=True))
            tasks = tasks.filter(Q(committee=committee) | Q(committee__isnull=True))
            activities = activities.filter(Q(committee=committee) | Q(committee__isnull=True))
            cultural_tasks = cultural_tasks.filter(committee=committee)
            task_sessions = task_sessions.filter(task__committee=committee)
            operations_tasks = operations_tasks.filter(committee=committee)
            scientific_tasks = scientific_tasks.filter(committee=committee)
            lectures = lectures.filter(committee=committee)
            sharia_tasks = sharia_tasks.filter(committee=committee)
            family_competitions = family_competitions.filter(committee=committee)
            sports_tasks = sports_tasks.filter(committee=committee)
            matches = matches.filter(committee=committee)
        except Committee.DoesNotExist:
            pass

    # Determine base template
    if user.role == 'director':
        base_template = 'director_base.html'
    elif user.role == 'program_manager':
        base_template = 'program_manager_base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'cultural':
        base_template = 'cultural_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'scientific':
        base_template = 'scientific_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sports':
        base_template = 'sports_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sharia':
        base_template = 'sharia_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'operations':
        base_template = 'operations_committee/base.html'
    else:
        base_template = 'base.html'

    context = {
        'program': program,
        'date': date,
        'events': events,
        'tasks': tasks,
        'activities': activities,
        'cultural_tasks': cultural_tasks,
        'task_sessions': task_sessions,
        'operations_tasks': operations_tasks,
        'scientific_tasks': scientific_tasks,
        'lectures': lectures,
        'sharia_tasks': sharia_tasks,
        'family_competitions': family_competitions,
        'sports_tasks': sports_tasks,
        'matches': matches,
        'base_template': base_template,
    }

    return render(request, 'schedule/day_events.html', context)


def has_permission_for_program(user, program):
    """Check if user has permission for this program"""
    if user.role == 'director':
        return True
    elif user.role == 'program_manager':
        return program.manager == user
    elif user.role == 'committee_supervisor':
        try:
            committee = Committee.objects.get(supervisor=user)
            return committee.program == program
        except Committee.DoesNotExist:
            return False
    return False

@login_required
def object_list(request, object_type, program_id):
    """List view for different object types"""
    program = get_object_or_404(Program, id=program_id)

    # Check permissions
    if not has_permission_for_program(request.user, program):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    model_map = {
        'task': (Task, 'tasks'),
        'activity': (Activity, 'activities'),
        'cultural_task': (CulturalTask, 'cultural_tasks'),
        'cultural_report': (CulturalReport, 'cultural_reports'),
    }

    if object_type not in model_map:
        messages.error(request, 'نوع الكائن غير صحيح')
        return redirect('home')

    model_class, template_name = model_map[object_type]

    if object_type == 'cultural_task' or object_type == 'cultural_report':
        objects = model_class.objects.filter(committee__program=program)
    else:
        objects = model_class.objects.filter(program=program)

    context = {
        'objects': objects,
        'program': program,
        'object_type': object_type,
        'object_type_display': get_object_type_display(object_type),
    }

    return render(request, f'schedule/{template_name}_list.html', context)





@login_required
def event_detail(request, event_id):
    """Event detail page"""
    event = get_object_or_404(ScheduleEvent, id=event_id)
    user = request.user

    # Check permissions
    if user.role == 'director':
        pass  # Can view all
    elif user.role == 'program_manager':
        if event.program.manager != user:
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذا الحدث')
            return redirect('home')
    elif user.role == 'committee_supervisor':
        try:
            committee = Committee.objects.get(supervisor=user)
            if event.program != committee.program:
                messages.error(request, 'ليس لديك صلاحية للوصول إلى هذا الحدث')
                return redirect('home')
        except Committee.DoesNotExist:
            messages.error(request, 'لم يتم تعيين لجنة لك بعد')
            return redirect('home')

    attendances = event.attendances.select_related('user', 'recorded_by').all()

    context = {
        'event': event,
        'attendances': attendances,
    }

    return render(request, 'schedule/event_detail.html', context)


@login_required
def add_event(request, program_id=None):
    """Add new event"""
    user = request.user

    # Get program
    if user.role == 'director':
        if not program_id:
            messages.error(request, 'يجب تحديد برنامج')
            return redirect('home')
        program = get_object_or_404(Program, id=program_id)
    elif user.role == 'program_manager':
        try:
            program = Program.objects.get(manager=user)
        except Program.DoesNotExist:
            messages.error(request, 'لم يتم تعيين برنامج لك بعد')
            return redirect('home')
    elif user.role == 'committee_supervisor':
        try:
            committee = Committee.objects.get(supervisor=user)
            program = committee.program
        except Committee.DoesNotExist:
            messages.error(request, 'لم يتم تعيين لجنة لك بعد')
            return redirect('home')
    else:
        messages.error(request, 'ليس لديك صلاحية لإضافة أحداث')
        return redirect('home')

    if request.method == 'POST':
        form = ScheduleEventForm(request.POST, program=program)
        if form.is_valid():
            event = form.save(commit=False)
            event.program = program
            event.created_by = user
            event.save()


            UserActivity.objects.create(
                user=user,
                action=f'إضافة حدث جدولة: {event.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة الحدث بنجاح!')
            return redirect('schedule_calendar', program_id=program.id)
    else:
        form = ScheduleEventForm(program=program)

    context = {
        'form': form,
        'program': program,
        'title': 'إضافة حدث جديد'
    }
    return render(request, 'schedule/event_form.html', context)



@login_required
def edit_event(request, event_id):
    """Edit existing event"""
    event = get_object_or_404(ScheduleEvent, id=event_id)
    user = request.user

    # Check permissions
    if user.role not in ['director', 'program_manager', 'committee_supervisor']:
        messages.error(request, 'ليس لديك صلاحية لتعديل الأحداث')
        return redirect('home')

    if request.method == 'POST':
        form = ScheduleEventForm(request.POST, instance=event, program=event.program)
        if form.is_valid():
            event = form.save()

            UserActivity.objects.create(
                user=user,
                action=f'تعديل حدث جدولة: {event.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل الحدث بنجاح!')
            return redirect('event_detail', event_id=event.id)
    else:
        form = ScheduleEventForm(instance=event, program=event.program)

    context = {
        'form': form,
        'event': event,
        'program': event.program,
        'title': 'تعديل الحدث'
    }
    return render(request, 'schedule/event_form.html', context)


@login_required
def delete_event(request, event_id):
    """Delete event"""
    event = get_object_or_404(ScheduleEvent, id=event_id)
    user = request.user

    # Check permissions
    if user.role not in ['director', 'program_manager']:
        messages.error(request, 'ليس لديك صلاحية لحذف الأحداث')
        return redirect('home')

    program_id = event.program.id

    if request.method == 'POST':
        event_title = event.title
        event.delete()

        UserActivity.objects.create(
            user=user,
            action=f'حذف حدث جدولة: {event_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف الحدث بنجاح!')
        return redirect('schedule_calendar', program_id=program_id)

    context = {
        'object': event,
        'type': 'حدث',
        'program': event.program
    }
    return render(request, 'schedule/confirm_delete.html', context)


# Add these imports at the top of views.py
from pm_dashboard.models import Task, Activity,StudentAttendance
from cultural_committee_dashboard.models import CulturalTask, CulturalReport, FileLibrary, Discussion,CommitteeMember,DiscussionComment


@login_required
def object_detail(request, object_type, object_id):
    """Generic detail page for any object type"""
    user = request.user

    # Map object types to their models
    model_map = {
        'task': Task,
        'activity': Activity,
        'cultural_task': CulturalTask,
        'cultural_report': CulturalReport,
        'file': FileLibrary,
        'discussion': Discussion,
        'operations_task': OperationsTask,
        'scientific_task': ScientificTask,
        'lecture': Lecture,
        'sharia_task': ShariaTask,
        'family_competition': FamilyCompetition,
        'sports_task': SportsTask,
        'match': Match,
    }

    if object_type not in model_map:
        messages.error(request, 'نوع الكائن غير صحيح')
        return redirect('home')

    model_class = model_map[object_type]
    obj = get_object_or_404(model_class, id=object_id)

    # Check permissions based on object type and user role
    if not has_permission_for_object(user, obj):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # Determine base template based on user role
    if user.role == 'director':
        base_template = 'director_base.html'
    elif user.role == 'program_manager':
        base_template = 'program_manager_base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'cultural':
        base_template = 'cultural_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'operations':
        base_template = 'operations_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'scientific':
        base_template = 'scientific_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sharia':
        base_template = 'sharia_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sports':
        base_template = 'sports_committee/base.html'
    else:
        base_template = 'base.html'

    # Get template context based on object type
    context = get_object_context(obj, object_type)
    context.update({
        'object': obj,
        'object_type': object_type,
        'object_type_display': get_object_type_display(object_type),
        'base_template': base_template,
    })

    template_name = get_template_name(object_type)
    return render(request, template_name, context)


def has_permission_for_object(user, obj):
    """Check if user has permission to view this object"""
    # Director can view everything
    if user.role == 'director':
        return True

    # Program Manager can view objects in their program
    if user.role == 'program_manager':
        program = get_object_program(obj)
        return program and program.manager == user

    # Committee Supervisor can view objects in their committee/program
    if user.role == 'committee_supervisor':
        program = get_object_program(obj)
        committee = get_object_committee(obj)

        if program:
            try:
                user_committee = Committee.objects.get(supervisor=user)
                return user_committee.program == program
            except Committee.DoesNotExist:
                return False

        if committee:
            return committee.supervisor == user

    return False


def get_object_program(obj):
    """Extract program from different object types"""
    if hasattr(obj, 'program'):
        return obj.program
    elif hasattr(obj, 'committee'):
        return obj.committee.program if obj.committee else None
    return None


def get_object_committee(obj):
    """Extract committee from different object types"""
    if hasattr(obj, 'committee'):
        return obj.committee
    return None


def get_object_context(obj, object_type):
    """Get specific context for each object type"""
    context = {}

    if object_type == 'task':
        context.update({
            'is_overdue': obj.is_overdue,
            'related_activities': Activity.objects.filter(program=obj.program, committee=obj.committee),
        })

    elif object_type == 'activity':
        context.update({
            'attendances': StudentAttendance.objects.filter(activity=obj).select_related('student', 'recorded_by'),
            'total_participants': obj.attendances.count(),
            'attended_count': obj.attendances.filter(attended=True).count(),
        })

    elif object_type == 'cultural_task':
        from cultural_committee_dashboard.models import CommitteeMember, FileLibrary
        context.update({
            'committee_members': CommitteeMember.objects.filter(committee=obj.committee, is_active=True),
            'related_files': FileLibrary.objects.filter(committee=obj.committee, file_type='cultural_plan'),
        })

    elif object_type == 'operations_task':
        from operations_committee_dashboard.models import OperationsTeamMember, LogisticsResource
        context.update({
            'committee_members': OperationsTeamMember.objects.filter(committee=obj.committee, is_active=True),
            'related_resources': LogisticsResource.objects.filter(committee=obj.committee),
            'is_overdue': obj.is_overdue,
        })

    elif object_type == 'scientific_task':
        from scientific_committee_dashboard.models import ScientificMember, ScientificFile
        context.update({
            'committee_members': ScientificMember.objects.filter(committee=obj.committee, is_active=True),
            'related_files': ScientificFile.objects.filter(committee=obj.committee),
        })

    elif object_type == 'lecture':
        from scientific_committee_dashboard.models import LectureAttendance
        context.update({
            'attendances': LectureAttendance.objects.filter(lecture=obj).select_related('user', 'recorded_by'),
            'total_participants': obj.attendances.count(),
            'attended_count': obj.attendances.filter(attended=True).count(),
        })

    elif object_type == 'sharia_task':
        from sharia_committee_dashboard.models import ShariaMember, ShariaFile
        context.update({
            'committee_members': ShariaMember.objects.filter(committee=obj.committee, is_active=True),
            'related_files': ShariaFile.objects.filter(committee=obj.committee),
        })

    elif object_type == 'family_competition':
        context.update({
            'is_active': obj.status == 'active',
            'is_upcoming': obj.status == 'upcoming',
        })

    elif object_type == 'sports_task':
        from sports_committee_dashboard.models import SportsMember
        context.update({
            'committee_members': SportsMember.objects.filter(committee=obj.committee, is_active=True),
        })

    elif object_type == 'match':
        context.update({
            'is_completed': obj.status == 'completed',
            'has_scores': obj.team1_score is not None and obj.team2_score is not None,
        })

    return context


def get_object_type_display(object_type):
    """Get display name for object type"""
    display_names = {
        'task': 'مهمة',
        'activity': 'نشاط',
        'cultural_task': 'مهمة ثقافية',
        'cultural_report': 'تقرير ثقافي',
        'file': 'ملف',
        'discussion': 'نقاش',
        'operations_task': 'مهمة تشغيلية',
        'scientific_task': 'مهمة علمية',
        'lecture': 'محاضرة',
        'sharia_task': 'مهمة شرعية',
        'family_competition': 'مسابقة أسرية',
        'sports_task': 'مهمة رياضية',
        'match': 'مباراة',
    }
    return display_names.get(object_type, 'كائن')


def get_template_name(object_type):
    """Get template name for each object type"""
    return f'schedule/{object_type}_detail.html'


from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from director_dashboard.models import DirectorAlbum, AlbumPhoto


def public_albums(request):
    """Public albums page for non-authenticated users"""
    # Get only active albums
    albums = DirectorAlbum.objects.filter(is_active=True).prefetch_related('photos').order_by('-created_at')

    # Pagination
    paginator = Paginator(albums, 9)  # Show 9 albums per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'albums': page_obj,
        'total_albums': albums.count(),
    }
    return render(request, 'main/albums.html', context)


def public_album_detail(request, album_id):
    """Public album detail page showing all photos"""
    album = get_object_or_404(DirectorAlbum, id=album_id, is_active=True)
    photos = album.photos.all().order_by('order', '-created_at')

    # Pagination for photos
    paginator = Paginator(photos, 12)  # Show 12 photos per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'album': album,
        'photos': page_obj,
        'total_photos': photos.count(),
    }
    return render(request, 'main/album_detail.html', context)
