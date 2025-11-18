from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Program, Committee, Student
from accounts.models import User, UserActivity
from .forms import ProgramForm, UserForm


@login_required
def dashboard(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # Statistics
    total_programs = Program.objects.count()
    total_committees = Committee.objects.count()
    total_students = Student.objects.count()
    total_users = User.objects.count()

    # Overall completion rate
    if total_students > 0:
        overall_completion = Student.objects.aggregate(avg_progress=Avg('progress'))['avg_progress'] or 0
    else:
        overall_completion = 0

    # Recent activities
    recent_activities = UserActivity.objects.select_related('user').order_by('-timestamp')[:5]

    context = {
        'total_programs': total_programs,
        'total_committees': total_committees,
        'total_students': total_students,
        'total_users': total_users,
        'overall_completion': round(overall_completion, 1),
        'recent_activities': recent_activities,
    }
    return render(request, 'director_dashboard/dashboard.html', context)


@login_required
def program_management(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    programs = Program.objects.select_related('manager').all()
    return render(request, 'director_dashboard/program_management.html', {'programs': programs})


@login_required
def add_program(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        form = ProgramForm(request.POST)
        if form.is_valid():
            program = form.save()
            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة برنامج جديد: {program.name}',
                ip_address=get_client_ip(request)
            )
            messages.success(request, 'تم إضافة البرنامج بنجاح!')
            return redirect('program_management')
    else:
        form = ProgramForm()

    return render(request, 'director_dashboard/program_form.html', {'form': form, 'title': 'إضافة برنامج جديد'})


@login_required
def edit_program(request, program_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    program = get_object_or_404(Program, id=program_id)

    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            program = form.save()
            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل البرنامج: {program.name}',
                ip_address=get_client_ip(request)
            )
            messages.success(request, 'تم تعديل البرنامج بنجاح!')
            return redirect('program_management')
    else:
        form = ProgramForm(instance=program)

    return render(request, 'director_dashboard/program_form.html', {'form': form, 'title': 'تعديل البرنامج'})


@login_required
def delete_program(request, program_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    program = get_object_or_404(Program, id=program_id)

    if request.method == 'POST':
        program_name = program.name
        program.delete()
        UserActivity.objects.create(
            user=request.user,
            action=f'حذف البرنامج: {program_name}',
            ip_address=get_client_ip(request)
        )
        messages.success(request, 'تم حذف البرنامج بنجاح!')
        return redirect('program_management')

    return render(request, 'director_dashboard/confirm_delete.html', {'object': program, 'type': 'برنامج'})


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from accounts.models import User, UserActivity
from .forms import UserEditForm, UserCreateForm


@login_required
def user_management(request):
    """View for managing all users"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة.')
        return redirect('dashboard')

    users = User.objects.all().order_by('-date_joined')

    # Filter users by role for statistics
    directors = users.filter(role='director')
    managers = users.filter(role='program_manager')
    supervisors = users.filter(role='committee_supervisor')
    students = users.filter(role='student')

    context = {
        'users': users,
        'directors': directors,
        'managers': managers,
        'supervisors': supervisors,
        'students': students,
    }

    return render(request, 'director_dashboard/user_management.html', context)


@login_required
def add_user(request):
    """View for adding new users"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية لإضافة مستخدمين.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة مستخدم جديد: {user.username}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, f'تم إضافة المستخدم {user.username} بنجاح!')
            return redirect('user_management')
    else:
        form = UserCreateForm()

    context = {
        'title': 'إضافة مستخدم جديد',
        'form': form
    }

    return render(request, 'director_dashboard/user_form.html', context)


@login_required
def edit_user(request, user_id):
    """View for editing existing users"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية لتعديل المستخدمين.')
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save()

            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل بيانات المستخدم: {user.username}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, f'تم تحديث بيانات المستخدم {user.username} بنجاح!')
            return redirect('user_management')
    else:
        form = UserEditForm(instance=user)

    context = {
        'title': f'تعديل المستخدم: {user.username}',
        'form': form
    }

    return render(request, 'director_dashboard/user_form.html', context)


@login_required
def toggle_user_status(request, user_id):
    """View for activating/deactivating users"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية لتغيير حالة المستخدمين.')
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)

    # Prevent self-deactivation
    if user == request.user:
        messages.error(request, 'لا يمكنك تعطيل حسابك الخاص.')
        return redirect('user_management')

    # Toggle user status
    user.is_active = not user.is_active
    user.save()

    action = 'تفعيل' if user.is_active else 'تعطيل'

    # Log activity
    UserActivity.objects.create(
        user=request.user,
        action=f'{action} المستخدم: {user.username}',
        ip_address=get_client_ip(request)
    )

    messages.success(request, f'تم {action} حساب المستخدم {user.username} بنجاح!')
    return redirect('user_management')


@login_required
def user_activity_log(request, user_id):
    """View for displaying user activity log"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية لعرض سجل النشاط.')
        return redirect('dashboard')

    user = get_object_or_404(User, id=user_id)
    activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:50]

    context = {
        'target_user': user,
        'activities': activities
    }

    return render(request, 'director_dashboard/user_activity.html', context)


@login_required
def reports(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    # Monthly program achievement
    programs = Program.objects.annotate(
        student_count=Count('student'),
        avg_progress=Avg('student__progress')
    )

    # Most active committees (based on student count and progress)
    active_committees = Committee.objects.annotate(
        student_count=Count('student'),
        avg_progress=Avg('student__progress')
    ).order_by('-student_count', '-avg_progress')[:5]

    # Best students (highest progress)
    best_students = Student.objects.select_related('user', 'program').order_by('-progress')[:10]

    context = {
        'programs': programs,
        'active_committees': active_committees,
        'best_students': best_students,
    }
    return render(request, 'director_dashboard/reports.html', context)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Q
from .models import DirectorAlbum, AlbumPhoto, DirectorFileLibrary, DirectorAlert
from .forms import DirectorAlbumForm, AlbumPhotoForm, DirectorFileLibraryForm, DirectorAlertForm

# Albums Management
@login_required
def album_management(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    albums = DirectorAlbum.objects.all().annotate(
        photos_count=Count('photos')
    ).order_by('-created_at')

    context = {
        'albums': albums,
    }
    return render(request, 'director_dashboard/albums/album_management.html', context)


@login_required
def add_album(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        form = DirectorAlbumForm(request.POST, request.FILES)
        if form.is_valid():
            album = form.save(commit=False)
            album.created_by = request.user
            album.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة ألبوم: {album.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة الألبوم بنجاح!')
            return redirect('album_management')
    else:
        form = DirectorAlbumForm()

    context = {
        'form': form,
        'title': 'إضافة ألبوم جديد'
    }
    return render(request, 'director_dashboard/albums/album_form.html', context)


@login_required
def edit_album(request, album_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    album = get_object_or_404(DirectorAlbum, id=album_id)

    if request.method == 'POST':
        form = DirectorAlbumForm(request.POST, request.FILES, instance=album)
        if form.is_valid():
            album = form.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل الألبوم: {album.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل الألبوم بنجاح!')
            return redirect('album_management')
    else:
        form = DirectorAlbumForm(instance=album)

    context = {
        'form': form,
        'album': album,
        'title': 'تعديل الألبوم'
    }
    return render(request, 'director_dashboard/albums/album_form.html', context)


@login_required
def album_detail(request, album_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    album = get_object_or_404(DirectorAlbum, id=album_id)
    photos = album.photos.all().order_by('order', '-created_at')

    context = {
        'album': album,
        'photos': photos,
    }
    return render(request, 'director_dashboard/albums/album_detail.html', context)


@login_required
def add_photo(request, album_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    album = get_object_or_404(DirectorAlbum, id=album_id)

    if request.method == 'POST':
        form = AlbumPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.album = album
            photo.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة صورة للألبوم: {album.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة الصورة بنجاح!')
            return redirect('album_detail', album_id=album.id)
    else:
        form = AlbumPhotoForm()

    context = {
        'form': form,
        'album': album,
        'title': 'إضافة صورة جديدة'
    }
    return render(request, 'director_dashboard/albums/photo_form.html', context)


@login_required
def delete_album(request, album_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    album = get_object_or_404(DirectorAlbum, id=album_id)

    if request.method == 'POST':
        album_title = album.title
        album.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف الألبوم: {album_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف الألبوم بنجاح!')
        return redirect('album_management')

    context = {
        'object': album,
        'type': 'ألبوم'
    }
    return render(request, 'director_dashboard/confirm_delete.html', context)


@login_required
def delete_photo(request, photo_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    photo = get_object_or_404(AlbumPhoto, id=photo_id)
    album_id = photo.album.id

    if request.method == 'POST':
        photo_title = photo.title
        photo.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف صورة: {photo_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف الصورة بنجاح!')
        return redirect('album_detail', album_id=album_id)

    context = {
        'object': photo,
        'type': 'صورة'
    }
    return render(request, 'director_dashboard/confirm_delete.html', context)


# File Library Management
@login_required
def file_library(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    files = DirectorFileLibrary.objects.all().order_by('-uploaded_at')

    file_type = request.GET.get('type')
    if file_type:
        files = files.filter(file_type=file_type)

    context = {
        'files': files,
        'file_type_filter': file_type,
    }
    return render(request, 'director_dashboard/files/file_library.html', context)


@login_required
def upload_file(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        form = DirectorFileLibraryForm(request.POST, request.FILES)
        if form.is_valid():
            file_obj = form.save(commit=False)
            file_obj.uploaded_by = request.user
            file_obj.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'رفع ملف: {file_obj.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم رفع الملف بنجاح!')
            return redirect('file_library')
    else:
        form = DirectorFileLibraryForm()

    context = {
        'form': form,
        'title': 'رفع ملف جديد'
    }
    return render(request, 'director_dashboard/files/file_form.html', context)


@login_required
def edit_file(request, file_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    file_obj = get_object_or_404(DirectorFileLibrary, id=file_id)

    if request.method == 'POST':
        form = DirectorFileLibraryForm(request.POST, request.FILES, instance=file_obj)
        if form.is_valid():
            file_obj = form.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل الملف: {file_obj.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تعديل الملف بنجاح!')
            return redirect('file_library')
    else:
        form = DirectorFileLibraryForm(instance=file_obj)

    context = {
        'form': form,
        'file': file_obj,
        'title': 'تعديل الملف'
    }
    return render(request, 'director_dashboard/files/file_form.html', context)


@login_required
def delete_file(request, file_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    file_obj = get_object_or_404(DirectorFileLibrary, id=file_id)

    if request.method == 'POST':
        file_title = file_obj.title
        file_obj.file.delete()
        if file_obj.thumbnail:
            file_obj.thumbnail.delete()
        file_obj.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف الملف: {file_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف الملف بنجاح!')
        return redirect('file_library')

    context = {
        'object': file_obj,
        'type': 'ملف'
    }
    return render(request, 'director_dashboard/confirm_delete.html', context)

from django.http import FileResponse
@login_required
def download_file(request, file_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    file_obj = get_object_or_404(DirectorFileLibrary, id=file_id)
    file_obj.increment_download_count()

    response = FileResponse(file_obj.file.open(), as_attachment=True, filename=file_obj.file.name)
    return response


# Alerts Management
@login_required
def alerts_management(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    alerts = DirectorAlert.objects.all().order_by('-created_at')

    alert_type = request.GET.get('type')
    if alert_type:
        alerts = alerts.filter(alert_type=alert_type)

    priority = request.GET.get('priority')
    if priority:
        alerts = alerts.filter(priority=priority)

    unread_count = alerts.filter(is_read=False).count()
    read_count = alerts.filter(is_read=True).count()

    context = {
        'alerts': alerts,
        'unread_count': unread_count,
        'read_count': read_count,
        'alert_type_filter': alert_type,
        'priority_filter': priority,
    }
    return render(request, 'director_dashboard/alerts/alerts_management.html', context)


@login_required
def add_alert(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        form = DirectorAlertForm(request.POST)
        if form.is_valid():
            alert = form.save()

            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة تنبيه: {alert.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة التنبيه بنجاح!')
            return redirect('alerts_management')
    else:
        form = DirectorAlertForm()

    context = {
        'form': form,
        'title': 'إضافة تنبيه جديد'
    }
    return render(request, 'director_dashboard/alerts/alert_form.html', context)


@login_required
def mark_alert_read(request, alert_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    alert = get_object_or_404(DirectorAlert, id=alert_id)
    alert.mark_as_read()

    messages.success(request, 'تم تحديد التنبيه كمقروء!')
    return redirect('alerts_management')


@login_required
def mark_all_alerts_read(request):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    if request.method == 'POST':
        DirectorAlert.objects.filter(is_read=False).update(is_read=True)

        UserActivity.objects.create(
            user=request.user,
            action='تحديد جميع التنبيهات كمقروءة',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم تحديد جميع التنبيهات كمقروءة!')

    return redirect('alerts_management')


@login_required
def delete_alert(request, alert_id):
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    alert = get_object_or_404(DirectorAlert, id=alert_id)

    if request.method == 'POST':
        alert_title = alert.title
        alert.delete()

        UserActivity.objects.create(
            user=request.user,
            action=f'حذف تنبيه: {alert_title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف التنبيه بنجاح!')
        return redirect('alerts_management')

    context = {
        'object': alert,
        'type': 'تنبيه'
    }
    return render(request, 'director_dashboard/confirm_delete.html', context)


def create_director_alert(title, message, alert_type, priority='medium',
                         related_user=None, related_program=None,
                         related_committee=None, action_url=''):
    """Utility function to create alerts from other parts of the system"""
    alert = DirectorAlert.objects.create(
        title=title,
        message=message,
        alert_type=alert_type,
        priority=priority,
        related_user=related_user,
        related_program=related_program,
        related_committee=related_committee,
        action_url=action_url
    )
    return alert


@login_required
def debug_images(request):
    """Debug view to check image paths"""
    if request.user.role != 'director':
        return redirect('home')

    from django.conf import settings
    import os

    photos = AlbumPhoto.objects.all()[:5]

    debug_info = {
        'MEDIA_ROOT': settings.MEDIA_ROOT,
        'MEDIA_URL': settings.MEDIA_URL,
        'BASE_DIR': settings.BASE_DIR,
        'photos': []
    }

    for photo in photos:
        debug_info['photos'].append({
            'title': photo.title,
            'image_path': photo.image.path if photo.image else 'No image',
            'image_url': photo.image.url if photo.image else 'No URL',
            'exists': os.path.exists(photo.image.path) if photo.image else False,
        })

    return JsonResponse(debug_info)