from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from director_dashboard.models import Committee
from accounts.models import User, UserActivity
from .models import (OperationsTask, OperationsTeamMember, LogisticsResource,
                     OperationsFileLibrary, OperationsWeeklyReport, OperationsNotification)
from .forms import (OperationsTaskForm, OperationsTeamMemberForm, LogisticsResourceForm,
                    OperationsFileLibraryForm, OperationsWeeklyReportForm)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def operations_dashboard(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Update overdue tasks
    OperationsTask.objects.filter(
        committee=committee,
        due_date__lt=timezone.now().date(),
        status__in=['not_started', 'in_progress']
    ).update(status='overdue')

    # Statistics
    total_members = OperationsTeamMember.objects.filter(committee=committee, is_active=True).count()
    total_tasks = OperationsTask.objects.filter(committee=committee).count()
    completed_tasks = OperationsTask.objects.filter(committee=committee, status='completed').count()
    pending_tasks = OperationsTask.objects.filter(committee=committee,
                                                  status__in=['not_started', 'in_progress']).count()
    overdue_tasks = OperationsTask.objects.filter(committee=committee, status='overdue').count()

    # Completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Recent tasks
    recent_tasks = OperationsTask.objects.filter(committee=committee).order_by('-created_at')[:5]

    # Unread notifications
    unread_notifications = OperationsNotification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    # Task type distribution
    task_distribution = OperationsTask.objects.filter(committee=committee).values('task_type').annotate(
        count=Count('id')
    )

    # Logistics resources count
    total_resources = LogisticsResource.objects.filter(committee=committee).count()
    available_resources = LogisticsResource.objects.filter(committee=committee, status='available').count()

    context = {
        'committee': committee,
        'total_members': total_members,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'overdue_tasks': overdue_tasks,
        'completion_rate': round(completion_rate, 1),
        'recent_tasks': recent_tasks,
        'unread_notifications': unread_notifications,
        'task_distribution': task_distribution,
        'total_resources': total_resources,
        'available_resources': available_resources,
    }
    return render(request, 'operations_committee/dashboard.html', context)


@login_required
def committee_info(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = OperationsTeamMember.objects.filter(committee=committee)
    active_members = members.filter(is_active=True).count()
    avg_participation = members.aggregate(avg=Avg('participation_score'))['avg'] or 0

    # Latest update
    latest_task = OperationsTask.objects.filter(committee=committee).order_by('-updated_at').first()
    last_update = latest_task.updated_at if latest_task else committee.created_at

    context = {
        'committee': committee,
        'total_members': members.count(),
        'active_members': active_members,
        'avg_participation': round(avg_participation, 1),
        'last_update': last_update,
    }
    return render(request, 'operations_committee/committee_info.html', context)


@login_required
def task_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    tasks = OperationsTask.objects.filter(committee=committee).order_by('-created_at')

    # Filter by type
    task_type = request.GET.get('type')
    if task_type:
        tasks = tasks.filter(task_type=task_type)

    # Filter by status
    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)

    context = {
        'committee': committee,
        'tasks': tasks,
        'task_type_filter': task_type,
        'status_filter': status,
    }
    return render(request, 'operations_committee/task_management.html', context)


@login_required
def add_task(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = OperationsTaskForm(request.POST, committee=committee)
        if form.is_valid():
            task = form.save(commit=False)
            task.committee = committee
            task.created_by = request.user
            task.save()

            # Create notification
            members = OperationsTeamMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                OperationsNotification.objects.create(
                    user=member.user,  # Send to each member individually
                    committee=committee,
                    notification_type='task_added',
                    title='مهمة جديدة',
                    message=f'تم إضافة مهمة جديدة: {task.title}' + (
                        f' للمسؤول: {task.assigned_to_name}' if task.assigned_to_name else ''),
                    related_task=task
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة مهمة تشغيلية: {task.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة المهمة بنجاح!')
            return redirect('operations_task_management')
    else:
        form = OperationsTaskForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة مهمة جديدة'
    }
    return render(request, 'operations_committee/task_form.html', context)


@login_required
def edit_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(OperationsTask, id=task_id, committee=committee)

    if request.method == 'POST':
        form = OperationsTaskForm(request.POST, instance=task, committee=committee)
        if form.is_valid():
            task = form.save()

            members = OperationsTeamMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                OperationsNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='task_updated',
                    title='تعديل مهمة',
                    message=f'تم تعديل المهمة: {task.title}' + (
                        f' للمسؤول: {task.assigned_to_name}' if task.assigned_to_name else ''),
                    related_task=task
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل مهمة تشغيلية: {task.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل المهمة بنجاح!')
            return redirect('operations_task_management')
    else:
        form = OperationsTaskForm(instance=task, committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'task': task,
        'title': 'تعديل المهمة'
    }
    return render(request, 'operations_committee/task_form.html', context)


@login_required
def delete_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(OperationsTask, id=task_id, committee=committee)

    if request.method == 'POST':
        task_title = task.title
        task.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف مهمة تشغيلية: {task_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف المهمة بنجاح!')
        return redirect('operations_task_management')

    context = {
        'committee': committee,
        'object': task,
        'type': 'مهمة'
    }
    return render(request, 'operations_committee/confirm_delete.html', context)


@login_required
def member_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = OperationsTeamMember.objects.filter(committee=committee).select_related('user').order_by('-participation_score')

    context = {
        'committee': committee,
        'members': members,
    }
    return render(request, 'operations_committee/member_management.html', context)


@login_required
def add_member(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = OperationsTeamMemberForm(request.POST, committee=committee)
        if form.is_valid():
            member = form.save(commit=False)
            member.committee = committee
            member.save()

            messages.success(request, 'تم إضافة العضو بنجاح!')
            return redirect('operations_member_management')
    else:
        form = OperationsTeamMemberForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة عضو جديد'
    }
    return render(request, 'operations_committee/member_form.html', context)


@login_required
def logistics_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    resources = LogisticsResource.objects.filter(committee=committee).order_by('-created_at')

    # Filter by type
    resource_type = request.GET.get('type')
    if resource_type:
        resources = resources.filter(resource_type=resource_type)

    # Filter by status
    status = request.GET.get('status')
    if status:
        resources = resources.filter(status=status)

    context = {
        'committee': committee,
        'resources': resources,
        'resource_type_filter': resource_type,
        'status_filter': status,
    }
    return render(request, 'operations_committee/logistics_management.html', context)


@login_required
def add_resource(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = LogisticsResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.committee = committee
            resource.created_by = request.user
            resource.save()

            # Notify members
            members = OperationsTeamMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                OperationsNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='resource_added',
                    title='مورد جديد',
                    message=f'تم إضافة مورد جديد: {resource.name}',
                    related_resource=resource
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة مورد لوجستي: {resource.name}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة المورد بنجاح!')
            return redirect('operations_logistics_management')
    else:
        form = LogisticsResourceForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة مورد جديد'
    }
    return render(request, 'operations_committee/resource_form.html', context)


@login_required
def edit_resource(request, resource_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    resource = get_object_or_404(LogisticsResource, id=resource_id, committee=committee)

    if request.method == 'POST':
        form = LogisticsResourceForm(request.POST, instance=resource)
        if form.is_valid():
            resource = form.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل مورد لوجستي: {resource.name}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل المورد بنجاح!')
            return redirect('operations_logistics_management')
    else:
        form = LogisticsResourceForm(instance=resource)

    context = {
        'committee': committee,
        'form': form,
        'resource': resource,
        'title': 'تعديل المورد'
    }
    return render(request, 'operations_committee/resource_form.html', context)


@login_required
def delete_resource(request, resource_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    resource = get_object_or_404(LogisticsResource, id=resource_id, committee=committee)

    if request.method == 'POST':
        resource_name = resource.name
        resource.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف مورد لوجستي: {resource_name}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف المورد بنجاح!')
        return redirect('operations_logistics_management')

    context = {
        'committee': committee,
        'object': resource,
        'type': 'مورد'
    }
    return render(request, 'operations_committee/confirm_delete.html', context)


@login_required
def file_library(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    files = OperationsFileLibrary.objects.filter(committee=committee).order_by('-uploaded_at')

    # Filter by type
    file_type = request.GET.get('type')
    if file_type:
        files = files.filter(file_type=file_type)

    context = {
        'committee': committee,
        'files': files,
        'file_type_filter': file_type,
    }
    return render(request, 'operations_committee/file_library.html', context)


@login_required
def upload_file(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = OperationsFileLibraryForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.save(commit=False)
            file_obj.committee = committee
            file_obj.uploaded_by = request.user
            file_obj.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'رفع ملف تشغيلي: {file_obj.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم رفع الملف بنجاح!')
            return redirect('operations_file_library')
    else:
        form = OperationsFileLibraryForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'رفع ملف جديد'
    }
    return render(request, 'operations_committee/file_form.html', context)


@login_required
def delete_file(request, file_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    file_obj = get_object_or_404(OperationsFileLibrary, id=file_id, committee=committee)

    if request.method == 'POST':
        file_title = file_obj.title
        file_obj.file.delete()
        file_obj.delete()

        messages.success(request, 'تم حذف الملف بنجاح!')
        return redirect('operations_file_library')

    context = {
        'committee': committee,
        'object': file_obj,
        'type': 'ملف'
    }
    return render(request, 'operations_committee/confirm_delete.html', context)


@login_required
def reports(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Get all weekly reports
    weekly_reports = OperationsWeeklyReport.objects.filter(committee=committee).order_by('-week_start_date')

    # Task statistics
    total_tasks = OperationsTask.objects.filter(committee=committee).count()
    completed_tasks = OperationsTask.objects.filter(committee=committee, status='completed').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Task type statistics
    task_stats = OperationsTask.objects.filter(committee=committee).values('task_type').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    )

    context = {
        'committee': committee,
        'weekly_reports': weekly_reports,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': round(completion_rate, 1),
        'task_stats': task_stats,
    }
    return render(request, 'operations_committee/reports.html', context)


@login_required
def add_report(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = OperationsWeeklyReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.committee = committee
            report.created_by = request.user
            report.save()

            # Notify members
            members = OperationsTeamMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                OperationsNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='report_uploaded',
                    title='تقرير جديد',
                    message=f'تم رفع تقرير أسبوعي جديد: {report.week_start_date} - {report.week_end_date}'
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة تقرير أسبوعي: {report.week_start_date}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة التقرير بنجاح!')
            return redirect('operations_reports')
    else:
        form = OperationsWeeklyReportForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة تقرير أسبوعي'
    }
    return render(request, 'operations_committee/report_form.html', context)


@login_required
def notifications(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    notifications = OperationsNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Mark as read if requested
    if request.method == 'POST':
        notif_id = request.POST.get('notification_id')
        if notif_id:
            OperationsNotification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
            return redirect('operations_notifications')

    context = {
        'committee': committee,
        'notifications': notifications,
    }
    return render(request, 'operations_committee/notifications.html', context)


@login_required
def mark_all_read(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'operations':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        OperationsNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'تم تحديد جميع الإشعارات كمقروءة!')

    return redirect('operations_notifications')
