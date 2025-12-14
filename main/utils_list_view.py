from django.utils import timezone
from datetime import datetime, timedelta


def get_date_range_for_view(request):
    """
    Get date range from request parameters or return default (current month)

    Args:
        request: Django request object

    Returns:
        tuple: (date_from, date_to)
    """
    today = timezone.now().date()

    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')

    if date_from_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            date_from = today.replace(day=1)
    else:
        date_from = today.replace(day=1)

    if date_to_str:
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            date_to = get_end_of_month(today)
    else:
        date_to = get_end_of_month(today)

    return date_from, date_to


def get_end_of_month(date):
    """
    Get the last day of the month for a given date

    Args:
        date: datetime.date object

    Returns:
        datetime.date: Last day of the month
    """
    if date.month == 12:
        return date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        return date.replace(month=date.month + 1, day=1) - timedelta(days=1)


def calculate_task_statistics(calendar_tasks, program_tasks, cultural_tasks,
                              scientific_tasks, operations_tasks, sharia_tasks,
                              sports_tasks):
    """
    Calculate statistics for all task types

    Returns:
        dict: Statistics including total, completed, pending, and overdue counts
    """
    today = timezone.now().date()

    total_tasks = (
            calendar_tasks.count() +
            program_tasks.count() +
            cultural_tasks.count() +
            scientific_tasks.count() +
            operations_tasks.count() +
            sharia_tasks.count() +
            sports_tasks.count()
    )

    completed_tasks = (
            calendar_tasks.filter(status='completed').count() +
            program_tasks.filter(status='completed').count() +
            cultural_tasks.filter(status='completed').count() +
            scientific_tasks.filter(status='completed').count() +
            operations_tasks.filter(status='completed').count() +
            sharia_tasks.filter(status='completed').count() +
            sports_tasks.filter(status='completed').count()
    )

    pending_tasks = (
            calendar_tasks.filter(status__in=['pending', 'in_progress']).count() +
            program_tasks.filter(status__in=['pending', 'in_progress']).count() +
            cultural_tasks.filter(status__in=['pending', 'in_progress']).count() +
            scientific_tasks.filter(status__in=['pending', 'in_progress']).count() +
            operations_tasks.filter(status__in=['pending', 'in_progress']).count() +
            sharia_tasks.filter(status__in=['pending', 'in_progress']).count() +
            sports_tasks.filter(status__in=['pending', 'in_progress']).count()
    )

    overdue_tasks = (
            program_tasks.filter(due_date__lt=today, status__in=['pending', 'in_progress']).count() +
            cultural_tasks.filter(due_date__lt=today, status__in=['pending', 'in_progress']).count() +
            scientific_tasks.filter(due_date__lt=today, status__in=['pending', 'in_progress']).count() +
            operations_tasks.filter(due_date__lt=today, status__in=['pending', 'in_progress']).count() +
            sharia_tasks.filter(due_date__lt=today, status__in=['pending', 'in_progress']).count() +
            sports_tasks.filter(due_date__lt=today, status__in=['pending', 'in_progress']).count()
    )

    return {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
    }


