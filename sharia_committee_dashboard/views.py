from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from director_dashboard.models import Committee
from accounts.models import User, UserActivity
from .models import (ShariaTask, ShariaMember, ShariaFile, DailyMessage,
                     FamilyCompetition, YouthBook, ShariaReport, ShariaNotification)
from .forms import (ShariaTaskForm, ShariaMemberForm, ShariaFileForm, DailyMessageForm,
                    FamilyCompetitionForm, YouthBookForm, ShariaReportForm)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def sharia_dashboard(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Statistics
    total_members = ShariaMember.objects.filter(committee=committee, is_active=True).count()
    total_tasks = ShariaTask.objects.filter(committee=committee).count()
    completed_tasks = ShariaTask.objects.filter(committee=committee, status='completed').count()
    pending_tasks = ShariaTask.objects.filter(committee=committee, status='pending').count()
    active_competitions = FamilyCompetition.objects.filter(committee=committee, status='active').count()
    pending_messages = DailyMessage.objects.filter(committee=committee, is_sent=False, scheduled_date__gte=timezone.now().date()).count()
    books_in_progress = YouthBook.objects.filter(committee=committee, status='reading').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Recent data
    recent_tasks = ShariaTask.objects.filter(committee=committee).order_by('-created_at')[:5]
    upcoming_messages = DailyMessage.objects.filter(committee=committee, is_sent=False, scheduled_date__gte=timezone.now().date()).order_by('scheduled_date')[:5]
    current_competitions = FamilyCompetition.objects.filter(committee=committee, status='active').order_by('-created_at')[:3]
    unread_notifications = ShariaNotification.objects.filter(user=request.user, is_read=False).count()
    top_members = ShariaMember.objects.filter(committee=committee, is_active=True).order_by('-participation_score')[:5]
    task_distribution = ShariaTask.objects.filter(committee=committee).values('task_type').annotate(count=Count('id'))

    context = {
        'committee': committee,
        'total_members': total_members,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'active_competitions': active_competitions,
        'pending_messages': pending_messages,
        'books_in_progress': books_in_progress,
        'completion_rate': round(completion_rate, 1),
        'recent_tasks': recent_tasks,
        'upcoming_messages': upcoming_messages,
        'current_competitions': current_competitions,
        'unread_notifications': unread_notifications,
        'top_members': top_members,
        'task_distribution': task_distribution,
    }
    return render(request, 'sharia_committee/dashboard.html', context)


@login_required
def committee_info(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = ShariaMember.objects.filter(committee=committee)
    active_members = members.filter(is_active=True).count()
    avg_participation = members.aggregate(avg=Avg('participation_score'))['avg'] or 0

    context = {
        'committee': committee,
        'total_members': members.count(),
        'active_members': active_members,
        'avg_participation': round(avg_participation, 1),
    }
    return render(request, 'sharia_committee/committee_info.html', context)


# Task Management
@login_required
def task_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    tasks = ShariaTask.objects.filter(committee=committee).order_by('-created_at')

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
    return render(request, 'sharia_committee/task_management.html', context)


@login_required
def add_task(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = ShariaTaskForm(request.POST, committee=committee)
        if form.is_valid():
            task = form.save(commit=False)
            task.committee = committee
            task.created_by = request.user
            task.save()

            members = ShariaMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ShariaNotification.objects.create(
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
                action=f'إضافة مهمة شرعية: {task.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة المهمة بنجاح!')
            return redirect('sharia_task_management')
    else:
        form = ShariaTaskForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة مهمة جديدة'
    }
    return render(request, 'sharia_committee/task_form.html', context)


@login_required
def edit_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(ShariaTask, id=task_id, committee=committee)

    if request.method == 'POST':
        form = ShariaTaskForm(request.POST, instance=task, committee=committee)
        if form.is_valid():
            task = form.save()

            members = ShariaMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ShariaNotification.objects.create(
                    user=request.user,
                    committee=committee,
                    notification_type='task_updated',
                    title='تعديل مهمة',
                    message=f'تم تعديل المهمة: {task.title}' + (
                        f' للمسؤول: {task.assigned_to_name}' if task.assigned_to_name else ''),
                    related_task=task
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل مهمة شرعية: {task.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل المهمة بنجاح!')
            return redirect('sharia_task_management')
    else:
        form = ShariaTaskForm(instance=task, committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'task': task,
        'title': 'تعديل المهمة'
    }
    return render(request, 'sharia_committee/task_form.html', context)


@login_required
def delete_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(ShariaTask, id=task_id, committee=committee)

    if request.method == 'POST':
        task_title = task.title
        task.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف مهمة شرعية: {task_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف المهمة بنجاح!')
        return redirect('sharia_task_management')

    context = {
        'committee': committee,
        'object': task,
        'type': 'مهمة'
    }
    return render(request, 'sharia_committee/confirm_delete.html', context)


# Member Management
@login_required
def member_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = ShariaMember.objects.filter(committee=committee).select_related('user').order_by('-participation_score')

    context = {
        'committee': committee,
        'members': members,
    }
    return render(request, 'sharia_committee/member_management.html', context)


@login_required
def add_member(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = ShariaMemberForm(request.POST, committee=committee)
        if form.is_valid():
            member = form.save(commit=False)
            member.committee = committee
            member.save()

            messages.success(request, 'تم إضافة العضو بنجاح!')
            return redirect('sharia_member_management')
    else:
        form = ShariaMemberForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة عضو جديد'
    }
    return render(request, 'sharia_committee/member_form.html', context)


# File Library
@login_required
def file_library(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    files = ShariaFile.objects.filter(committee=committee).order_by('-uploaded_at')

    file_type = request.GET.get('type')
    if file_type:
        files = files.filter(file_type=file_type)

    context = {
        'committee': committee,
        'files': files,
        'file_type_filter': file_type,
    }
    return render(request, 'sharia_committee/file_library.html', context)


@login_required
def upload_file(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = ShariaFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.save(commit=False)
            file_obj.committee = committee
            file_obj.uploaded_by = request.user
            file_obj.save()

            members = ShariaMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ShariaNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='lesson_scheduled',
                    title='ملف جديد',
                    message=f'تم رفع ملف جديد: {file_obj.title}'
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'رفع ملف شرعي: {file_obj.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم رفع الملف بنجاح!')
            return redirect('sharia_file_library')
    else:
        form = ShariaFileForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'رفع ملف جديد'
    }
    return render(request, 'sharia_committee/file_form.html', context)


@login_required
def delete_file(request, file_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    file_obj = get_object_or_404(ShariaFile, id=file_id, committee=committee)

    if request.method == 'POST':
        file_title = file_obj.title
        file_obj.file.delete()
        file_obj.delete()

        messages.success(request, 'تم حذف الملف بنجاح!')
        return redirect('sharia_file_library')

    context = {
        'committee': committee,
        'object': file_obj,
        'type': 'ملف'
    }
    return render(request, 'sharia_committee/confirm_delete.html', context)


# Daily Messages
@login_required
def message_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    messages_list = DailyMessage.objects.filter(committee=committee).order_by('-scheduled_date')

    context = {
        'committee': committee,
        'messages_list': messages_list,
    }
    return render(request, 'sharia_committee/message_management.html', context)


@login_required
def add_message(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = DailyMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.committee = committee
            message.created_by = request.user
            message.save()

            members = ShariaMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ShariaNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='message_sent',
                    title='رسالة جديدة',
                    message=f'تم جدولة رسالة جديدة: {message.title}'
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة رسالة: {message.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة الرسالة بنجاح!')
            return redirect('sharia_message_management')
    else:
        form = DailyMessageForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة رسالة جديدة'
    }
    return render(request, 'sharia_committee/message_form.html', context)


# Family Competitions
@login_required
def competition_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    competitions = FamilyCompetition.objects.filter(committee=committee).order_by('-created_at')

    context = {
        'committee': committee,
        'competitions': competitions,
    }
    return render(request, 'sharia_committee/competition_management.html', context)


@login_required
def add_competition(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = FamilyCompetitionForm(request.POST, request.FILES)
        if form.is_valid():
            competition = form.save(commit=False)
            competition.committee = committee
            competition.created_by = request.user
            competition.save()

            members = ShariaMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ShariaNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='competition_uploaded',
                    title='مسابقة جديدة',
                    message=f'تم رفع مسابقة جديدة: {competition.title}',
                    related_competition=competition
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة مسابقة: {competition.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة المسابقة بنجاح!')
            return redirect('sharia_competition_management')
    else:
        form = FamilyCompetitionForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة مسابقة جديدة'
    }
    return render(request, 'sharia_committee/competition_form.html', context)


# Youth Books
@login_required
def book_management(request):
    try:
        # Check user permissions
        if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
            messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
            return redirect('home')

        # Get committee for the current user
        try:
            committee = Committee.objects.get(supervisor=request.user)
        except Committee.DoesNotExist:
            messages.error(request, 'لم يتم تعيين لجنة لك بعد')
            return redirect('home')
        except Committee.MultipleObjectsReturned:
            messages.error(request, 'تم تعيين أكثر من لجنة لك. يرجى التواصل مع الإدارة')
            return redirect('home')

        # Get books for the committee
        try:
            books = YouthBook.objects.filter(committee=committee).order_by('-created_at')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء جلب بيانات الكتب: {str(e)}')
            books = YouthBook.objects.none()  # Return empty queryset

        context = {
            'committee': committee,
            'books': books,
        }

        return render(request, 'sharia_committee/book_management.html', context)

    except Exception as e:
        # Catch any unexpected errors
        messages.error(request, f'حدث خطأ غير متوقع: {str(e)}')
        return redirect('home')


@login_required
def add_book(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = YouthBookForm(request.POST, committee=committee)
        if form.is_valid():
            book = form.save(commit=False)
            book.committee = committee
            book.created_by = request.user
            book.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة كتاب: {book.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة الكتاب بنجاح!')
            return redirect('sharia_book_management')
    else:
        form = YouthBookForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة كتاب جديد'
    }
    return render(request, 'sharia_committee/book_form.html', context)


# Reports
@login_required
def reports(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    total_tasks = ShariaTask.objects.filter(committee=committee).count()
    completed_tasks = ShariaTask.objects.filter(committee=committee, status='completed').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    task_stats = ShariaTask.objects.filter(committee=committee).values('task_type').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    )

    top_members = ShariaMember.objects.filter(committee=committee, is_active=True).order_by('-participation_score')[:10]
    recent_reports = ShariaReport.objects.filter(committee=committee).order_by('-created_at')[:5]

    context = {
        'committee': committee,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': round(completion_rate, 1),
        'task_stats': task_stats,
        'top_members': top_members,
        'recent_reports': recent_reports,
    }
    return render(request, 'sharia_committee/reports.html', context)


@login_required
def add_report(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = ShariaReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.committee = committee
            report.created_by = request.user
            report.save()

            members = ShariaMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ShariaNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='report_uploaded',
                    title='تقرير جديد',
                    message=f'تم رفع تقرير جديد: {report.title}',
                    related_report=report
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة تقرير شرعي: {report.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة التقرير بنجاح!')
            return redirect('sharia_reports')
    else:
        form = ShariaReportForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة تقرير جديد'
    }
    return render(request, 'sharia_committee/report_form.html', context)


# Notifications
@login_required
def notifications(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    notifications = ShariaNotification.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST':
        notif_id = request.POST.get('notification_id')
        if notif_id:
            ShariaNotification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
            return redirect('sharia_notifications')

    context = {
        'committee': committee,
        'notifications': notifications,
    }
    return render(request, 'sharia_committee/notifications.html', context)


@login_required
def mark_all_read(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'sharia':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        ShariaNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'تم تحديد جميع الإشعارات كمقروءة!')

    return redirect('sharia_notifications')
