from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from director_dashboard.models import Committee
from accounts.models import User, UserActivity
from .models import (SportsTask, SportsMember, SportsFile, Match, SportsReport, SportsNotification)
from .forms import (SportsTaskForm, SportsMemberForm, SportsFileForm, MatchForm, SportsReportForm)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

from cultural_committee_dashboard.models import DailyPhrase
@login_required
def sports_dashboard(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Statistics
    total_members = SportsMember.objects.filter(committee=committee, is_active=True).count()
    total_tasks = SportsTask.objects.filter(committee=committee).count()
    completed_tasks = SportsTask.objects.filter(committee=committee, status='completed').count()
    pending_tasks = SportsTask.objects.filter(committee=committee, status='pending').count()

    # Matches statistics
    upcoming_matches = Match.objects.filter(
        committee=committee,
        status='scheduled',
        date__gte=timezone.now().date()
    ).count()

    # Completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Recent tasks
    recent_tasks = SportsTask.objects.filter(committee=committee).order_by('-created_at')[:5]

    # Upcoming matches
    next_matches = Match.objects.filter(
        committee=committee,
        status='scheduled',
        date__gte=timezone.now().date()
    ).order_by('date', 'time')[:5]

    # Unread notifications
    unread_notifications = SportsNotification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    # Get daily phrase from cultural committee in the same program
    try:
        cultural_committee = Committee.objects.filter(
            program=committee.program,
        ).first()

        if cultural_committee:
            daily_phrase = DailyPhrase.get_today_phrase()
        else:
            daily_phrase = None
    except:
        daily_phrase = None

    context = {
        'committee': committee,
        'total_members': total_members,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'upcoming_matches': upcoming_matches,
        'completion_rate': round(completion_rate, 1),
        'recent_tasks': recent_tasks,
        'next_matches': next_matches,
        'unread_notifications': unread_notifications,
        'daily_phrase': daily_phrase,
    }
    return render(request, 'sports_committee/dashboard.html', context)


@login_required
def committee_info(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = SportsMember.objects.filter(committee=committee)
    active_members = members.filter(is_active=True).count()
    avg_participation = members.aggregate(avg=Avg('participation_score'))['avg'] or 0

    # Role distribution
    role_distribution = members.values('role').annotate(count=Count('id'))

    context = {
        'committee': committee,
        'total_members': members.count(),
        'active_members': active_members,
        'avg_participation': round(avg_participation, 1),
        'role_distribution': role_distribution,
    }
    return render(request, 'sports_committee/committee_info.html', context)


@login_required
def task_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    tasks = SportsTask.objects.filter(committee=committee).order_by('-created_at')

    # Filters
    task_type = request.GET.get('type')
    if task_type:
        tasks = tasks.filter(task_type=task_type)

    status = request.GET.get('status')
    if status:
        tasks = tasks.filter(status=status)

    context = {
        'committee': committee,
        'tasks': tasks,
        'task_type_filter': task_type,
        'status_filter': status,
    }
    return render(request, 'sports_committee/task_management.html', context)


@login_required
def add_task(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = SportsTaskForm(request.POST, committee=committee)
        if form.is_valid():
            task = form.save(commit=False)
            task.committee = committee
            task.created_by = request.user

            # Set start_date if not provided
            if not task.start_date:
                task.start_date = task.due_date

            # Convert recurrence_days to JSON format if it's a list
            if task.is_recurring and task.recurrence_pattern == 'custom' and task.recurrence_days:
                if isinstance(task.recurrence_days, list):
                    # Already a list, good to go
                    pass
                else:
                    # Convert to list if needed
                    task.recurrence_days = list(task.recurrence_days)

            task.save()

            # Create notifications for committee members
            members = SportsMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                SportsNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='task_added',
                    title='مهمة جديدة',
                    message=f'تم إضافة مهمة جديدة: {task.title}' + (
                        f' ({task.get_recurrence_pattern_display()})' if task.is_recurring else '') +
                            (f' للمسؤول: {task.assigned_to_name}' if task.assigned_to_name else ''),
                    related_task=task
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة مهمة رياضية: {task.title}' +
                       (f' ({task.get_recurrence_pattern_display()})' if task.is_recurring else ''),
                ip_address=get_client_ip(request)
            )

            if task.is_recurring:
                messages.success(request,
                                 f'تم إضافة المهمة المتكررة بنجاح! ({task.get_recurrence_pattern_display()})')
            else:
                messages.success(request, 'تم إضافة المهمة بنجاح!')

            return redirect('sports_task_management')
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)
            messages.error(request, 'حدث خطأ في حفظ النموذج. يرجى مراجعة البيانات.')
    else:
        form = SportsTaskForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة مهمة جديدة'
    }
    return render(request, 'sports_committee/task_form.html', context)


