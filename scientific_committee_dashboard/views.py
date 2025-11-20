from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from director_dashboard.models import Committee
from accounts.models import User, UserActivity
from .models import (ScientificTask, ScientificMember, ScientificFile,
                     Lecture, LectureAttendance, ScientificReport, ScientificNotification)
from .forms import (ScientificTaskForm, ScientificMemberForm, ScientificFileForm,
                    LectureForm, LectureAttendanceForm, ScientificReportForm)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required
def scientific_dashboard(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Statistics
    total_members = ScientificMember.objects.filter(committee=committee, is_active=True).count()
    total_tasks = ScientificTask.objects.filter(committee=committee).count()
    completed_tasks = ScientificTask.objects.filter(committee=committee, status='completed').count()
    pending_tasks = ScientificTask.objects.filter(committee=committee, status='pending').count()

    # Lectures statistics
    upcoming_lectures = Lecture.objects.filter(
        committee=committee,
        status='scheduled',
        date__gte=timezone.now().date()
    ).count()

    # Completion rate
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Recent data
    recent_tasks = ScientificTask.objects.filter(committee=committee).order_by('-created_at')[:5]
    next_lectures = Lecture.objects.filter(
        committee=committee,
        status='scheduled',
        date__gte=timezone.now().date()
    ).order_by('date', 'time')[:5]

    # Unread notifications
    unread_notifications = ScientificNotification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    # Top members
    top_members = ScientificMember.objects.filter(
        committee=committee,
        is_active=True
    ).order_by('-participation_score')[:5]

    # Task distribution
    task_distribution = ScientificTask.objects.filter(committee=committee).values('task_type').annotate(
        count=Count('id')
    )

    context = {
        'committee': committee,
        'total_members': total_members,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'upcoming_lectures': upcoming_lectures,
        'completion_rate': round(completion_rate, 1),
        'recent_tasks': recent_tasks,
        'next_lectures': next_lectures,
        'unread_notifications': unread_notifications,
        'top_members': top_members,
        'task_distribution': task_distribution,
    }
    return render(request, 'scientific_committee/dashboard.html', context)


@login_required
def committee_info(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = ScientificMember.objects.filter(committee=committee)
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
    return render(request, 'scientific_committee/committee_info.html', context)


# Task Management
@login_required
def task_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    tasks = ScientificTask.objects.filter(committee=committee).order_by('-created_at')

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
    return render(request, 'scientific_committee/task_management.html', context)


@login_required
def add_task(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = ScientificTaskForm(request.POST, committee=committee)
        if form.is_valid():
            task = form.save(commit=False)
            task.committee = committee
            task.created_by = request.user
            task.save()

            members = ScientificMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ScientificNotification.objects.create(
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
                action=f'إضافة مهمة علمية: {task.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة المهمة بنجاح!')
            return redirect('scientific_task_management')
    else:
        form = ScientificTaskForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة مهمة جديدة'
    }
    return render(request, 'scientific_committee/task_form.html', context)


@login_required
def edit_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(ScientificTask, id=task_id, committee=committee)

    if request.method == 'POST':
        form = ScientificTaskForm(request.POST, instance=task, committee=committee)
        if form.is_valid():
            task = form.save()

            members = ScientificMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ScientificNotification.objects.create(
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
                action=f'تعديل مهمة علمية: {task.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل المهمة بنجاح!')
            return redirect('scientific_task_management')
    else:
        form = ScientificTaskForm(instance=task, committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'task': task,
        'title': 'تعديل المهمة'
    }
    return render(request, 'scientific_committee/task_form.html', context)


@login_required
def delete_task(request, task_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    task = get_object_or_404(ScientificTask, id=task_id, committee=committee)

    if request.method == 'POST':
        task_title = task.title
        task.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف مهمة علمية: {task_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف المهمة بنجاح!')
        return redirect('scientific_task_management')

    context = {
        'committee': committee,
        'object': task,
        'type': 'مهمة'
    }
    return render(request, 'scientific_committee/confirm_delete.html', context)


# Member Management
@login_required
def member_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    members = ScientificMember.objects.filter(committee=committee).select_related('user').order_by(
        '-participation_score')

    # Calculate statistics
    active_members_count = members.filter(is_active=True).count()
    avg_participation = members.aggregate(avg=Avg('participation_score'))['avg'] or 0
    top_member = members.first()

    context = {
        'committee': committee,
        'members': members,
        'active_members_count': active_members_count,
        'avg_participation': round(avg_participation, 1),
        'top_member': top_member,
    }
    return render(request, 'scientific_committee/member_management.html', context)


@login_required
def view_member(request, member_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    member = get_object_or_404(ScientificMember, id=member_id, committee=committee)

    # Get member statistics
    tasks_assigned = ScientificTask.objects.filter(
        committee=committee,
        assigned_to_name__icontains=member.user.get_full_name()
    ).count()

    tasks_completed = ScientificTask.objects.filter(
        committee=committee,
        assigned_to_name__icontains=member.user.get_full_name(),
        status='completed'
    ).count()

    lectures_given = Lecture.objects.filter(
        committee=committee,
        lecturer=member.user
    ).count()

    context = {
        'committee': committee,
        'member': member,
        'tasks_assigned': tasks_assigned,
        'tasks_completed': tasks_completed,
        'lectures_given': lectures_given,
    }
    return render(request, 'scientific_committee/view_member.html', context)


@login_required
def edit_member(request, member_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    member = get_object_or_404(ScientificMember, id=member_id, committee=committee)

    if request.method == 'POST':
        form = ScientificMemberForm(request.POST, instance=member, committee=committee)
        if form.is_valid():
            # تأكد من أن المستخدم لم يتغير
            updated_member = form.save(commit=False)
            # الحفاظ على المستخدم الأصلي (لضمان الأمان)
            updated_member.user = member.user
            updated_member.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل عضو: {member.user.get_full_name()}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل بيانات العضو بنجاح!')
            return redirect('scientific_member_management')
    else:
        form = ScientificMemberForm(instance=member, committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'member': member,
        'title': f'تعديل العضو: {member.user.get_full_name()}'
    }
    return render(request, 'scientific_committee/member_form.html', context)


@login_required
def delete_member(request, member_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    member = get_object_or_404(ScientificMember, id=member_id, committee=committee)

    if request.method == 'POST':
        member_name = member.user.get_full_name()
        member.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف عضو: {member_name}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف العضو بنجاح!')
        return redirect('scientific_member_management')

    context = {
        'committee': committee,
        'object': member,
        'type': 'عضو',
        'object_name': member.user.get_full_name()
    }
    return render(request, 'scientific_committee/confirm_delete.html', context)


@login_required
def add_member(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = ScientificMemberForm(request.POST, committee=committee)
        if form.is_valid():
            member = form.save(commit=False)
            member.committee = committee
            member.save()

            messages.success(request, 'تم إضافة العضو بنجاح!')
            return redirect('scientific_member_management')
    else:
        form = ScientificMemberForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة عضو جديد'
    }
    return render(request, 'scientific_committee/member_form.html', context)


# File Library
@login_required
def file_library(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    files = ScientificFile.objects.filter(committee=committee).order_by('-uploaded_at')

    # Filter by type
    file_type = request.GET.get('type')
    if file_type:
        files = files.filter(file_type=file_type)

    context = {
        'committee': committee,
        'files': files,
        'file_type_filter': file_type,
    }
    return render(request, 'scientific_committee/file_library.html', context)


@login_required
def upload_file(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = ScientificFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.save(commit=False)
            file_obj.committee = committee
            file_obj.uploaded_by = request.user
            file_obj.save()

            # Notify all committee members
            members = ScientificMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ScientificNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='file_uploaded',
                    title='ملف جديد',
                    message=f'تم رفع ملف جديد: {file_obj.title}',
                    related_file=file_obj
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'رفع ملف علمي: {file_obj.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم رفع الملف بنجاح!')
            return redirect('scientific_file_library')
    else:
        form = ScientificFileForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'رفع ملف جديد'
    }
    return render(request, 'scientific_committee/file_form.html', context)


@login_required
def delete_file(request, file_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    file_obj = get_object_or_404(ScientificFile, id=file_id, committee=committee)

    if request.method == 'POST':
        file_title = file_obj.title
        file_obj.file.delete()
        file_obj.delete()

        messages.success(request, 'تم حذف الملف بنجاح!')
        return redirect('scientific_file_library')

    context = {
        'committee': committee,
        'object': file_obj,
        'type': 'ملف'
    }
    return render(request, 'scientific_committee/confirm_delete.html', context)


# Lecture Management
@login_required
def lecture_management(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    lectures = Lecture.objects.filter(committee=committee).order_by('-date', '-time')

    # Filters
    lecture_type = request.GET.get('type')
    if lecture_type:
        lectures = lectures.filter(lecture_type=lecture_type)

    status = request.GET.get('status')
    if status:
        lectures = lectures.filter(status=status)

    context = {
        'committee': committee,
        'lectures': lectures,
        'lecture_type_filter': lecture_type,
        'status_filter': status,
    }
    return render(request, 'scientific_committee/lecture_management.html', context)


@login_required
def add_lecture(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = LectureForm(request.POST, committee=committee)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.committee = committee
            lecture.created_by = request.user
            lecture.save()

            # Notify all members about the lecture
            members = ScientificMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ScientificNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='lecture_scheduled',
                    title='محاضرة جديدة',
                    message=f'محاضرة مجدولة: {lecture.title} - {lecture.date} {lecture.time}',
                    related_lecture=lecture
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة محاضرة: {lecture.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة المحاضرة بنجاح!')
            return redirect('scientific_lecture_management')
    else:
        form = LectureForm(committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة محاضرة جديدة'
    }
    return render(request, 'scientific_committee/lecture_form.html', context)


@login_required
def edit_lecture(request, lecture_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    lecture = get_object_or_404(Lecture, id=lecture_id, committee=committee)

    if request.method == 'POST':
        form = LectureForm(request.POST, instance=lecture, committee=committee)
        if form.is_valid():
            lecture = form.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل محاضرة: {lecture.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل المحاضرة بنجاح!')
            return redirect('scientific_lecture_management')
    else:
        form = LectureForm(instance=lecture, committee=committee)

    context = {
        'committee': committee,
        'form': form,
        'lecture': lecture,
        'title': 'تعديل المحاضرة'
    }
    return render(request, 'scientific_committee/lecture_form.html', context)


@login_required
def delete_lecture(request, lecture_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    lecture = get_object_or_404(Lecture, id=lecture_id, committee=committee)

    if request.method == 'POST':
        lecture_title = lecture.title
        lecture.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف محاضرة: {lecture_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف المحاضرة بنجاح!')
        return redirect('scientific_lecture_management')

    context = {
        'committee': committee,
        'object': lecture,
        'type': 'محاضرة'
    }
    return render(request, 'scientific_committee/confirm_delete.html', context)


@login_required
def lecture_attendance(request, lecture_id):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    lecture = get_object_or_404(Lecture, id=lecture_id, committee=committee)
    attendances = LectureAttendance.objects.filter(lecture=lecture).select_related('user')

    if request.method == 'POST':
        form = LectureAttendanceForm(request.POST)
        if form.is_valid():
            # Handle attendance recording
            pass

    context = {
        'committee': committee,
        'lecture': lecture,
        'attendances': attendances,
    }
    return render(request, 'scientific_committee/lecture_attendance.html', context)


# Reports
@login_required
def reports(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    # Task completion stats
    total_tasks = ScientificTask.objects.filter(committee=committee).count()
    completed_tasks = ScientificTask.objects.filter(committee=committee, status='completed').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Lecture statistics
    total_lectures = Lecture.objects.filter(committee=committee).count()
    completed_lectures = Lecture.objects.filter(committee=committee, status='completed').count()

    # Task type statistics
    task_stats = ScientificTask.objects.filter(committee=committee).values('task_type').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    )

    # Lecture type statistics
    lecture_stats = Lecture.objects.filter(committee=committee).values('lecture_type').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    )

    # Top participating members
    top_members = ScientificMember.objects.filter(
        committee=committee,
        is_active=True
    ).order_by('-participation_score')[:10]

    # Recent reports
    recent_reports = ScientificReport.objects.filter(committee=committee).order_by('-created_at')[:5]

    context = {
        'committee': committee,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': round(completion_rate, 1),
        'total_lectures': total_lectures,
        'completed_lectures': completed_lectures,
        'task_stats': task_stats,
        'lecture_stats': lecture_stats,
        'top_members': top_members,
        'recent_reports': recent_reports,
    }
    return render(request, 'scientific_committee/reports.html', context)


@login_required
def add_report(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    if request.method == 'POST':
        form = ScientificReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save(commit=False)
            report.committee = committee
            report.created_by = request.user
            report.save()

            # Notify members
            members = ScientificMember.objects.filter(committee=committee, is_active=True)
            for member in members:
                ScientificNotification.objects.create(
                    user=member.user,
                    committee=committee,
                    notification_type='report_uploaded',
                    title='تقرير جديد',
                    message=f'تم رفع تقرير جديد: {report.title}',
                    related_report=report
                )

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة تقرير علمي: {report.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة التقرير بنجاح!')
            return redirect('scientific_reports')
    else:
        form = ScientificReportForm()

    context = {
        'committee': committee,
        'form': form,
        'title': 'إضافة تقرير جديد'
    }
    return render(request, 'scientific_committee/report_form.html', context)


# Notifications
@login_required
def notifications(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        committee = Committee.objects.get(supervisor=request.user)
    except Committee.DoesNotExist:
        messages.error(request, 'لم يتم تعيين لجنة لك بعد')
        return redirect('home')

    notifications = ScientificNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    # Mark as read if requested
    if request.method == 'POST':
        notif_id = request.POST.get('notification_id')
        if notif_id:
            ScientificNotification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
            return redirect('scientific_notifications')

    context = {
        'committee': committee,
        'notifications': notifications,
    }
    return render(request, 'scientific_committee/notifications.html', context)


@login_required
def mark_all_read(request):
    if request.user.role != 'committee_supervisor' or request.user.supervisor_type != 'scientific':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        ScientificNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'تم تحديد جميع الإشعارات كمقروءة!')

    return redirect('scientific_notifications')
