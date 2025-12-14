from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from director_dashboard.models import Committee
from accounts.models import User, UserActivity
from .models import (CulturalTask, CommitteeMember, FileLibrary,
                     Discussion, DiscussionComment, CulturalReport, CulturalNotification,DailyPhrase)
from .forms import (CulturalTaskForm, CommitteeMemberForm, FileLibraryForm,
                    DiscussionForm, DiscussionCommentForm, CulturalReportForm,DailyPhraseForm)


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

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        CulturalNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'تم تحديد جميع الإشعارات كمقروءة!')

    return redirect('cultural_notifications')





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
    print("=== CULTURAL DASHBOARD ACCESSED ===")
    print(f"User: {request.user}")
    print(f"User role: {getattr(request.user, 'role', 'No role')}")
    print(f"Supervisor type: {getattr(request.user, 'supervisor_type', 'No supervisor_type')}")

    if request.user.role != 'committee_supervisor' or getattr(request.user, 'supervisor_type', None) != 'cultural':
        print("Permission denied - not cultural supervisor")
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        print("Attempting to get committee...")
        committee = Committee.objects.get(supervisor=request.user)
        print(f"Committee found: {committee.name}")
    except Committee.DoesNotExist:
        print("Committee.DoesNotExist exception raised")
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')
    except Exception as e:
        print(f"Unexpected error getting committee: {e}")
        messages.error(request, f'حدث خطأ: {e}')
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

    # Daily phrase for today
    from django.utils import timezone
    try:
        daily_phrase = DailyPhrase.get_today_phrase()
    except Exception as e:
        daily_phrase = None

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
        'daily_phrase': daily_phrase,
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
    """View for displaying all tasks with filtering"""

    committee = get_object_or_404(Committee, supervisor=request.user)

    # Get filter parameter
    status_filter = request.GET.get('status')

    # Query tasks
    tasks = CulturalTask.objects.filter(committee=committee)

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    context = {
        'committee': committee,
        'tasks': tasks,
        'status_filter': status_filter,
    }

    return render(request, 'cultural_committee/task_management.html', context)


@login_required
def view_task_sessions(request, task_id):
    """View for displaying all sessions of a specific task"""

    task = get_object_or_404(CulturalTask, id=task_id)

    # Ensure user has permission to view this task
    if task.committee.supervisor != request.user:
        messages.error(request, 'ليس لديك صلاحية لعرض هذه المهمة.')
        return redirect('cultural_task_management')

    sessions = task.sessions.all()

    context = {
        'task': task,
        'sessions': sessions,
        'committee': task.committee,
    }

    return render(request, 'cultural_committee/task_sessions.html', context)


