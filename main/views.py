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
    """Main calendar view for all users with monthly/weekly toggle - includes all committee tasks and recurring tasks"""
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

        start_date = week_start
        end_date = week_end

    else:
        # Monthly view logic
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, monthrange(year, month)[1]).date()

    # Get all events and tasks for the period
    events = ScheduleEvent.objects.filter(
        program=program,
        start_date__gte=start_date,
        start_date__lte=end_date
    ).select_related('committee', 'created_by').order_by('start_date', 'start_time')

    # Get regular tasks - now handling recurring tasks
    # Get regular tasks - now handling recurring tasks
    tasks = Task.objects.filter(
        program=program
    ).select_related('committee')

    # Process recurring tasks
    task_occurrences = {}  # {date: [(task, is_start, is_end, group_id), ...]}

    for task in tasks:
        if task.is_recurring:
            # IMPORTANT: Only get occurrences within the view's date range
            # Don't process if task hasn't started yet
            task_start = task.start_date or task.due_date
            if task_start > end_date:
                continue

            # Don't process if task has ended
            if task.recurrence_end_date and task.recurrence_end_date < start_date:
                continue

            # Get consecutive day groups for this task within the view range
            groups = task.get_consecutive_day_groups(start_date, end_date)
            for group_idx, (group_start, group_end) in enumerate(groups):
                group_id = f"task_{task.id}_group_{group_idx}"

                # Add all dates in this group
                current = group_start
                while current <= group_end:
                    if start_date <= current <= end_date:
                        if current not in task_occurrences:
                            task_occurrences[current] = []

                        task_occurrences[current].append({
                            'task': task,
                            'is_start': current == group_start,
                            'is_end': current == group_end,
                            'group_id': group_id,
                            'group_start': group_start,
                            'group_end': group_end,
                            'span_days': (group_end - group_start).days + 1
                        })
                    current += timedelta(days=1)
        else:
            # Non-recurring task
            if start_date <= task.due_date <= end_date:
                if task.due_date not in task_occurrences:
                    task_occurrences[task.due_date] = []
                task_occurrences[task.due_date].append({
                    'task': task,
                    'is_start': True,
                    'is_end': True,
                    'group_id': f"task_{task.id}_single",
                    'group_start': task.due_date,
                    'group_end': task.due_date,
                    'span_days': 1
                })

    activities = Activity.objects.filter(
        program=program,
        date__lte=end_date,
        date__gte=start_date
    ).select_related('committee', 'created_by')

    cultural_tasks = CulturalTask.objects.filter(
        committee__program=program,
        due_date__lte=end_date,
        due_date__gte=start_date
    ).select_related('committee')

    task_sessions = TaskSession.objects.filter(
        task__committee__program=program,
        date__lte=end_date,
        date__gte=start_date
    ).select_related('task', 'task__committee')

    operations_tasks = OperationsTask.objects.filter(
        committee__program=program,
        due_date__lte=end_date,
        due_date__gte=start_date
    ).select_related('committee')

    scientific_tasks = ScientificTask.objects.filter(
        committee__program=program,
        due_date__lte=end_date,
        due_date__gte=start_date
    ).select_related('committee')

    lectures = Lecture.objects.filter(
        committee__program=program,
        date__lte=end_date,
        date__gte=start_date
    ).select_related('committee', 'created_by')

    sharia_tasks = ShariaTask.objects.filter(
        committee__program=program,
        due_date__lte=end_date,
        due_date__gte=start_date
    ).select_related('committee')

    family_competitions = FamilyCompetition.objects.filter(
        committee__program=program,
        start_date__lte=end_date,
        end_date__gte=start_date
    ).select_related('committee')

    sports_tasks = SportsTask.objects.filter(
        committee__program=program,
        due_date__lte=end_date,
        due_date__gte=start_date
    ).select_related('committee')

    matches = Match.objects.filter(
        committee__program=program,
        date__lte=end_date,
        date__gte=start_date
    ).select_related('committee', 'created_by')

    # Filter by committee if supervisor
    if user.role == 'committee_supervisor':
        events = events.filter(Q(committee=committee) | Q(committee__isnull=True))
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

    if view_type == 'weekly':
        # Build week days
        week_days = []
        for i in range(7):
            day_date = week_start + timedelta(days=i)
            day_events = events.filter(start_date=day_date)
            day_task_occurrences = task_occurrences.get(day_date, [])
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
                    day_events.count() + len(day_task_occurrences) + day_activities.count() +
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
                'task_occurrences': day_task_occurrences,
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
            'month_name': f"{month_names[week_start.month - 1]} - {month_names[week_end.month - 1]}" if week_start.month != week_end.month else
            month_names[week_start.month - 1],
        }


    else:

        # Monthly view logic

        first_day = datetime(year, month, 1).date()

        last_day = datetime(year, month, monthrange(year, month)[1]).date()

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

                    'events': [],

                    'task_occurrences': []

                })

        days_in_month = monthrange(year, month)[1]

        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day).date()

            day_events = events.filter(start_date=date)

            day_task_occurrences = task_occurrences.get(date, [])

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

                    day_events.count() + len(day_task_occurrences) + day_activities.count() +

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

                'task_occurrences': day_task_occurrences,  # This is now a list, not queryset

                'activities': day_activities,

                'cultural_tasks': day_cultural_tasks,

                'operations_tasks': day_operations_tasks,

                'scientific_tasks': day_scientific_tasks,

                'task_sessions': day_task_sessions,

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

                'events': [],

                'task_occurrences': []

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
    """Show all events for a specific day - includes all committee tasks and recurring tasks"""
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

    # Get ALL tasks (including recurring ones)
    all_tasks = Task.objects.filter(program=program).select_related('committee')

    # Filter tasks that occur on this date
    tasks_for_day = []
    for task in all_tasks:
        if task.is_recurring:
            # Check if this date is in the task's occurrence dates
            occurrences = task.get_occurrence_dates(date, date)
            if date in occurrences:
                tasks_for_day.append(task)
        else:
            # Regular task - check if due_date matches
            if task.due_date == date:
                tasks_for_day.append(task)

    # Convert to queryset-like behavior for template
    tasks = tasks_for_day

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
            tasks = [t for t in tasks if t.committee == committee or t.committee is None]
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