def filter_tasks_by_user_role(user, program_tasks, activities, cultural_tasks,
                              scientific_tasks, operations_tasks, sharia_tasks,
                              sports_tasks):
    """
    Filter tasks based on user role and permissions

    Returns:
        dict: Filtered querysets for each task type
    """
    if user.role == 'program_manager':
        try:
            from director_dashboard.models import Program
            program = Program.objects.get(manager=user)

            program_tasks = program_tasks.filter(program=program)
            activities = activities.filter(program=program)
            cultural_tasks = cultural_tasks.filter(committee__program=program)
            scientific_tasks = scientific_tasks.filter(committee__program=program)
            operations_tasks = operations_tasks.filter(committee__program=program)
            sharia_tasks = sharia_tasks.filter(committee__program=program)
            sports_tasks = sports_tasks.filter(committee__program=program)
        except Exception:
            pass

    elif user.role == 'committee_supervisor':
        try:
            from director_dashboard.models import Committee
            committee = Committee.objects.get(supervisor=user)

            program_tasks = program_tasks.filter(committee=committee)
            activities = activities.filter(committee=committee)

            # Filter based on supervisor type
            if user.supervisor_type == 'cultural':
                cultural_tasks = cultural_tasks.filter(committee=committee)
                scientific_tasks = scientific_tasks.none()
                operations_tasks = operations_tasks.none()
                sharia_tasks = sharia_tasks.none()
                sports_tasks = sports_tasks.none()
            elif user.supervisor_type == 'scientific':
                scientific_tasks = scientific_tasks.filter(committee=committee)
                cultural_tasks = cultural_tasks.none()
                operations_tasks = operations_tasks.none()
                sharia_tasks = sharia_tasks.none()
                sports_tasks = sports_tasks.none()
            elif user.supervisor_type == 'operations':
                operations_tasks = operations_tasks.filter(committee=committee)
                cultural_tasks = cultural_tasks.none()
                scientific_tasks = scientific_tasks.none()
                sharia_tasks = sharia_tasks.none()
                sports_tasks = sports_tasks.none()
            elif user.supervisor_type == 'sharia':
                sharia_tasks = sharia_tasks.filter(committee=committee)
                cultural_tasks = cultural_tasks.none()
                scientific_tasks = scientific_tasks.none()
                operations_tasks = operations_tasks.none()
                sports_tasks = sports_tasks.none()
            elif user.supervisor_type == 'sports':
                sports_tasks = sports_tasks.filter(committee=committee)
                cultural_tasks = cultural_tasks.none()
                scientific_tasks = scientific_tasks.none()
                operations_tasks = operations_tasks.none()
                sharia_tasks = sharia_tasks.none()
        except Exception:
            pass

    return {
        'program_tasks': program_tasks,
        'activities': activities,
        'cultural_tasks': cultural_tasks,
        'scientific_tasks': scientific_tasks,
        'operations_tasks': operations_tasks,
        'sharia_tasks': sharia_tasks,
        'sports_tasks': sports_tasks,
    }


def get_task_color_by_type(task_type):
    """
    Get color for task type to maintain consistency with calendar view

    Args:
        task_type: String representing the task type

    Returns:
        str: Hex color code
    """
    colors = {
        'calendar_task': '#8B5CF6',  # Purple
        'program_task': '#3B82F6',  # Blue
        'activity': '#10B981',  # Green
        'cultural_task': '#EC4899',  # Pink
        'scientific_task': '#FB923C',  # Orange
        'operations_task': '#8B5CF6',  # Purple
        'sharia_task': '#F59E0B',  # Amber
        'sports_task': '#0EA5E9',  # Sky blue
    }
    return colors.get(task_type, '#6B7280')  # Default gray


def format_task_for_export(task, task_type):
    """
    Format task data for export (Excel/PDF)

    Args:
        task: Task object
        task_type: String representing task type

    Returns:
        dict: Formatted task data
    """
    data = {
        'title': task.title,
        'type': task_type,
        'status': task.get_status_display() if hasattr(task, 'get_status_display') else str(task.status),
        'description': task.description if hasattr(task, 'description') else '',
    }

    # Add date based on task type
    if hasattr(task, 'due_date'):
        data['date'] = task.due_date.strftime('%Y-%m-%d')
    elif hasattr(task, 'date'):
        data['date'] = task.date.strftime('%Y-%m-%d')
    elif hasattr(task, 'date_start'):
        data['date'] = task.date_start.strftime('%Y-%m-%d')

    # Add committee if available
    if hasattr(task, 'committee') and task.committee:
        data['committee'] = task.committee.name

    # Add priority if available
    if hasattr(task, 'priority'):
        data['priority'] = task.get_priority_display() if hasattr(task, 'get_priority_display') else str(task.priority)

    return data


def get_tasks_grouped_by_date(tasks_dict):
    """
    Group tasks by date for timeline view

    Args:
        tasks_dict: Dictionary containing all task querysets

    Returns:
        dict: Tasks grouped by date
    """
    from collections import defaultdict

    grouped = defaultdict(list)

    # Process each task type
    for task_type, tasks in tasks_dict.items():
        for task in tasks:
            # Get appropriate date field
            if hasattr(task, 'due_date'):
                date = task.due_date
            elif hasattr(task, 'date'):
                date = task.date
            elif hasattr(task, 'date_start'):
                date = task.date_start.date() if hasattr(task.date_start, 'date') else task.date_start
            else:
                continue

            grouped[date].append({
                'task': task,
                'type': task_type
            })

    # Sort by date
    return dict(sorted(grouped.items()))