from .models import TaskSession
from .forms import TaskSessionForm
from django.http import JsonResponse
import json
@login_required
def toggle_session_completion(request, session_id):
    """AJAX view to toggle session completion status"""

    if request.method == 'POST':
        session = get_object_or_404(TaskSession, id=session_id)

        # Ensure user has permission
        if session.task.committee.supervisor != request.user:
            return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

        session.is_completed = not session.is_completed
        session.save()

        return JsonResponse({
            'success': True,
            'is_completed': session.is_completed,
            'session_id': session.id
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

from datetime import datetime
from django.db import transaction

@login_required
def add_task(request):
    committee = get_object_or_404(Committee, supervisor=request.user)

    if request.method == 'POST':
        form = CulturalTaskForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():

                    task = form.save(commit=False)
                    task.committee = committee
                    task.created_by = request.user

                    sessions_data = request.POST.get('sessions_data')

                    if sessions_data:
                        sessions = json.loads(sessions_data)
                    else:
                        sessions = []

                    task.has_sessions = len(sessions) > 0
                    task.save()

                    if sessions:
                        for session_data in sessions:
                            TaskSession.objects.create(
                                task=task,
                                name=session_data.get('name', ''),
                                date=datetime.strptime(session_data['date'], '%Y-%m-%d').date(),
                                time=datetime.strptime(session_data['time'], '%H:%M').time(),
                                session_order=session_data.get('id', 1)
                            )

                messages.success(request, 'تم إضافة المهمة بنجاح 🎉')
                return redirect('cultural_task_management')

            except json.JSONDecodeError:
                messages.error(request, 'بيانات الجلسات غير صحيحة.')
            except Exception as e:
                messages.error(request, 'حدث خطأ غير متوقع.')

        else:
            messages.error(request, 'الرجاء تصحيح أخطاء النموذج.')

    else:
        form = CulturalTaskForm()

    return render(request, 'cultural_committee/task_form.html', {
        'form': form,
        'committee': committee,
        'title': 'إضافة مهمة جديدة'
    })



@login_required
def edit_task(request, task_id):
    """View for editing an existing cultural task and its sessions"""

    task = get_object_or_404(CulturalTask, id=task_id)

    # Ensure user has permission to edit this task
    if task.committee.supervisor != request.user:
        messages.error(request, 'ليس لديك صلاحية لتعديل هذه المهمة.')
        return redirect('cultural_task_management')

    if request.method == 'POST':
        form = CulturalTaskForm(request.POST, instance=task)

        if form.is_valid():
            task = form.save(commit=False)

            # Handle sessions data
            sessions_data = request.POST.get('sessions_data', '[]')

            try:
                sessions = json.loads(sessions_data)
                task.has_sessions = len(sessions) > 0

                # Convert recurrence_days to JSON if custom pattern
                if task.is_recurring and task.recurrence_pattern == 'custom' and task.recurrence_days:
                    if isinstance(task.recurrence_days, list):
                        pass
                    else:
                        task.recurrence_days = list(task.recurrence_days)

                task.save()

                # Delete existing sessions and create new ones
                task.sessions.all().delete()

                if sessions:
                    for session_data in sessions:
                        TaskSession.objects.create(
                            task=task,
                            name=session_data.get('name', ''),
                            date=datetime.strptime(session_data.get('date'), '%Y-%m-%d').date(),
                            time=datetime.strptime(session_data.get('time'), '%H:%M').time(),
                            session_order=session_data.get('id', 1)
                        )

                # Create notification for task update
                members = CommitteeMember.objects.filter(committee=task.committee, is_active=True)
                for member in members:
                    CulturalNotification.objects.create(
                        user=member.user,
                        committee=task.committee,
                        notification_type='task_updated',
                        title='تم تعديل المهمة',
                        message=f'تم تعديل المهمة: {task.title}',
                        related_task=task
                    )

                UserActivity.objects.create(
                    user=request.user,
                    action=f'تعديل مهمة ثقافية: {task.title}',
                    ip_address=get_client_ip(request)
                )

                if task.is_recurring:
                    recurrence_info = f' ({task.get_recurrence_pattern_display()})'
                    if sessions:
                        messages.success(
                            request,
                            f'تم تحديث المهمة المتكررة "{task.title}" بنجاح مع {len(sessions)} جلسة/جلسات!{recurrence_info}'
                        )
                    else:
                        messages.success(request, f'تم تحديث المهمة المتكررة "{task.title}" بنجاح!{recurrence_info}')
                else:
                    if sessions:
                        messages.success(
                            request,
                            f'تم تحديث المهمة "{task.title}" بنجاح مع {len(sessions)} جلسة/جلسات!'
                        )
                    else:
                        messages.success(request, f'تم تحديث المهمة "{task.title}" بنجاح!')

                return redirect('cultural_task_management')

            except (ValueError, json.JSONDecodeError) as e:
                messages.error(request, 'حدث خطأ في معالجة بيانات الجلسات.')
        else:
            messages.error(request, 'الرجاء تصحيح الأخطاء في النموذج.')
    else:
        # Prepare initial data for recurrence_days
        initial_data = {}
        if task.recurrence_days and isinstance(task.recurrence_days, list):
            initial_data['recurrence_days'] = [str(day) for day in task.recurrence_days]

        form = CulturalTaskForm(instance=task, initial=initial_data)

    # Get existing sessions for pre-population
    existing_sessions = []
    for idx, session in enumerate(task.sessions.all(), 1):
        existing_sessions.append({
            'id': idx,
            'name': session.name,
            'date': session.date.strftime('%Y-%m-%d'),
            'time': session.time.strftime('%H:%M'),
        })

    context = {
        'form': form,
        'title': 'تعديل المهمة',
        'committee': task.committee,
        'task': task,
        'existing_sessions': json.dumps(existing_sessions),
        'has_sessions': task.has_sessions,
    }

    return render(request, 'cultural_committee/task_form.html', context)


@login_required
def delete_task(request, task_id):
    """View for deleting a cultural task"""

    task = get_object_or_404(CulturalTask, id=task_id)

    # Ensure user has permission to delete this task
    if task.committee.supervisor != request.user:
        messages.error(request, 'ليس لديك صلاحية لحذف هذه المهمة.')
        return redirect('cultural_task_management')

    if request.method == 'POST':
        task_title = task.title
        is_recurring = task.is_recurring
        recurrence_pattern = task.get_recurrence_pattern_display() if task.is_recurring else None

        # Create notification before deletion
        members = CommitteeMember.objects.filter(committee=task.committee, is_active=True)
        for member in members:
            CulturalNotification.objects.create(
                user=member.user,
                committee=task.committee,
                notification_type='task_updated',
                title='تم حذف المهمة',
                message=f'تم حذف المهمة: {task_title}'
            )

        task.delete()  # This will also cascade delete all associated sessions

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف مهمة ثقافية: {task_title}' + (f' ({recurrence_pattern})' if is_recurring else ''),
            ip_address=get_client_ip(request)
        )

        if is_recurring:
            messages.success(request, f'تم حذف المهمة المتكررة بنجاح! ({recurrence_pattern})')
        else:
            messages.success(request, f'تم حذف المهمة "{task_title}" بنجاح!')

        return redirect('cultural_task_management')

    context = {
        'task': task,
        'committee': task.committee,
    }

    return render(request, 'cultural_committee/delete_task_confirm.html', context)

from django.db import models

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

    active_members_count = CommitteeMember.objects.filter(committee=committee,is_active='True').count()

    # حساب متوسط درجة المشاركة
    avg_participation_score = members.aggregate(
        avg_score=models.Avg('participation_score')
    )['avg_score'] or 0

    # تقريب المتوسط إلى منزلتين عشريتين
    avg_participation_score = round(avg_participation_score, 2)

    # الحصول على أعلى درجة مشاركة
    top_member = members.first()
    top_member_score = top_member.participation_score if top_member else 0

    context = {
        'committee': committee,
        'members': members,
        'active_members_count':active_members_count,
        'avg_participation_score': avg_participation_score,
        'top_member_score': top_member_score,
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


from .models import DailyPhrase
from .forms import DailyPhraseForm


@login_required
def daily_phrases(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Get all phrases for this committee
    phrases = DailyPhrase.objects.filter(committee=committee).order_by('day_of_week')

    # Get phrases by day for display
    days_dict = {}
    for day_code, day_name in DailyPhrase.DAY_CHOICES:
        day_phrase = phrases.filter(day_of_week=day_code).first()
        days_dict[day_code] = {
            'name': day_name,
            'phrase': day_phrase,
            'code': day_code
        }

    # Filter by active status
    is_active = request.GET.get('is_active')
    if is_active == 'true':
        phrases = phrases.filter(is_active=True)
    elif is_active == 'false':
        phrases = phrases.filter(is_active=False)

    context = {
        'committee': committee,
        'phrases': phrases,
        'days_dict': days_dict,
        'day_choices': DailyPhrase.DAY_CHOICES,
        'is_active_filter': is_active,
    }
    return render(request, 'cultural_committee/daily_phrases.html', context)


@login_required
def add_daily_phrase(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Check which days are already taken
    taken_days = DailyPhrase.objects.filter(
        committee=committee
    ).values_list('day_of_week', flat=True)

    available_days = [
        (code, name) for code, name in DailyPhrase.DAY_CHOICES
        if code not in taken_days
    ]

    if not available_days:
        messages.error(request, 'جميع أيام الأسبوع تحتوي بالفعل على عبارات')
        return redirect('cultural_daily_phrases')

    if request.method == 'POST':
        form = DailyPhraseForm(request.POST, committee=committee)
        if form.is_valid():
            phrase = form.save(commit=False)
            phrase.committee = committee
            phrase.created_by = request.user
            phrase.save()

            # Notify members
            members = CommitteeMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                CulturalNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='daily_phrase_added',
                    title='عبارة جديدة',
                    message=f'تم إضافة عبارة ليوم {phrase.get_day_of_week_display()}',
                    related_daily_phrase=phrase
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة عبارة ليوم {phrase.get_day_of_week_display()}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة العبارة بنجاح!')
            return redirect('cultural_daily_phrases')
    else:
        # Initialize form with available days only
        initial_form = DailyPhraseForm(committee=committee)
        # Update choices dynamically
        initial_form.fields['day_of_week'].choices = available_days

    context = {
        'committee': committee,
        'form': initial_form,
        'title': 'إضافة عبارة جديدة',
        'available_days': available_days,
        'taken_days': taken_days,
    }
    return render(request, 'cultural_committee/daily_phrase_form.html', context)


@login_required
def edit_daily_phrase(request, phrase_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    phrase = get_object_or_404(DailyPhrase, id=phrase_id, committee=committee)

    if request.method == 'POST':
        form = DailyPhraseForm(request.POST, instance=phrase, committee=committee)
        if form.is_valid():
            form.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل عبارة ليوم {phrase.get_day_of_week_display()}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل العبارة بنجاح!')
            return redirect('cultural_daily_phrases')
    else:
        form = DailyPhraseForm(instance=phrase, committee=committee)
        # If phrase is for a specific day, show all choices except those taken by others
        if phrase.day_of_week != 'all':
            taken_days = DailyPhrase.objects.filter(
                committee=committee
            ).exclude(id=phrase.id).values_list('day_of_week', flat=True)

            available_days = [
                (code, name) for code, name in DailyPhrase.DAY_CHOICES
                if code not in taken_days or code == phrase.day_of_week
            ]
            form.fields['day_of_week'].choices = available_days

    context = {
        'committee': committee,
        'form': form,
        'phrase': phrase,
        'title': f'تعديل عبارة {phrase.get_day_of_week_display()}'
    }
    return render(request, 'cultural_committee/daily_phrase_form.html', context)


@login_required
def delete_daily_phrase(request, phrase_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    phrase = get_object_or_404(DailyPhrase, id=phrase_id, committee=committee)

    if request.method == 'POST':
        phrase.delete()

        UserActivity.objects.create(
            user=request.user,
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف عبارة اليوم بنجاح!')
        return redirect('cultural_daily_phrases')

    context = {
        'committee': committee,
        'object': phrase,
        'type': 'عبارة اليوم'
    }
    return render(request, 'cultural_committee/confirm_delete.html', context)


@login_required
def toggle_daily_phrase(request, phrase_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'cultural':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    phrase = get_object_or_404(DailyPhrase, id=phrase_id, committee=committee)
    phrase.is_active = not phrase.is_active
    phrase.save()

    action = "تفعيل" if phrase.is_active else "تعطيل"
    messages.success(request, f'تم {action} عبارة اليوم بنجاح!')

    return redirect('cultural_daily_phrases')