@login_required
def edit_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(SportsTask, id=task_id, committee=committee)

    if request.method == 'POST':
        form = SportsTaskForm(request.POST, instance=task, committee=committee)
        if form.is_valid():
            task = form.save(commit=False)

            # Set start_date if not provided
            if not task.start_date:
                task.start_date = task.due_date

            # Convert recurrence_days to JSON format if it's a list
            if task.is_recurring and task.recurrence_pattern == 'custom' and task.recurrence_days:
                if isinstance(task.recurrence_days, list):
                    pass
                else:
                    task.recurrence_days = list(task.recurrence_days)

            task.save()

            # Create notifications for committee members
            members = SportsMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                SportsNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='task_updated',
                    title='تعديل مهمة',
                    message=f'تم تعديل المهمة: {task.title}' + (
                        f' ({task.get_recurrence_pattern_display()})' if task.is_recurring else '') +
                            (f' للمسؤول: {task.assigned_to_name}' if task.assigned_to_name else ''),
                    related_task=task
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل مهمة رياضية: {task.title}' +
                       (f' ({task.get_recurrence_pattern_display()})' if task.is_recurring else ''),
                ip_address=get_client_ip(request)
            )

            if task.is_recurring:
                messages.success(request,
                                 f'تم تعديل المهمة المتكررة بنجاح! ({task.get_recurrence_pattern_display()})')
            else:
                messages.success(request, 'تم تعديل المهمة بنجاح!')

            return redirect('sports_task_management')
        else:
            print("Form errors:", form.errors)
            messages.error(request, 'حدث خطأ في حفظ النموذج. يرجى مراجعة البيانات.')
    else:
        # Pre-populate form with existing data
        initial_data = {}
        if task.recurrence_days and isinstance(task.recurrence_days, list):
            initial_data['recurrence_days'] = [str(day) for day in task.recurrence_days]

        form = SportsTaskForm(instance=task, committee=committee, initial=initial_data)

    context = {
        'committee': committee,
        'form': form,
        'task': task,
        'title': 'تعديل المهمة'
    }
    return render(request, 'sports_committee/task_form.html', context)


@login_required
def delete_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(SportsTask, id=task_id, committee=committee)

    if request.method == 'POST':
        task_title = task.title
        is_recurring = task.is_recurring
        recurrence_pattern = task.get_recurrence_pattern_display() if task.is_recurring else None

        task.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف مهمة رياضية: {task_title}' +
                   (f' ({recurrence_pattern})' if is_recurring else ''),
            ip_address=get_client_ip(request)
        )

        if is_recurring:
            messages.success(request,
                             f'تم حذف المهمة المتكررة بنجاح! ({recurrence_pattern})')
        else:
            messages.success(request, 'تم حذف المهمة بنجاح!')

        return redirect('sports_task_management')

    context = {
        'committee': committee,
        'object': task,
        'type': 'مهمة' + (' متكررة' if task.is_recurring else ''),
        'extra_info': f'نمط التكرار: {task.get_recurrence_pattern_display()}' if task.is_recurring else None
    }
    return render(request, 'sports_committee/confirm_delete.html', context)


@login_required
def member_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = SportsMember.objects.filter(committee=committee).select_related('user').order_by('-participation_score')

    context = {
        'committee': committee,
        'members': members,
    }
    return render(request, 'sports_committee/member_management.html', context)


@login_required
def add_member(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = SportsMemberForm(request.POST, committee=committee)
        if form.is_valid():
            member = form.save(commit=False)
            member.committee = committee
            member.save()

            messages.success(request, 'تم إضافة العضو بنجاح!')
            return redirect('sports_member_management')
    else:
        form = SportsMemberForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة عضو جديد'
    }
    return render(request, 'sports_committee/member_form.html', context)


@login_required
def file_library(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    files = SportsFile.objects.filter(committee=committee).order_by('-uploaded_at')

    # Filter by type
    file_type = request.GET.get('type')
    if file_type:
        files = files.filter(file_type=file_type)

    context = {
        'committee': committee,
        'files': files,
        'file_type_filter': file_type,
    }
    return render(request, 'sports_committee/file_library.html', context)


@login_required
def upload_file(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = SportsFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.save(commit=False)
            file_obj.committee = committee
            file_obj.uploaded_by = request.user
            file_obj.save()

            # Notify all committee members
            members = SportsMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                SportsNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='results_uploaded',
                    title='ملف جديد',
                    message=f'تم رفع ملف جديد: {file_obj.title}'
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'رفع ملف رياضي: {file_obj.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم رفع الملف بنجاح!')
            return redirect('sports_file_library')
    else:
        form = SportsFileForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'رفع ملف جديد'
    }
    return render(request, 'sports_committee/file_form.html', context)