from django.http import HttpResponse
from datetime import datetime, timedelta
import csv
from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


@login_required
def export_calendar_ics(request):
    """Export calendar as ICS file"""
    program_id = request.GET.get('program_id')
    view_type = request.GET.get('view', 'monthly')
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    week = int(request.GET.get('week', timezone.now().isocalendar()[1]))

    program = get_object_or_404(Program, id=program_id)

    # Check permissions
    if not has_permission_for_program(request.user, program):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذا التقويم')
        return redirect('home')

    # Get date range
    if view_type == 'weekly':
        jan_1 = datetime(year, 1, 1).date()
        start_date = jan_1 + timedelta(weeks=week - 1)
        start_date = start_date - timedelta(days=(start_date.weekday() + 1) % 7)
        end_date = start_date + timedelta(days=6)
    else:
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, monthrange(year, month)[1]).date()

    # Get all events
    events = ScheduleEvent.objects.filter(
        program=program,
        start_date__gte=start_date,
        start_date__lte=end_date
    ).select_related('committee', 'created_by')

    # Filter by committee if supervisor
    if request.user.role == 'committee_supervisor':
        try:
            committee = Committee.objects.get(supervisor=request.user)
            events = events.filter(Q(committee=committee) | Q(committee__isnull=True))
        except Committee.DoesNotExist:
            pass

    # Create ICS content
    response = HttpResponse(content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="calendar_{program.name}_{year}_{month}.ics"'

    ics_content = ["BEGIN:VCALENDAR"]
    ics_content.append("VERSION:2.0")
    ics_content.append(f"PRODID:-//{program.name}//Calendar//AR")
    ics_content.append("CALSCALE:GREGORIAN")
    ics_content.append("METHOD:PUBLISH")

    for event in events:
        ics_content.append("BEGIN:VEVENT")

        # Format dates
        dtstart = event.start_date.strftime('%Y%m%d')
        if event.start_time:
            dtstart += f"T{event.start_time.strftime('%H%M%S')}"
        ics_content.append(f"DTSTART:{dtstart}")

        if event.end_date:
            dtend = event.end_date.strftime('%Y%m%d')
            if event.end_time:
                dtend += f"T{event.end_time.strftime('%H%M%S')}"
            ics_content.append(f"DTEND:{dtend}")

        ics_content.append(f"SUMMARY:{event.title}")
        ics_content.append(f"DESCRIPTION:{event.description}")

        if event.location:
            ics_content.append(f"LOCATION:{event.location}")

        ics_content.append(f"UID:{event.id}@{program.name}")
        ics_content.append(f"DTSTAMP:{timezone.now().strftime('%Y%m%dT%H%M%SZ')}")
        ics_content.append("END:VEVENT")

    ics_content.append("END:VCALENDAR")

    response.write('\r\n'.join(ics_content))
    return response


@login_required
def export_calendar_excel(request):
    """Export calendar as Excel file"""
    if not OPENPYXL_AVAILABLE:
        messages.error(request, 'مكتبة Excel غير متوفرة. الرجاء تثبيت openpyxl')
        return redirect('schedule_calendar')

    program_id = request.GET.get('program_id')
    view_type = request.GET.get('view', 'monthly')
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    week = int(request.GET.get('week', timezone.now().isocalendar()[1]))

    program = get_object_or_404(Program, id=program_id)

    # Check permissions
    if not has_permission_for_program(request.user, program):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذا التقويم')
        return redirect('home')

    # Get date range
    if view_type == 'weekly':
        jan_1 = datetime(year, 1, 1).date()
        start_date = jan_1 + timedelta(weeks=week - 1)
        start_date = start_date - timedelta(days=(start_date.weekday() + 1) % 7)
        end_date = start_date + timedelta(days=6)
    else:
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, monthrange(year, month)[1]).date()

    # Get all events
    events = ScheduleEvent.objects.filter(
        program=program,
        start_date__gte=start_date,
        start_date__lte=end_date
    ).select_related('committee', 'created_by').order_by('start_date', 'start_time')

    tasks = Task.objects.filter(
        program=program,
        due_date__gte=start_date,
        due_date__lte=end_date
    ).select_related('committee').order_by('due_date')

    activities = Activity.objects.filter(
        program=program,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('committee').order_by('date')

    # Filter by committee if supervisor
    if request.user.role == 'committee_supervisor':
        try:
            committee = Committee.objects.get(supervisor=request.user)
            events = events.filter(Q(committee=committee) | Q(committee__isnull=True))
            tasks = tasks.filter(Q(committee=committee) | Q(committee__isnull=True))
            activities = activities.filter(Q(committee=committee) | Q(committee__isnull=True))
        except Committee.DoesNotExist:
            pass

    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "التقويم"
    ws.right_to_left = True

    # Styles
    header_fill = PatternFill(start_color="0084AB", end_color="0084AB", fill_type="solid")
    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_alignment = Alignment(horizontal="center", vertical="center")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Headers
    headers = ["التاريخ", "النوع", "العنوان", "الوصف", "الوقت", "المكان", "اللجنة", "الحالة"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = header_alignment
        cell.border = border

    # Add events
    row = 2
    for event in events:
        ws.cell(row=row, column=1, value=event.start_date.strftime('%Y-%m-%d')).border = border
        ws.cell(row=row, column=2, value=event.get_event_type_display()).border = border
        ws.cell(row=row, column=3, value=event.title).border = border
        ws.cell(row=row, column=4, value=event.description).border = border
        ws.cell(row=row, column=5, value=event.start_time.strftime('%H:%M') if event.start_time else '').border = border
        ws.cell(row=row, column=6, value=event.location or '').border = border
        ws.cell(row=row, column=7, value=event.committee.name if event.committee else '').border = border
        ws.cell(row=row, column=8, value=event.get_status_display()).border = border
        row += 1

    # Add tasks
    for task in tasks:
        ws.cell(row=row, column=1, value=task.due_date.strftime('%Y-%m-%d')).border = border
        ws.cell(row=row, column=2, value='مهمة').border = border
        ws.cell(row=row, column=3, value=task.title).border = border
        ws.cell(row=row, column=4, value=task.description).border = border
        ws.cell(row=row, column=5, value='').border = border
        ws.cell(row=row, column=6, value='').border = border
        ws.cell(row=row, column=7, value=task.committee.name if task.committee else '').border = border
        ws.cell(row=row, column=8, value=task.get_status_display()).border = border
        row += 1

    # Add activities
    for activity in activities:
        ws.cell(row=row, column=1, value=activity.date.strftime('%Y-%m-%d')).border = border
        ws.cell(row=row, column=2, value='نشاط').border = border
        ws.cell(row=row, column=3, value=activity.name).border = border
        ws.cell(row=row, column=4, value=activity.description or '').border = border
        ws.cell(row=row, column=5, value=activity.time.strftime('%H:%M') if activity.time else '').border = border
        ws.cell(row=row, column=6, value=activity.location or '').border = border
        ws.cell(row=row, column=7, value=activity.committee.name if activity.committee else '').border = border
        ws.cell(row=row, column=8, value='').border = border
        row += 1

    # Adjust column widths
    for col in range(1, 9):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 20

    # Save to response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="calendar_{program.name}_{year}_{month}.xlsx"'

    wb.save(response)
    return response


@login_required
def export_calendar_pdf(request):
    """Export calendar as PDF file with Arabic support - includes all event types"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from io import BytesIO
        import os
        from django.conf import settings

        REPORTLAB_AVAILABLE = True
    except ImportError as e:
        print(f"❌ ReportLab import error: {e}")
        messages.error(request, 'مكتبة PDF غير متوفرة. الرجاء تثبيت reportlab')
        return redirect('schedule_calendar')

    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        ARABIC_TEXT_SUPPORT = True
    except ImportError:
        ARABIC_TEXT_SUPPORT = False
        print("⚠ Arabic text support libraries not found")

    def process_arabic_text(text):
        """Process Arabic text for proper RTL display"""
        if not text or not isinstance(text, str):
            return text or ''

        if not ARABIC_TEXT_SUPPORT:
            return text

        try:
            reshaper = arabic_reshaper.ArabicReshaper()
            reshaped_text = reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        except Exception as e:
            print(f"⚠ Arabic text processing error: {e}")
            return text

    def hex_to_rgb(hex_color):
        """Convert hex color to RGB tuple (0-1 scale)"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 3:
            hex_color = ''.join([c * 2 for c in hex_color])

        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b)

    # Get parameters
    program_id = request.GET.get('program_id')
    view_type = request.GET.get('view', 'monthly')
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))
    week = int(request.GET.get('week', timezone.now().isocalendar()[1]))

    program = get_object_or_404(Program, id=program_id)

    if not has_permission_for_program(request.user, program):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذا التقويم')
        return redirect('home')

    # Get date range
    if view_type == 'weekly':
        jan_1 = datetime(year, 1, 1).date()
        start_date = jan_1 + timedelta(weeks=week - 1)
        start_date = start_date - timedelta(days=(start_date.weekday() + 1) % 7)
        end_date = start_date + timedelta(days=6)
    else:
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, monthrange(year, month)[1]).date()

    # Get all types of events/tasks
    all_items = []

    # Schedule Events
    events = ScheduleEvent.objects.filter(
        program=program,
        start_date__gte=start_date,
        start_date__lte=end_date
    ).select_related('committee', 'created_by').order_by('start_date', 'start_time')

    for event in events:
        all_items.append({
            'date': event.start_date,
            'type': 'حدث',
            'title': event.title,
            'description': event.description,
            'committee': event.committee.name if event.committee else '',
            'item_type': 'event',
            'event_obj': event
        })

    # Tasks
    tasks = Task.objects.filter(
        program=program,
        due_date__gte=start_date,
        due_date__lte=end_date
    ).select_related('committee').order_by('due_date')

    for task in tasks:
        all_items.append({
            'date': task.due_date,
            'type': 'مهمة',
            'title': task.title,
            'description': task.description,
            'committee': task.committee.name if task.committee else '',
            'item_type': 'task',
            'event_obj': task
        })

    # Activities
    activities = Activity.objects.filter(
        program=program,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('committee').order_by('date')

    for activity in activities:
        all_items.append({
            'date': activity.date,
            'type': 'نشاط',
            'title': activity.name,
            'description': activity.description or '',
            'committee': activity.committee.name if activity.committee else '',
            'item_type': 'activity',
            'event_obj': activity
        })

    # Cultural Tasks
    cultural_tasks = CulturalTask.objects.filter(
        committee__program=program,
        due_date__gte=start_date,
        due_date__lte=end_date
    ).select_related('committee')

    for task in cultural_tasks:
        all_items.append({
            'date': task.due_date,
            'type': 'مهمة ثقافية',
            'title': task.title,
            'description': task.description or '',
            'committee': task.committee.name if task.committee else '',
            'item_type': 'cultural_task',
            'event_obj': task
        })

    # Task Sessions
    task_sessions = TaskSession.objects.filter(
        task__committee__program=program,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('task', 'task__committee')

    for session in task_sessions:
        all_items.append({
            'date': session.date,
            'type': 'جلسة مهمة',
            'title': session.title or f"جلسة {session.task.title}",
            'description': session.description or '',
            'committee': session.task.committee.name if session.task and session.task.committee else '',
            'item_type': 'task_session',
            'event_obj': session
        })

    # Operations Tasks
    operations_tasks = OperationsTask.objects.filter(
        committee__program=program,
        due_date__gte=start_date,
        due_date__lte=end_date
    ).select_related('committee')

    for task in operations_tasks:
        all_items.append({
            'date': task.due_date,
            'type': 'مهمة تشغيلية',
            'title': task.title,
            'description': task.description or '',
            'committee': task.committee.name if task.committee else '',
            'item_type': 'operations_task',
            'event_obj': task
        })

    # Scientific Tasks
    scientific_tasks = ScientificTask.objects.filter(
        committee__program=program,
        due_date__gte=start_date,
        due_date__lte=end_date
    ).select_related('committee')

    for task in scientific_tasks:
        all_items.append({
            'date': task.due_date,
            'type': 'مهمة علمية',
            'title': task.title,
            'description': task.description or '',
            'committee': task.committee.name if task.committee else '',
            'item_type': 'scientific_task',
            'event_obj': task
        })

    # Lectures
    lectures = Lecture.objects.filter(
        committee__program=program,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('committee', 'created_by')

    for lecture in lectures:
        all_items.append({
            'date': lecture.date,
            'type': 'محاضرة',
            'title': lecture.title,
            'description': lecture.description or '',
            'committee': lecture.committee.name if lecture.committee else '',
            'item_type': 'lecture',
            'event_obj': lecture
        })

    # Sharia Tasks
    sharia_tasks = ShariaTask.objects.filter(
        committee__program=program,
        due_date__gte=start_date,
        due_date__lte=end_date
    ).select_related('committee')

    for task in sharia_tasks:
        all_items.append({
            'date': task.due_date,
            'type': 'مهمة شرعية',
            'title': task.title,
            'description': task.description or '',
            'committee': task.committee.name if task.committee else '',
            'item_type': 'sharia_task',
            'event_obj': task
        })

    # Family Competitions
    family_competitions = FamilyCompetition.objects.filter(
        committee__program=program,
        start_date__lte=end_date,
        end_date__gte=start_date
    ).select_related('committee')

    for comp in family_competitions:
        all_items.append({
            'date': comp.start_date,
            'type': 'مسابقة أسرية',
            'title': comp.title,
            'description': comp.description or '',
            'committee': comp.committee.name if comp.committee else '',
            'item_type': 'family_competition',
            'event_obj': comp
        })

    # Sports Tasks
    sports_tasks = SportsTask.objects.filter(
        committee__program=program,
        due_date__gte=start_date,
        due_date__lte=end_date
    ).select_related('committee')

    for task in sports_tasks:
        all_items.append({
            'date': task.due_date,
            'type': 'مهمة رياضية',
            'title': task.title,
            'description': task.description or '',
            'committee': task.committee.name if task.committee else '',
            'item_type': 'sports_task',
            'event_obj': task
        })

    # Matches
    matches = Match.objects.filter(
        committee__program=program,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('committee', 'created_by')

    for match in matches:
        all_items.append({
            'date': match.date,
            'type': 'مباراة',
            'title': match.title,
            'description': match.description or '',
            'committee': match.committee.name if match.committee else '',
            'item_type': 'match',
            'event_obj': match
        })

    # Filter by committee if supervisor
    if request.user.role == 'committee_supervisor':
        try:
            committee = Committee.objects.get(supervisor=request.user)
            filtered_items = []
            for item in all_items:
                if item['committee'] == committee.name:
                    filtered_items.append(item)
            all_items = filtered_items
        except Committee.DoesNotExist:
            all_items = []

    # Sort all items by date
    all_items.sort(key=lambda x: x['date'])

    # Create PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="calendar_{program.name}_{year}_{month}.pdf"'

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm
    )

    # Try to register Arabic font
    arabic_font = 'Helvetica'
    try:
        font_paths = [
            os.path.join(settings.BASE_DIR, 'main', 'static', 'fonts', 'IBMPlexSansArabic-Regular.ttf'),
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            r'C:\Windows\Fonts\arial.ttf',
        ]

        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont('IBMPlexArabic', font_path))
                    arabic_font = 'IBMPlexArabic'
                    break
                except Exception as e:
                    continue
    except Exception as e:
        arabic_font = 'Helvetica'

    # Create styles
    styles = getSampleStyleSheet()

    primary_color = (0, 0.33, 0.67)

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=primary_color,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName=arabic_font,
    )

    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=11,
        textColor=(0, 0, 0),
        alignment=TA_CENTER,
        fontName=arabic_font,
        leading=14,
    )

    cell_style = ParagraphStyle(
        'CustomCell',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        fontName=arabic_font,
        leading=12,
    )

    legend_style = ParagraphStyle(
        'LegendStyle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=TA_RIGHT,
        fontName=arabic_font,
        spaceAfter=5,
    )

    # Build story
    story = []

    # Title
    title_text = process_arabic_text(f'تقويم {program.name} - {year}/{month}')
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 0.3 * cm))


    # Legend items as simple text
    legend_items = [
        ('اجتماع', '#8B5CF6'),
        ('مبيت', '#EC4899'),
        ('رحلة', '#10B981'),
        ('الثقافية', '#3B82F6'),
        ('الرياضية', '#0EA5E9'),
        ('العلمية', '#FB923C'),
        ('الشرعية', '#F59E0B'),
        ('التشغيلية', '#8B5A2B'),
        ('المهمات', '#6B7280'),
        ('النشاطات', '#10B981'),
        ('المباريات', '#EF4444'),
        ('المحاضرات', '#8B5CF6'),
        ('المسابقات', '#EC4899'),
    ]

    # Build table data with only 5 columns: التاريخ, النوع, العنوان, الوصف, اللجنة
    table_data = []

    # Header row (only 5 columns now)
    headers = ['التاريخ', 'النوع', 'العنوان', 'الوصف', 'اللجنة']
    table_data.append([Paragraph(process_arabic_text(header), header_style) for header in headers])

    # Add all items to table
    for item in all_items:
        row = []

        # Date
        date_str = item['date'].strftime('%Y-%m-%d')
        row.append(Paragraph(process_arabic_text(date_str), cell_style))

        # Type
        row.append(Paragraph(process_arabic_text(item['type']), cell_style))

        # Title
        title = item['title'][:30] + '...' if len(item['title']) > 30 else item['title']
        row.append(Paragraph(process_arabic_text(title), cell_style))

        # Description
        desc = item['description'][:40] + '...' if len(item['description']) > 40 else item['description']
        row.append(Paragraph(process_arabic_text(desc), cell_style))

        # Committee
        row.append(Paragraph(process_arabic_text(item['committee']), cell_style))

        table_data.append(row)

    # Create table with 5 columns
    col_widths = [2.5 * cm, 2.5 * cm, 4.5 * cm, 5 * cm, 3 * cm]
    table = Table(table_data, colWidths=col_widths, repeatRows=1)

    # Style table
    table_style = [
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), (0.21, 0.38, 0.57)),
        ('TEXTCOLOR', (0, 0), (-1, 0), (1, 1, 1)),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), arabic_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),

        # Data rows
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, (0.7, 0.7, 0.7)),
        ('FONTNAME', (0, 1), (-1, -1), arabic_font),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]

    # Add alternating row colors for better readability
    for row_idx in range(1, len(table_data)):
        if row_idx % 2 == 0:
            table_style.append(('BACKGROUND', (0, row_idx), (-1, row_idx), (0.95, 0.95, 0.95)))

    table.setStyle(TableStyle(table_style))
    story.append(table)

    # Add summary
    story.append(Spacer(1, 0.5 * cm))
    summary_text = process_arabic_text(f'إجمالي العناصر: {len(all_items)}')
    summary_style = ParagraphStyle(
        'SummaryStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        fontName=arabic_font,
        spaceBefore=10,
    )
    story.append(Paragraph(summary_text, summary_style))

    # Build PDF
    doc.build(story)

    return response
