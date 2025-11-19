from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from director_dashboard.models import Program, Committee, Student
from accounts.models import User, UserActivity
from .models import Task, Activity, StudentAttendance, Notification
from .forms import CommitteeForm, TaskForm, ActivityForm, AttendanceForm


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def pm_dashboard(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # Get user's program
    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    # Statistics
    total_committees = Committee.objects.filter(program=program).count()
    total_students = Student.objects.filter(program=program).count()
    total_tasks = Task.objects.filter(program=program).count()
    pending_tasks = Task.objects.filter(program=program, status='pending').count()

    # Recent activities
    recent_activities = Activity.objects.filter(program=program).order_by('-created_at')[:5]

    # Overdue tasks
    overdue_tasks = Task.objects.filter(
        program=program,
        due_date__lt=timezone.now().date(),
        status='pending'
    ).count()

    # Update overdue tasks status
    Task.objects.filter(
        program=program,
        due_date__lt=timezone.now().date(),
        status='pending'
    ).update(status='overdue')

    # Unread notifications
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    # Committee progress
    committees = Committee.objects.filter(program=program).annotate(
        student_count=Count('student'),
        avg_progress=Avg('student__progress')
    )

    context = {
        'program': program,
        'total_committees': total_committees,
        'total_students': total_students,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_activities': recent_activities,
        'unread_notifications': unread_notifications,
        'committees': committees,
    }
    return render(request, 'program_manager/dashboard.html', context)


@login_required
def program_info(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    # Program statistics
    total_committees = Committee.objects.filter(program=program).count()
    total_students = Student.objects.filter(program=program).count()
    avg_progress = Student.objects.filter(program=program).aggregate(avg=Avg('progress'))['avg'] or 0

    context = {
        'program': program,
        'total_committees': total_committees,
        'total_students': total_students,
        'avg_progress': round(avg_progress, 1),
    }
    return render(request, 'program_manager/program_info.html', context)


@login_required
def committee_management(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    committees = Committee.objects.filter(program=program).select_related('supervisor').annotate(
        student_count=Count('student'),
        avg_progress=Avg('student__progress')
    )

    context = {
        'program': program,
        'committees': committees,
    }
    return render(request, 'program_manager/committee_management.html', context)


@login_required
def add_committee(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = CommitteeForm(request.POST, program=program)
        if form.is_valid():
            committee = form.save(commit=False)
            committee.program = program
            committee.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة لجنة جديدة: {committee.name}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة اللجنة بنجاح!')
            return redirect('pm_committee_management')
    else:
        form = CommitteeForm(program=program)

    context = {
        'program': program,
        'form': form,
        'title': 'إضافة لجنة جديدة'
    }
    return render(request, 'program_manager/committee_form.html', context)


@login_required
def edit_committee(request, committee_id):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    committee = get_object_or_404(Committee, id=committee_id, program=program)

    if request.method == 'POST':
        form = CommitteeForm(request.POST, instance=committee, program=program)
        if form.is_valid():
            committee = form.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل اللجنة: {committee.name}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل اللجنة بنجاح!')
            return redirect('pm_committee_management')
    else:
        form = CommitteeForm(instance=committee, program=program)

    context = {
        'program': program,
        'form': form,
        'committee': committee,
        'title': 'تعديل اللجنة'
    }
    return render(request, 'program_manager/committee_form.html', context)


@login_required
def delete_committee(request, committee_id):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    committee = get_object_or_404(Committee, id=committee_id, program=program)

    if request.method == 'POST':
        committee_name = committee.name
        committee.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف اللجنة: {committee_name}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف اللجنة بنجاح!')
        return redirect('pm_committee_management')

    context = {
        'program': program,
        'object': committee,
        'type': 'لجنة'
    }
    return render(request, 'program_manager/confirm_delete.html', context)


@login_required
def task_management(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    # Update overdue tasks
    Task.objects.filter(
        program=program,
        due_date__lt=timezone.now().date(),
        status='pending'
    ).update(status='overdue')

    tasks = Task.objects.filter(program=program).select_related('committee', 'assigned_to').order_by('-created_at')

    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    context = {
        'program': program,
        'tasks': tasks,
        'status_filter': status_filter,
    }
    return render(request, 'program_manager/task_management.html', context)


from scientific_committee_dashboard.models import ScientificTask,ScientificNotification
from sports_committee_dashboard.models import SportsTask,SportsNotification
from sharia_committee_dashboard.models import ShariaTask,ShariaNotification
from cultural_committee_dashboard.models import CulturalNotification,CulturalTask
from operations_committee_dashboard.models import OperationsTask,OperationsNotification
@login_required
def add_task(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = TaskForm(request.POST, program=program)
        if form.is_valid():
            task_data = form.cleaned_data

            # Check if this is a scientific committee task
            committee = task_data.get('committee')
            assigned_to = task_data.get('assigned_to')

            is_scientific_committee = (
                    committee and
                    assigned_to and
                    assigned_to.role == 'committee_supervisor' and
                    assigned_to.supervisor_type == 'scientific'
            )

            if is_scientific_committee:
                # Create ScientificTask instead of regular Task
                scientific_task = ScientificTask.objects.create(
                    committee=committee,
                    task_type='other',  # Default type, you might want to add a field for this
                    title=f"مهمة من المدير: {task_data['title']}",
                    description=task_data['description'],
                    assigned_to=assigned_to,
                    status='pending',
                    due_date=task_data['due_date'],
                    created_by=request.user
                )

                # Create scientific notification
                ScientificNotification.objects.create(
                    user=assigned_to,
                    committee=committee,
                    notification_type='task_added',
                    title='مهمة جديدة من مدير البرنامج',
                    message=f'تم تعيين مهمة جديدة لك من مدير البرنامج: {task_data["title"]}',
                    related_task=scientific_task
                )

                UserActivity.objects.create(
                    user=request.user,
                    action=f'إضافة مهمة علمية: {task_data["title"]}',
                    ip_address=get_client_ip(request)
                )

                messages.success(request, 'تم إضافة المهمة العلمية بنجاح!')

            is_sports_committee = (
                    committee and
                    assigned_to and
                    assigned_to.role == 'committee_supervisor' and
                    assigned_to.supervisor_type == 'sports'
            )

            is_cultural_committee = (
                    committee and
                    assigned_to and
                    assigned_to.role == 'committee_supervisor' and
                    assigned_to.supervisor_type == 'cultural'
            )

            if is_cultural_committee:
                # Create CulturalTask instead of regular Task
                cultural_task = CulturalTask.objects.create(
                    committee=committee,
                    task_type='other',  # Default type for program manager tasks
                    title=f"مهمة من مدير البرنامج: {task_data['title']}",
                    description=task_data['description'],
                    assigned_to=assigned_to,
                    status='pending',
                    due_date=task_data['due_date'],
                    created_by=request.user
                )

                # Create notification for cultural committee supervisor
                CulturalNotification.objects.create(
                    user=assigned_to,
                    committee=committee,
                    notification_type='task_added',
                    title='مهمة جديدة من مدير البرنامج',
                    message=f'تم تعيين مهمة جديدة لك من مدير البرنامج: {task_data["title"]}',
                    related_task=cultural_task
                )

                # Also create regular Task for tracking in program manager dashboard
                task = form.save(commit=False)
                task.program = program
                task.created_by = request.user
                task.is_cultural_task = True  # Add this field to your Task model
                task.cultural_task_ref = cultural_task  # Add this field to your Task model
                task.save()

                UserActivity.objects.create(
                    user=request.user,
                    action=f'إضافة مهمة ثقافية: {task_data["title"]}',
                    ip_address=get_client_ip(request)
                )

                messages.success(request, 'تم إضافة المهمة الثقافية بنجاح!')

            if is_sports_committee:
                # Create SportsTask for sports committee
                sports_task = SportsTask.objects.create(
                    committee=committee,
                    task_type='other',  # Default type for program manager tasks
                    title=f"مهمة من المدير: {task_data['title']}",
                    description=task_data['description'],
                    assigned_to_name=assigned_to.get_full_name() if assigned_to else "غير محدد",
                    status='pending',
                    due_date=task_data['due_date'],
                    created_by=request.user
                )

                # Create notification for sports committee supervisor
                SportsNotification.objects.create(
                    user=assigned_to,
                    committee=committee,
                    notification_type='task_added',
                    title='مهمة جديدة من مدير البرنامج',
                    message=f'تم تعيين مهمة جديدة لك من مدير البرنامج: {task_data["title"]}',
                    related_task=sports_task
                )

                # Also create regular Task for tracking
                task = form.save(commit=False)
                task.program = program
                task.created_by = request.user
                task.is_sports_task = True  # Add this field to your Task model
                task.sports_task_ref = sports_task  # Add this field to your Task model
                task.save()

                UserActivity.objects.create(
                    user=request.user,
                    action=f'إضافة مهمة رياضية: {task_data["title"]}',
                    ip_address=get_client_ip(request)
                )

                messages.success(request, 'تم إضافة المهمة الرياضية بنجاح!')

            is_operations_committee = (
                    committee and
                    assigned_to and
                    assigned_to.role == 'committee_supervisor' and
                    assigned_to.supervisor_type == 'operations'
            )

            if is_operations_committee:
                # Create OperationsTask instead of regular Task
                operations_task = OperationsTask.objects.create(
                    committee=committee,
                    task_type='other',  # Default type for program manager tasks
                    title=f"مهمة من مدير البرنامج: {task_data['title']}",
                    description=task_data['description'],
                    assigned_to=assigned_to,
                    status='not_started',  # Use operations committee status
                    priority=task_data.get('priority', 'medium'),
                    due_date=task_data['due_date'],
                    created_by=request.user
                )

                # Create operations notification for the supervisor
                OperationsNotification.objects.create(
                    user=assigned_to,
                    committee=committee,
                    notification_type='task_added',
                    title='مهمة جديدة من مدير البرنامج',
                    message=f'تم تعيين مهمة جديدة لك من مدير البرنامج: {task_data["title"]}',
                    related_task=operations_task
                )

                # Also create regular Task for tracking in program manager dashboard
                task = form.save(commit=False)
                task.program = program
                task.created_by = request.user
                task.is_operations_task = True  # Add this field to your Task model
                task.operations_task_ref = operations_task  # Add this field to your Task model
                task.save()

                # Create notification for the assigned user (if different from supervisor)
                if assigned_to:
                    Notification.objects.create(
                        user=assigned_to,
                        notification_type='task_added',
                        title='مهمة جديدة',
                        message=f'تم تعيين مهمة جديدة لك: {task_data["title"]}',
                        related_task=task
                    )

                UserActivity.objects.create(
                    user=request.user,
                    action=f'إضافة مهمة تشغيلية: {task_data["title"]}',
                    ip_address=get_client_ip(request)
                )

                messages.success(request, 'تم إضافة المهمة التشغيلية بنجاح!')

            is_sharia_committee = (
                    committee and
                    assigned_to and
                    assigned_to.role == 'committee_supervisor' and
                    assigned_to.supervisor_type == 'sharia'
            )

            if is_sharia_committee:
                # Create ShariaTask instead of regular Task
                sharia_task = ShariaTask.objects.create(
                    committee=committee,
                    task_type='other',  # Default type for program manager tasks
                    title=f"مهمة من مدير البرنامج: {task_data['title']}",
                    description=task_data['description'],
                    assigned_to=assigned_to,
                    status='pending',
                    due_date=task_data['due_date'],
                    created_by=request.user
                )

                # Create sharia notification for the supervisor
                ShariaNotification.objects.create(
                    user=assigned_to,
                    committee=committee,
                    notification_type='task_added',
                    title='مهمة جديدة من مدير البرنامج',
                    message=f'تم تعيين مهمة جديدة لك من مدير البرنامج: {task_data["title"]}',
                    related_task=sharia_task
                )

                # Also create regular Task for tracking in program manager dashboard
                task = form.save(commit=False)
                task.program = program
                task.created_by = request.user
                task.is_sharia_task = True  # Add this field to your Task model
                task.sharia_task_ref = sharia_task  # Add this field to your Task model
                task.save()

                UserActivity.objects.create(
                    user=request.user,
                    action=f'إضافة مهمة شرعية: {task_data["title"]}',
                    ip_address=get_client_ip(request)
                )

                messages.success(request, 'تم إضافة المهمة الشرعية بنجاح!')

            else:
                # Create regular task
                task = form.save(commit=False)
                task.program = program
                task.created_by = request.user
                task.save()

                # Create notification for regular task
                if task.assigned_to:
                    Notification.objects.create(
                        user=task.assigned_to,
                        notification_type='task_added',
                        title='مهمة جديدة',
                        message=f'تم تعيين مهمة جديدة لك: {task.title}',
                        related_task=task
                    )

                UserActivity.objects.create(
                    user=request.user,
                    action=f'إضافة مهمة جديدة: {task.title}',
                    ip_address=get_client_ip(request)
                )

                messages.success(request, 'تم إضافة المهمة بنجاح!')

            return redirect('pm_task_management')
    else:
        form = TaskForm(program=program)

    context = {
        'program': program,
        'form': form,
        'title': 'إضافة مهمة جديدة'
    }
    return render(request, 'program_manager/task_form.html', context)


@login_required
def edit_task(request, task_id):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    task = get_object_or_404(Task, id=task_id, program=program)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, program=program)
        if form.is_valid():
            task = form.save()

            # Handle scientific committee task updates
            if task.is_scientific_task and task.scientific_task_ref:
                scientific_task = task.scientific_task_ref
                scientific_task.title = f"مهمة من مدير البرنامج: {task.title}"
                scientific_task.description = task.description
                scientific_task.due_date = task.due_date
                scientific_task.status = task.status
                scientific_task.save()

                # Create notification for the update
                ScientificNotification.objects.create(
                    user=scientific_task.assigned_to,
                    committee=scientific_task.committee,
                    notification_type='task_updated',
                    title='تم تعديل المهمة',
                    message=f'تم تعديل المهمة من مدير البرنامج: {task.title}',
                    related_task=scientific_task
                )

            elif task.is_cultural_task and task.cultural_task_ref:
                cultural_task = task.cultural_task_ref
                cultural_task.title = f"مهمة من مدير البرنامج: {task.title}"
                cultural_task.description = task.description
                cultural_task.due_date = task.due_date
                cultural_task.status = task.status
                cultural_task.assigned_to = task.assigned_to
                cultural_task.save()

                # Create notification for the update
                CulturalNotification.objects.create(
                    user=cultural_task.assigned_to,
                    committee=cultural_task.committee,
                    notification_type='task_updated',
                    title='تم تعديل المهمة',
                    message=f'تم تعديل المهمة من مدير البرنامج: {task.title}',
                    related_task=cultural_task
                )

            # Handle sharia committee task updates
            elif task.is_sharia_task and task.sharia_task_ref:
                sharia_task = task.sharia_task_ref
                sharia_task.title = f"مهمة من مدير البرنامج: {task.title}"
                sharia_task.description = task.description
                sharia_task.due_date = task.due_date
                sharia_task.status = task.status
                sharia_task.save()

                # Create notification for the update
                ShariaNotification.objects.create(
                    user=sharia_task.assigned_to,
                    committee=sharia_task.committee,
                    notification_type='task_updated',
                    title='تم تعديل المهمة',
                    message=f'تم تعديل المهمة من مدير البرنامج: {task.title}',
                    related_task=sharia_task
                )

            # Handle sports committee task updates
            elif task.is_sports_task and task.sports_task_ref:
                sports_task = task.sports_task_ref
                sports_task.title = f"مهمة من مدير البرنامج: {task.title}"
                sports_task.description = task.description
                sports_task.due_date = task.due_date
                sports_task.status = task.status
                sports_task.assigned_to_name = task.assigned_to.get_full_name() if task.assigned_to else "غير محدد"
                sports_task.save()

                # Create notification for the update
                SportsNotification.objects.create(
                    user=task.assigned_to,
                    committee=sports_task.committee,
                    notification_type='task_updated',
                    title='تم تعديل المهمة',
                    message=f'تم تعديل المهمة من مدير البرنامج: {task.title}',
                    related_task=sports_task
                )

            elif task.is_operations_task and task.operations_task_ref:
                operations_task = task.operations_task_ref
                operations_task.title = f"مهمة من مدير البرنامج: {task.title}"
                operations_task.description = task.description
                operations_task.due_date = task.due_date
                operations_task.status = 'not_started' if task.status == 'pending' else task.status
                operations_task.priority = task.priority
                operations_task.assigned_to = task.assigned_to
                operations_task.save()

                # Create notification for the update
                OperationsNotification.objects.create(
                    user=operations_task.assigned_to,
                    committee=operations_task.committee,
                    notification_type='task_updated',
                    title='تم تعديل المهمة',
                    message=f'تم تعديل المهمة من مدير البرنامج: {task.title}',
                    related_task=operations_task
                )

            # Handle regular task notifications
            elif task.assigned_to:
                Notification.objects.create(
                    user=task.assigned_to,
                    notification_type='task_updated',
                    title='تم تعديل المهمة',
                    message=f'تم تعديل المهمة: {task.title}',
                    related_task=task
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل المهمة: {task.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل المهمة بنجاح!')
            return redirect('pm_task_management')
    else:
        form = TaskForm(instance=task, program=program)

    context = {
        'program': program,
        'form': form,
        'task': task,
        'title': 'تعديل المهمة'
    }
    return render(request, 'program_manager/task_form.html', context)


@login_required
def delete_task(request, task_id):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    task = get_object_or_404(Task, id=task_id, program=program)

    if request.method == 'POST':
        task_title = task.title

        # Handle scientific committee task deletion
        if task.is_scientific_task and task.scientific_task_ref:
            scientific_task = task.scientific_task_ref

            # Create notification before deletion
            ScientificNotification.objects.create(
                user=scientific_task.assigned_to,
                committee=scientific_task.committee,
                notification_type='task_updated',
                title='تم حذف المهمة',
                message=f'تم حذف المهمة من مدير البرنامج: {task_title}'
            )

            scientific_task.delete()

        elif task.is_cultural_task and task.cultural_task_ref:
            cultural_task = task.cultural_task_ref

            # Create notification before deletion
            CulturalNotification.objects.create(
                user=cultural_task.assigned_to,
                committee=cultural_task.committee,
                notification_type='task_updated',
                title='تم حذف المهمة',
                message=f'تم حذف المهمة من مدير البرنامج: {task_title}'
            )

            cultural_task.delete()

        # Handle sharia committee task deletion
        elif task.is_sharia_task and task.sharia_task_ref:
            sharia_task = task.sharia_task_ref

            # Create notification before deletion
            ShariaNotification.objects.create(
                user=sharia_task.assigned_to,
                committee=sharia_task.committee,
                notification_type='task_updated',
                title='تم حذف المهمة',
                message=f'تم حذف المهمة من مدير البرنامج: {task_title}'
            )

            sharia_task.delete()

        elif task.is_operations_task and task.operations_task_ref:
            operations_task = task.operations_task_ref

            # Create notification before deletion
            OperationsNotification.objects.create(
                user=operations_task.assigned_to,
                committee=operations_task.committee,
                notification_type='task_updated',
                title='تم حذف المهمة',
                message=f'تم حذف المهمة من مدير البرنامج: {task_title}'
            )

            operations_task.delete()

        # Handle sports committee task deletion
        elif task.is_sports_task and task.sports_task_ref:
            sports_task = task.sports_task_ref

            # Create notification before deletion
            SportsNotification.objects.create(
                user=task.assigned_to,
                committee=sports_task.committee,
                notification_type='task_updated',
                title='تم حذف المهمة',
                message=f'تم حذف المهمة من مدير البرنامج: {task_title}'
            )

            sports_task.delete()

        # Handle regular task notifications
        elif task.assigned_to:
            Notification.objects.create(
                user=task.assigned_to,
                notification_type='task_updated',
                title='تم حذف المهمة',
                message=f'تم حذف المهمة: {task_title}'
            )

        task.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف المهمة: {task_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف المهمة بنجاح!')
        return redirect('pm_task_management')

    context = {
        'program': program,
        'object': task,
        'type': 'مهمة'
    }
    return render(request, 'program_manager/confirm_delete.html', context)


@login_required
def activity_management(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    activities = Activity.objects.filter(program=program).select_related('committee').order_by('-date', '-time')

    context = {
        'program': program,
        'activities': activities,
    }
    return render(request, 'program_manager/activity_management.html', context)


@login_required
def add_activity(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = ActivityForm(request.POST, program=program)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.program = program
            activity.created_by = request.user
            activity.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة نشاط جديد: {activity.name}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة النشاط بنجاح!')
            return redirect('pm_activity_management')
    else:
        form = ActivityForm(program=program)

    context = {
        'program': program,
        'form': form,
        'title': 'إضافة نشاط جديد'
    }
    return render(request, 'program_manager/activity_form.html', context)


@login_required
def reports(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    # Committee statistics with task counts and completion percentages
    committees = Committee.objects.filter(program=program).annotate(
        student_count=Count('student')
    ).select_related('supervisor').order_by('-student_count')

    # Convert to list so we can modify the objects
    committees_list = list(committees)

    # Calculate statistics for each committee based on supervisor type
    for committee in committees_list:
        supervisor = committee.supervisor

        # Default values
        committee.task_count = 0
        committee.completed_tasks = 0
        committee.pending_tasks = 0
        committee.overdue_tasks = 0
        committee.avg_progress = 0

        if supervisor and supervisor.supervisor_type:
            # Query the appropriate task model based on supervisor type
            if supervisor.supervisor_type == 'cultural':
                from cultural_committee_dashboard.models import CulturalTask
                tasks = CulturalTask.objects.filter(committee=committee)
                committee.task_count = tasks.count()
                committee.completed_tasks = tasks.filter(status='completed').count()
                committee.pending_tasks = tasks.filter(status='pending').count()
                committee.overdue_tasks = 0  # Cultural tasks don't have overdue status

            elif supervisor.supervisor_type == 'sports':
                from sports_committee_dashboard.models import SportsTask
                tasks = SportsTask.objects.filter(committee=committee)
                committee.task_count = tasks.count()
                committee.completed_tasks = tasks.filter(status='completed').count()
                committee.pending_tasks = tasks.filter(status='pending').count()
                committee.overdue_tasks = tasks.filter(status='overdue').count()

            elif supervisor.supervisor_type == 'sharia':
                from sharia_committee_dashboard.models import ShariaTask
                tasks = ShariaTask.objects.filter(committee=committee)
                committee.task_count = tasks.count()
                committee.completed_tasks = tasks.filter(status='completed').count()
                committee.pending_tasks = tasks.filter(status='pending').count()
                committee.overdue_tasks = 0  # Sharia tasks don't have overdue status

            elif supervisor.supervisor_type == 'scientific':
                from scientific_committee_dashboard.models import ScientificTask
                tasks = ScientificTask.objects.filter(committee=committee)
                committee.task_count = tasks.count()
                committee.completed_tasks = tasks.filter(status='completed').count()
                committee.pending_tasks = tasks.filter(status='pending').count()
                committee.overdue_tasks = 0  # Scientific tasks don't have overdue status

            elif supervisor.supervisor_type == 'operations':
                from operations_committee_dashboard.models import OperationsTask
                tasks = OperationsTask.objects.filter(committee=committee)
                committee.task_count = tasks.count()
                committee.completed_tasks = tasks.filter(status='completed').count()
                committee.pending_tasks = tasks.filter(status__in=['not_started', 'in_progress']).count()
                committee.overdue_tasks = tasks.filter(status='overdue').count()
            else:
                # Fallback to generic Task model
                tasks = Task.objects.filter(committee=committee)
                committee.task_count = tasks.count()
                committee.completed_tasks = tasks.filter(status='completed').count()
                committee.pending_tasks = tasks.filter(status='pending').count()
                committee.overdue_tasks = tasks.filter(status='overdue').count()

            # Calculate average progress based on completion_percentage
            if tasks.exists():
                total_completion = sum(task.completion_percentage for task in tasks)
                committee.avg_progress = round(total_completion / tasks.count(), 1)
            else:
                # If no tasks, calculate based on completed vs total
                if committee.task_count > 0:
                    committee.avg_progress = round((committee.completed_tasks / committee.task_count) * 100, 1)
                else:
                    committee.avg_progress = 0
        else:
            # No supervisor or supervisor type - use generic Task model
            tasks = Task.objects.filter(committee=committee)
            committee.task_count = tasks.count()
            committee.completed_tasks = tasks.filter(status='completed').count()
            committee.pending_tasks = tasks.filter(status='pending').count()
            committee.overdue_tasks = tasks.filter(status='overdue').count()

            if tasks.exists():
                total_completion = sum(task.completion_percentage for task in tasks)
                committee.avg_progress = round(total_completion / tasks.count(), 1)
            else:
                if committee.task_count > 0:
                    committee.avg_progress = round((committee.completed_tasks / committee.task_count) * 100, 1)
                else:
                    committee.avg_progress = 0

    # Weekly/Monthly data - need to count all task types
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Count tasks from all models
    from cultural_committee_dashboard.models import CulturalTask
    from sports_committee_dashboard.models import SportsTask
    from sharia_committee_dashboard.models import ShariaTask
    from scientific_committee_dashboard.models import ScientificTask
    from operations_committee_dashboard.models import OperationsTask

    weekly_tasks = (
            Task.objects.filter(program=program, created_at__gte=week_ago).count() +
            CulturalTask.objects.filter(committee__program=program, created_at__gte=week_ago).count() +
            SportsTask.objects.filter(committee__program=program, created_at__gte=week_ago).count() +
            ShariaTask.objects.filter(committee__program=program, created_at__gte=week_ago).count() +
            ScientificTask.objects.filter(committee__program=program, created_at__gte=week_ago).count() +
            OperationsTask.objects.filter(committee__program=program, created_at__gte=week_ago).count()
    )

    monthly_tasks = (
            Task.objects.filter(program=program, created_at__gte=month_ago).count() +
            CulturalTask.objects.filter(committee__program=program, created_at__gte=month_ago).count() +
            SportsTask.objects.filter(committee__program=program, created_at__gte=month_ago).count() +
            ShariaTask.objects.filter(committee__program=program, created_at__gte=month_ago).count() +
            ScientificTask.objects.filter(committee__program=program, created_at__gte=month_ago).count() +
            OperationsTask.objects.filter(committee__program=program, created_at__gte=month_ago).count()
    )

    weekly_activities = Activity.objects.filter(program=program, date__gte=week_ago).count()
    monthly_activities = Activity.objects.filter(program=program, date__gte=month_ago).count()

    # Top committees (best performing based on task completion)
    top_committees = sorted(committees_list, key=lambda c: c.avg_progress, reverse=True)[:10]

    # Top students (keep student progress as is)
    top_students = Student.objects.filter(program=program).select_related('user', 'committee').order_by('-progress')[
        :10]

    context = {
        'program': program,
        'committees': committees_list,
        'weekly_tasks': weekly_tasks,
        'monthly_tasks': monthly_tasks,
        'weekly_activities': weekly_activities,
        'monthly_activities': monthly_activities,
        'top_committees': top_committees,
        'top_students': top_students,
    }
    return render(request, 'program_manager/reports.html', context)


@login_required
def committee_detail_report(request, committee_id):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    committee = get_object_or_404(Committee, id=committee_id, program=program)
    supervisor = committee.supervisor

    # Initialize default values
    total_tasks = 0
    completed_tasks = 0
    pending_tasks = 0
    overdue_tasks = 0
    avg_task_completion = 0
    tasks = None
    recent_tasks = []

    # Query the appropriate task model based on supervisor type
    if supervisor and supervisor.supervisor_type:
        if supervisor.supervisor_type == 'cultural':
            from cultural_committee_dashboard.models import CulturalTask
            tasks = CulturalTask.objects.filter(committee=committee)
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='completed').count()
            pending_tasks = tasks.filter(status='pending').count()
            overdue_tasks = 0  # Cultural tasks don't have overdue status
            recent_tasks = tasks.order_by('-created_at')[:10]

        elif supervisor.supervisor_type == 'sports':
            from sports_committee_dashboard.models import SportsTask
            tasks = SportsTask.objects.filter(committee=committee)
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='completed').count()
            pending_tasks = tasks.filter(status='pending').count()
            overdue_tasks = tasks.filter(status='overdue').count()
            recent_tasks = tasks.order_by('-created_at')[:10]

        elif supervisor.supervisor_type == 'sharia':
            from sharia_committee_dashboard.models import ShariaTask
            tasks = ShariaTask.objects.filter(committee=committee)
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='completed').count()
            pending_tasks = tasks.filter(status='pending').count()
            overdue_tasks = 0  # Sharia tasks don't have overdue status
            recent_tasks = tasks.order_by('-created_at')[:10]

        elif supervisor.supervisor_type == 'scientific':
            from scientific_committee_dashboard.models import ScientificTask
            tasks = ScientificTask.objects.filter(committee=committee)
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='completed').count()
            pending_tasks = tasks.filter(status='pending').count()
            overdue_tasks = 0  # Scientific tasks don't have overdue status
            recent_tasks = tasks.order_by('-created_at')[:10]

        elif supervisor.supervisor_type == 'operations':
            from operations_committee_dashboard.models import OperationsTask
            tasks = OperationsTask.objects.filter(committee=committee)
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='completed').count()
            pending_tasks = tasks.filter(status__in=['not_started', 'in_progress']).count()
            overdue_tasks = tasks.filter(status='overdue').count()
            recent_tasks = tasks.order_by('-created_at')[:10]
        else:
            # Fallback to generic Task model
            tasks = Task.objects.filter(committee=committee)
            total_tasks = tasks.count()
            completed_tasks = tasks.filter(status='completed').count()
            pending_tasks = tasks.filter(status='pending').count()
            overdue_tasks = tasks.filter(status='overdue').count()
            recent_tasks = tasks.order_by('-created_at')[:10]
    else:
        # No supervisor or supervisor type - use generic Task model
        tasks = Task.objects.filter(committee=committee)
        total_tasks = tasks.count()
        completed_tasks = tasks.filter(status='completed').count()
        pending_tasks = tasks.filter(status='pending').count()
        overdue_tasks = tasks.filter(status='overdue').count()
        recent_tasks = tasks.order_by('-created_at')[:10]

    # Calculate average task completion percentage
    if tasks and tasks.exists():
        total_completion = sum(task.completion_percentage for task in tasks)
        avg_task_completion = round(total_completion / tasks.count(), 1)
    else:
        avg_task_completion = 0

    committee_stats = {
        'total_students': Student.objects.filter(committee=committee).count(),
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'avg_student_progress': Student.objects.filter(committee=committee).aggregate(avg=Avg('progress'))['avg'] or 0,
        'avg_task_completion': avg_task_completion,
    }

    # Recent activities
    recent_activities = Activity.objects.filter(committee=committee).order_by('-date')[:10]

    # Students progress
    students = Student.objects.filter(committee=committee).select_related('user').order_by('-progress')

    # Task completion rate (percentage of completed tasks)
    if committee_stats['total_tasks'] > 0:
        task_completion_rate = round((committee_stats['completed_tasks'] / committee_stats['total_tasks']) * 100, 1)
    else:
        task_completion_rate = 0

    context = {
        'program': program,
        'committee': committee,
        'committee_stats': committee_stats,
        'recent_tasks': recent_tasks,
        'recent_activities': recent_activities,
        'students': students,
        'task_completion_rate': task_completion_rate,
    }
    return render(request, 'program_manager/committee_detail_report.html', context)


@login_required
def notifications(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Mark as read if requested
    if request.method == 'POST':
        notif_id = request.POST.get('notification_id')
        if notif_id:
            Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
            return redirect('pm_notifications')

    context = {
        'program': program,
        'notifications': notifications,
    }
    return render(request, 'program_manager/notifications.html', context)


@login_required
def mark_all_read(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'تم تحديد جميع الإشعارات كمقروءة!')

    return redirect('pm_notifications')


from accounts.models import ProgramSupervisor
from .forms import AddSupervisorForm
@login_required
def supervisor_management(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    # Get supervisors for this program
    supervisors = User.objects.filter(
        role='committee_supervisor',
        programsupervisor__program=program
    ).distinct()

    context = {
        'program': program,
        'supervisors': supervisors,
    }
    return render(request, 'program_manager/supervisor_management.html', context)

from django.db import IntegrityError
@login_required
def add_supervisor(request):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = AddSupervisorForm(request.POST)
        if form.is_valid():
            try:
                # Create the supervisor user
                supervisor = form.save()
                supervisor.set_password('123456')  # Default password
                supervisor.save()

                # Link supervisor to program
                ProgramSupervisor.objects.create(
                    program=program,
                    supervisor=supervisor,
                    created_by=request.user
                )

                UserActivity.objects.create(
                    user=request.user,
                    action=f'إضافة مشرف جديد: {supervisor.get_full_name()}',
                    ip_address=get_client_ip(request)
                )

                messages.success(request, 'تم إضافة المشرف بنجاح! كلمة المرور الافتراضية: 123456')
                return redirect('pm_supervisor_management')

            except IntegrityError:
                messages.error(request, 'اسم المستخدم موجود مسبقاً')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إضافة المشرف: {str(e)}')
    else:
        form = AddSupervisorForm()

    context = {
        'program': program,
        'form': form,
        'title': 'إضافة مشرف جديد'
    }
    return render(request, 'program_manager/supervisor_form.html', context)


@login_required
def delete_supervisor(request, supervisor_id):
    if request.user.role != 'program_manager':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        program = Program.objects.get(manager=request.user)
    except Program.DoesNotExist:
        messages.error(request, 'لم يتم تعيين برنامج لك بعد')
        return redirect('home')

    supervisor = get_object_or_404(User, id=supervisor_id, role='committee_supervisor')

    # Check if supervisor is linked to this program
    program_supervisor = get_object_or_404(ProgramSupervisor, program=program, supervisor=supervisor)

    if request.method == 'POST':
        supervisor_name = supervisor.get_full_name() or supervisor.username

        # Delete the supervisor user completely
        supervisor.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف المشرف: {supervisor_name}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف المشرف بنجاح!')
        return redirect('pm_supervisor_management')

    context = {
        'program': program,
        'object': supervisor,
        'type': 'مشرف'
    }
    return render(request, 'program_manager/confirm_delete.html', context)