@login_required
def delete_file(request, file_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    file_obj = get_object_or_404(SportsFile, id=file_id, committee=committee)

    if request.method == 'POST':
        file_title = file_obj.title
        file_obj.file.delete()
        file_obj.delete()

        messages.success(request, 'تم حذف الملف بنجاح!')
        return redirect('sports_file_library')

    context = {
        'committee': committee,
        'object': file_obj,
        'type': 'ملف'
    }
    return render(request, 'sports_committee/confirm_delete.html', context)


@login_required
def match_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    matches = Match.objects.filter(committee=committee).order_by('-date', '-time')

    # Filters
    match_type = request.GET.get('type')
    if match_type:
        matches = matches.filter(match_type=match_type)

    status = request.GET.get('status')
    if status:
        matches = matches.filter(status=status)

    context = {
        'committee': committee,
        'matches': matches,
        'match_type_filter': match_type,
        'status_filter': status,
    }
    return render(request, 'sports_committee/match_management.html', context)


@login_required
def add_match(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = MatchForm(request.POST, committee=committee)
        if form.is_valid():
            match = form.save(commit=False)
            match.committee = committee
            match.created_by = request.user
            match.save()

            # Notify all members about the match
            members = SportsMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                SportsNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='match_scheduled',
                    title='مباراة جديدة',
                    message=f'مباراة مجدولة: {match.title} - {match.date} {match.time}',
                    related_match=match
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة مباراة: {match.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة المباراة بنجاح!')
            return redirect('sports_match_management')
    else:
        form = MatchForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة مباراة جديدة'
    }
    return render(request, 'sports_committee/match_form.html', context)


@login_required
def edit_match(request, match_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    match = get_object_or_404(Match, id=match_id, committee=committee)

    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match, committee=committee)
        if form.is_valid():
            match = form.save()

            # Notify about results if scores are added
            if match.team1_score is not None and match.team2_score is not None:
                members = SportsMember.objects.filter(committee=committee, is_active=True)
                for member in members:
                    SportsNotification.objects.create(
                        user=member.user,
                        committee=committee,
                        notification_type='results_uploaded',
                        title='نتائج المباراة',
                        message=f'نتيجة {match.title}: {match.team1} {match.team1_score} - {match.team2_score} {match.team2}',
                        related_match=match
                    )

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل مباراة: {match.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل المباراة بنجاح!')
            return redirect('sports_match_management')
    else:
        form = MatchForm(instance=match, committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'match': match,
        'title': 'تعديل المباراة'
    }
    return render(request, 'sports_committee/match_form.html', context)


@login_required
def delete_match(request, match_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    match = get_object_or_404(Match, id=match_id, committee=committee)

    if request.method == 'POST':
        match_title = match.title
        match.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف مباراة: {match_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف المباراة بنجاح!')
        return redirect('sports_match_management')

    context = {
        'committee': committee,
        'object': match,
        'type': 'مباراة'
    }
    return render(request, 'sports_committee/confirm_delete.html', context)


@login_required
def reports(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Task completion stats
    total_tasks = SportsTask.objects.filter(committee=committee).count()
    completed_tasks = SportsTask.objects.filter(committee=committee, status='completed').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Match statistics
    total_matches = Match.objects.filter(committee=committee).count()
    completed_matches = Match.objects.filter(committee=committee, status='completed').count()

    # Task type statistics
    task_stats = SportsTask.objects.filter(committee=committee).values('task_type').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    )

    # Match type statistics
    match_stats = Match.objects.filter(committee=committee).values('match_type').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    )

    # Top participating members
    top_members = SportsMember.objects.filter(
        committee=committee,
        is_active=True
    ).order_by('-participation_score')[:10]

    # Recent reports
    recent_reports = SportsReport.objects.filter(committee=committee).order_by('-created_at')[:5]

    context = {
        'committee': committee,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': round(completion_rate, 1),
        'total_matches': total_matches,
        'completed_matches': completed_matches,
        'task_stats': task_stats,
        'match_stats': match_stats,
        'top_members': top_members,
        'recent_reports': recent_reports,
    }
    return render(request, 'sports_committee/reports.html', context)


@login_required
def add_report(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = SportsReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.committee = committee
            report.created_by = request.user
            report.save()

            # Notify members
            members = SportsMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                SportsNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='report_uploaded',
                    title='تقرير جديد',
                    message=f'تم رفع تقرير جديد: {report.title}',
                    related_report=report
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة تقرير رياضي: {report.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة التقرير بنجاح!')
            return redirect('sports_reports')
    else:
        form = SportsReportForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة تقرير جديد'
    }
    return render(request, 'sports_committee/report_form.html', context)


@login_required
def notifications(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    notifications = SportsNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Mark as read if requested
    if request.method == 'POST':
        notif_id = request.POST.get('notification_id')
        if notif_id:
            SportsNotification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
            return redirect('sports_notifications')

    context = {
        'committee': committee,
        'notifications': notifications,
    }
    return render(request, 'sports_committee/notifications.html', context)


@login_required
def mark_all_read(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sports':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        SportsNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'تم تحديد جميع الإشعارات كمقروءة!')

    return redirect('sports_notifications')