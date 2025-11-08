from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from director_dashboard.models import Committee
from accounts.models import User, UserActivity
from .models import (CulturalTask, CommitteeMember, FileLibrary,
                     Discussion, DiscussionComment, CulturalReport, CulturalNotification)
from .forms import (CulturalTaskForm, CommitteeMemberForm, FileLibraryForm,
                    DiscussionForm, DiscussionCommentForm, CulturalReportForm)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def add_report(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # Get user's committee
    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = CulturalReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.committee = committee
            report.created_by = request.user
            report.save()

            # Notify members
            members = CommitteeMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                CulturalNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='report_uploaded',
                    title='تقرير جديد',
                    message=f'تم رفع تقرير جديد: {report.title}',
                    related_report=report
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة تقرير ثقافي: {report.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة التقرير بنجاح!')
            return redirect('cultural_reports')
    else:
        form = CulturalReportForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة تقرير جديد'
    }
    return render(request, 'cultural_committee/report_form.html', context)


@login_required
def notifications(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    notifications = CulturalNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Mark as read if requested
    if request.method == 'POST':
        notif_id = request.POST.get('notification_id')
        if notif_id:
            CulturalNotification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
            return redirect('cultural_notifications')

    context = {
        'committee': committee,
        'notifications': notifications,
    }
    return render(request, 'cultural_committee/notifications.html', context)


@login_required
def mark_all_read(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        CulturalNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'تم تحديد جميع الإشعارات كمقروءة!')

    return redirect('cultural_notifications')
    messages.error(request, 'لم يتم تعيين لجنة لك بعد')
    return redirect('home')





@login_required
def upload_file(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = FileLibraryForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.save(commit=False)
            file_obj.committee = committee
            file_obj.uploaded_by = request.user
            file_obj.save()

            # Notify all committee members
            members = CommitteeMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                CulturalNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='file_uploaded',
                    title='ملف جديد',
                    message=f'تم رفع ملف جديد: {file_obj.title}',
                    related_file=file_obj
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'رفع ملف ثقافي: {file_obj.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم رفع الملف بنجاح!')
            return redirect('cultural_file_library')
    else:
        form = FileLibraryForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'رفع ملف جديد'
    }
    return render(request, 'cultural_committee/file_form.html', context)


@login_required
def delete_file(request, file_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    file_obj = get_object_or_404(FileLibrary, id=file_id, committee=committee)

    if request.method == 'POST':
        file_title = file_obj.title
        file_obj.file.delete()
        file_obj.delete()

        messages.success(request, 'تم حذف الملف بنجاح!')
        return redirect('cultural_file_library')

    context = {
        'committee': committee,
        'object': file_obj,
        'type': 'ملف'
    }
    return render(request, 'cultural_committee/confirm_delete.html', context)


@login_required
def discussions(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    discussions = Discussion.objects.filter(committee=committee).select_related('created_by')

    context = {
        'committee': committee,
        'discussions': discussions,
    }
    return render(request, 'cultural_committee/discussions.html', context)


from sports_committee_dashboard.models import SportsNotification
from director_dashboard.models import DirectorAlert
from operations_committee_dashboard.models import OperationsNotification
from pm_dashboard.models import Notification
from scientific_committee_dashboard.models import ScientificNotification
from sharia_committee_dashboard.models import ShariaNotification
@login_required
def add_discussion(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = DiscussionForm(request.POST)
        if form.is_valid():
            discussion = form.save(commit=False)
            discussion.committee = committee
            discussion.created_by = request.user
            discussion.save()

            # Notify members based on discussion type
            if discussion.is_public_to_all_supervisors:
                # Send to all supervisors, program managers, and director
                users_to_notify = User.objects.filter(
                    Q(role='committee_supervisor') |
                    Q(role='program_manager') |
                    Q(role='director')
                ).exclude(id=request.user.id)  # Exclude the creator
            else:
                # Send only to committee members (original behavior)
                users_to_notify = User.objects.filter(
                    id__in=CommitteeMember.objects.filter(
                        committee=committee, is_active=True
                    ).values_list('user', flat=True)
                )

            for user in users_to_notify:
                CulturalNotification.objects.create(
                    user=user,
                    committee=committee,
                    notification_type='discussion_created',
                    title='نقاش جديد',
                    message=f'نقاش جديد: {discussion.title}',
                    related_discussion=discussion
                )

                # Sports Notification (for sports committee)
                SportsNotification.objects.create(
                    user=user,
                    committee=committee,
                    notification_type='discussion_created',
                    title='نقاش جديد',
                    message=f'تم إنشاء نقاش جديد: {discussion.title}',
                    related_discussion=discussion
                )

                # Scientific Notification (for scientific committee)
                ScientificNotification.objects.create(
                    user=user,
                    committee=committee,
                    notification_type='discussion_created',
                    title='نقاش جديد',
                    message=f'تم إنشاء نقاش جديد: {discussion.title}',
                    related_discussion=discussion
                )

                # Sharia Notification (for sharia committee)
                ShariaNotification.objects.create(
                    user=user,
                    committee=committee,
                    notification_type='discussion_created',
                    title='نقاش جديد',
                    message=f'تم إنشاء نقاش جديد: {discussion.title}',
                    related_discussion=discussion
                )

                Notification.objects.create(
                    user=user,
                    related_committee=committee,
                    notification_type='discussion_created',
                    title='نقاش جديد',
                    message=f'تم إنشاء نقاش جديد: {discussion.title}',
                    related_discussion=discussion
                )

                # Director Alert (for director dashboard)
                DirectorAlert.objects.create(
                    title='نقاش جديد',
                    message=f'تم إنشاء نقاش جديد في اللجنة الثقافية: {discussion.title}',
                    alert_type='system_alert',
                    priority='medium',
                    related_user=request.user,
                    related_committee=committee,
                    related_discussion=discussion,
                    action_url=f'/cultural/discussions/{discussion.id}/'
                )

                # Operations Notification (for operations committee)
                OperationsNotification.objects.create(
                    user=user,
                    committee=committee,
                    notification_type='discussion_created',
                    title='نقاش جديد',
                    message=f'تم إنشاء نقاش جديد: {discussion.title}',
                    related_discussion=discussion
                )

            messages.success(request, 'تم إضافة النقاش بنجاح!')
            return redirect('cultural_discussion_detail', discussion_id=discussion.id)
    else:
        form = DiscussionForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة نقاش جديد'
    }
    return render(request, 'cultural_committee/discussion_form.html', context)


@login_required
def discussion_detail(request, discussion_id):
    # Allow access for cultural committee supervisor, all supervisors, program managers, and director
    if not (request.user.role in ['committee_supervisor', 'program_manager', 'director']):
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        # For program managers and director who don't have a committee, get the discussion's committee
        discussion = get_object_or_404(Discussion, id=discussion_id)
        committee = discussion.committee

    discussion = get_object_or_404(Discussion, id=discussion_id)

    # Check if user has permission to view this discussion
    if discussion.is_public_to_all_supervisors:
        # Allow all supervisors, program managers, and director
        if not (request.user.role in ['committee_supervisor', 'program_manager', 'director']):
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')
    else:
        # Original permission check - only cultural committee supervisor
        if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')
        # Also check if the discussion belongs to the user's committee
        if discussion.committee.supervisor != request.user:
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')

    comments = discussion.comments.select_related('created_by').order_by('created_at')

    if request.method == 'POST':
        form = DiscussionCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.discussion = discussion
            comment.created_by = request.user
            comment.save()

            messages.success(request, 'تم إضافة التعليق بنجاح!')
            return redirect('cultural_discussion_detail', discussion_id=discussion.id)
    else:
        form = DiscussionCommentForm()

    context = {
        'committee': committee,
        'discussion': discussion,
        'comments': comments,
        'form': form,
    }
    return render(request, 'cultural_committee/discussion_detail.html', context)


@login_required
def reports(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Task completion stats
    total_tasks = CulturalTask.objects.filter(committee=committee).count()
    completed_tasks = CulturalTask.objects.filter(committee=committee, status='completed').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Task type statistics
    task_stats = CulturalTask.objects.filter(committee=committee).values('task_type').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    )

    # Top participating members
    top_members = CommitteeMember.objects.filter(
        committee=committee,
        is_active=True
    ).order_by('-participation_score')[:10]

    # Recent reports
    recent_reports = CulturalReport.objects.filter(committee=committee).order_by('-created_at')[:5]

    context = {
        'committee': committee,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': round(completion_rate, 1),
        'task_stats': task_stats,
        'top_members': top_members,
        'recent_reports': recent_reports,
    }
    return render(request, 'cultural_committee/reports.html', context)


@login_required
def cultural_dashboard(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Statistics
    total_members = CommitteeMember.objects.filter(committee=committee, is_active=True).count()
    total_tasks = CulturalTask.objects.filter(committee=committee).count()
    completed_tasks = CulturalTask.objects.filter(committee=committee, status='completed').count()
    pending_tasks = CulturalTask.objects.filter(committee=committee, status='pending').count()

    # Completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Recent tasks
    recent_tasks = CulturalTask.objects.filter(committee=committee).order_by('-created_at')[:5]

    # Unread notifications
    unread_notifications = CulturalNotification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    # Top participating members
    top_members = CommitteeMember.objects.filter(
        committee=committee,
        is_active=True
    ).order_by('-participation_score')[:5]

    # Task type distribution
    task_distribution = CulturalTask.objects.filter(committee=committee).values('task_type').annotate(
        count=Count('id')
    )

    context = {
        'committee': committee,
        'total_members': total_members,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'completion_rate': round(completion_rate, 1),
        'recent_tasks': recent_tasks,
        'unread_notifications': unread_notifications,
        'top_members': top_members,
        'task_distribution': task_distribution,
    }
    return render(request, 'cultural_committee/dashboard.html', context)


@login_required
def committee_info(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = CommitteeMember.objects.filter(committee=committee)
    active_members = members.filter(is_active=True).count()
    avg_participation = members.aggregate(avg=Avg('participation_score'))['avg'] or 0

    context = {
        'committee': committee,
        'total_members': members.count(),
        'active_members': active_members,
        'avg_participation': round(avg_participation, 1),
    }
    return render(request, 'cultural_committee/committee_info.html', context)


@login_required
def task_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    tasks = CulturalTask.objects.filter(committee=committee).order_by('-created_at')

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
    return render(request, 'cultural_committee/task_management.html', context)


@login_required
def add_task(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = CulturalTaskForm(request.POST, committee=committee)
        if form.is_valid():
            task = form.save(commit=False)
            task.committee = committee
            task.created_by = request.user
            task.save()

            # Create notification
            members = CommitteeMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                CulturalNotification.objects.create(
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
                action=f'إضافة مهمة ثقافية: {task.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة المهمة بنجاح!')
            return redirect('cultural_task_management')
    else:
        form = CulturalTaskForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة مهمة جديدة'
    }
    return render(request, 'cultural_committee/task_form.html', context)


@login_required
def edit_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(CulturalTask, id=task_id, committee=committee)

    if request.method == 'POST':
        form = CulturalTaskForm(request.POST, instance=task, committee=committee)
        if form.is_valid():
            task = form.save()

            # Create notification
            members = CommitteeMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                CulturalNotification.objects.create(
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
                action=f'تعديل مهمة ثقافية: {task.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل المهمة بنجاح!')
            return redirect('cultural_task_management')
    else:
        form = CulturalTaskForm(instance=task, committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'task': task,
        'title': 'تعديل المهمة'
    }
    return render(request, 'cultural_committee/task_form.html', context)


@login_required
def delete_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(CulturalTask, id=task_id, committee=committee)

    if request.method == 'POST':
        task_title = task.title
        task.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف مهمة ثقافية: {task_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف المهمة بنجاح!')
        return redirect('cultural_task_management')

    context = {
        'committee': committee,
        'object': task,
        'type': 'مهمة'
    }
    return render(request, 'cultural_committee/confirm_delete.html', context)


@login_required
def member_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = CommitteeMember.objects.filter(committee=committee).select_related('user').order_by(
        '-participation_score')

    context = {
        'committee': committee,
        'members': members,
    }
    return render(request, 'cultural_committee/member_management.html', context)


@login_required
def add_member(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = CommitteeMemberForm(request.POST, committee=committee)
        if form.is_valid():
            member = form.save(commit=False)
            member.committee = committee
            member.save()

            messages.success(request, 'تم إضافة العضو بنجاح!')
            return redirect('cultural_member_management')
    else:
        form = CommitteeMemberForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة عضو جديد'
    }
    return render(request, 'cultural_committee/member_form.html', context)


@login_required
def file_library(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
        files = FileLibrary.objects.filter(committee=committee).order_by('-uploaded_at')

        # Filter by type
        file_type = request.GET.get('type')
        if file_type:
            files = files.filter(file_type=file_type)

        context = {
            'committee': committee,
            'files': files,
            'file_type_filter': file_type,
        }
        return render(request, 'cultural_committee/file_library.html', context)

    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم العثور على لجنة مرتبطة بحسابك')
        return redirect('home')  # or wherever appropriate