from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from .models import Program, Committee, Student
from accounts.models import User, UserActivity
from .forms import ProgramForm, UserForm


from cultural_committee_dashboard.models import DailyPhrase
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

    # Get daily phrase from cultural committee of the first program
    daily_phrase = None
    try:
        first_program = Program.objects.first()
        if first_program:
            cultural_committee = Committee.objects.filter(
                program=first_program,
            ).first()

            if cultural_committee:
                from datetime import date
                daily_phrase = DailyPhrase.objects.filter(
                    display_date=date.today(),
                    is_active=True
                ).first()
    except Exception as e:
        # Log the error but don't break the dashboard
        print(f"Error fetching daily phrase: {e}")

    context = {
        'total_programs': total_programs,
        'total_committees': total_committees,
        'total_students': total_students,
        'total_users': total_users,
        'overall_completion': round(overall_completion, 1),
        'recent_activities': recent_activities,
        'daily_phrase': daily_phrase,
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


from django.http import HttpResponse
from django.template.loader import render_to_string
import pandas as pd
from datetime import datetime
import tempfile
from django.db.models import Count, Avg


@login_required
def export_reports_pdf(request):
    try:
        # Import only when function is called
        from weasyprint import HTML
        # Use HTML here
    except ImportError:
        messages.error(request, 'WeasyPrint غير متوفر')
        return redirect('reports')
    """Export reports as PDF"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        # Get the same data as reports view
        programs = Program.objects.annotate(
            student_count=Count('student'),
            avg_progress=Avg('student__progress')
        )

        active_committees = Committee.objects.annotate(
            student_count=Count('student'),
            avg_progress=Avg('student__progress')
        ).order_by('-student_count', '-avg_progress')[:5]

        best_students = Student.objects.select_related('user', 'program').order_by('-progress')[:10]

        context = {
            'programs': programs,
            'active_committees': active_committees,
            'best_students': best_students,
            'export_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }

        # Render HTML template
        html_string = render_to_string('director_dashboard/reports_pdf.html', context)

        # Create PDF
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf_file = html.write_pdf()

        # Create response
        response = HttpResponse(pdf_file, content_type='application/pdf')
        filename = f'reports_export_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='تصدير تقارير PDF',
            ip_address=get_client_ip(request)
        )

        return response

    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء تصدير PDF: {str(e)}')
        return redirect('reports')


@login_required
def export_reports_excel(request):
    """Export reports as Excel"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    try:
        # Get data
        programs = Program.objects.annotate(
            student_count=Count('student'),
            avg_progress=Avg('student__progress')
        )

        active_committees = Committee.objects.annotate(
            student_count=Count('student'),
            avg_progress=Avg('student__progress')
        ).order_by('-student_count', '-avg_progress')[:5]

        best_students = Student.objects.select_related('user', 'program').order_by('-progress')[:10]

        # Create Excel file with multiple sheets
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            with pd.ExcelWriter(tmp_file.name, engine='openpyxl') as writer:

                # Programs Sheet
                programs_data = []
                for program in programs:
                    programs_data.append({
                        'اسم البرنامج': program.name,
                        'مدير البرنامج': program.manager.get_full_name() if program.manager else 'غير معين',
                        'عدد الطلاب': program.student_count,
                        'متوسط التقدم %': round(program.avg_progress or 0, 1),
                        'تاريخ البدء': program.start_date,
                        'تاريخ الانتهاء': program.end_date,
                        'الحالة': 'نشط' if program.is_active else 'منتهي'
                    })

                if programs_data:
                    df_programs = pd.DataFrame(programs_data)
                    df_programs.to_excel(writer, sheet_name='البرامج', index=False)

                # Active Committees Sheet
                committees_data = []
                for committee in active_committees:
                    committees_data.append({
                        'اسم اللجنة': committee.name,
                        'البرنامج': committee.program.name,
                        'عدد الأعضاء': committee.student_count,
                        'متوسط التقدم %': round(committee.avg_progress or 0, 1),
                        'المشرف': committee.supervisor.get_full_name() if committee.supervisor else 'غير معين'
                    })

                if committees_data:
                    df_committees = pd.DataFrame(committees_data)
                    df_committees.to_excel(writer, sheet_name='اللجان النشطة', index=False)

                # Best Students Sheet
                students_data = []
                for student in best_students:
                    students_data.append({
                        'اسم الطالب': student.user.get_full_name() or student.user.username,
                        'البرنامج': student.program.name,
                        'اللجنة': student.committee.name if student.committee else '-',
                        'مستوى الحفظ': student.memorization_level or 'غير محدد',
                        'نسبة التقدم %': student.progress,
                        'تاريخ الانضمام': student.joined_date
                    })

                if students_data:
                    df_students = pd.DataFrame(students_data)
                    df_students.to_excel(writer, sheet_name='أفضل الطلاب', index=False)

            # Read the file and create response
            with open(tmp_file.name, 'rb') as f:
                excel_data = f.read()

        # Create response
        response = HttpResponse(excel_data,
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        filename = f'reports_export_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='تصدير تقارير Excel',
            ip_address=get_client_ip(request)
        )

        return response

    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء تصدير Excel: {str(e)}')
        return redirect('reports')


# ============================================
# حاسبة النقاط - Points Calculator
# ============================================
from .models import PointsCalculatorSettings,PointsResult
def convert_arabic_to_english_number(text):
    """تحويل الأرقام العربية إلى إنجليزية"""
    if not text:
        return text

    arabic_to_english = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
    }

    result = ''
    for char in text:
        if char in arabic_to_english:
            result += arabic_to_english[char]
        else:
            result += char

    return result


def normalize_week_number(week_number_str):
    """تحويل رقم الأسبوع إلى إنجليزية والتحقق من صحته"""
    if not week_number_str:
        return None

    normalized = convert_arabic_to_english_number(week_number_str.strip())

    if not normalized.isdigit():
        return None

    try:
        week_num = int(normalized)
        if 1 <= week_num <= 52:
            return week_num
    except ValueError:
        pass

    return None


def get_user_settings(user):
    """الحصول على إعدادات المستخدم أو الإعدادات الافتراضية"""
    try:
        settings = PointsCalculatorSettings.objects.get(user=user)
        if not settings.batches:
            default_settings = PointsCalculatorSettings.get_default_settings()
            return {
                'program_name': settings.program_name,
                'committees': settings.committees if settings.committees else default_settings['committees'],
                'batches': default_settings['batches'],
                'default_committee_name': settings.default_committee_name,
                'current_week': settings.current_week
            }
        else:
            return {
                'program_name': settings.program_name,
                'committees': settings.committees if settings.committees else [],
                'batches': settings.batches,
                'default_committee_name': settings.default_committee_name,
                'current_week': settings.current_week
            }
    except PointsCalculatorSettings.DoesNotExist:
        return PointsCalculatorSettings.get_default_settings()


def generate_template_message(settings):
    """إنشاء القالب المفرغ بناءً على الإعدادات"""
    lines = []

    lines.append(f"📌 اسم البرنامج: {settings['program_name']}")
    lines.append("")
    lines.append(f"📋 اسم اللجنة: {settings['default_committee_name']}")
    lines.append("")
    week_num = settings.get('current_week', 1)
    lines.append(f"🗓 نقاط الأسبوع الـ({week_num})")
    lines.append("")
    lines.append("✨ رصد نقاط الترم ✨")
    lines.append("")
    lines.append("⸻")
    lines.append("")

    for batch in settings['batches']:
        batch_name = batch.get('name', '')
        emoji = batch.get('emoji', '👨‍🎓')
        students = batch.get('students', [])

        lines.append(f"👨‍🎓 دفعة {batch_name}:")
        lines.append("")

        if students:
            for student_name in students:
                if student_name.strip():
                    lines.append(f"▫ {student_name.strip()} {emoji} (0)")
        else:
            student_count = batch.get('student_count', 0)
            for i in range(student_count):
                lines.append(f"▫ [اسم الطالب {i + 1}] {emoji} (0)")

        lines.append("")
        lines.append("⸻")
        lines.append("")

    return "\n".join(lines)


@login_required(login_url="/accounts/login/")
def points_main(request):
    """الصفحة الرئيسية للنقاط"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    return render(request, 'director_dashboard/points/points_main.html')


@login_required(login_url="/accounts/login/")
def points_calculator(request):
    """عرض واجهة حاسبة النقاط مع القالب المفرغ"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    settings = get_user_settings(request.user)
    template_message = generate_template_message(settings)

    return render(request, 'director_dashboard/points/points_calculator.html', {
        "template_message": template_message,
        "settings": settings
    })


@login_required(login_url="/accounts/login/")
def process_points(request):
    """معالجة الرسائل المجمعة وحساب النقاط"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    if request.method == "POST":
        combined_messages = request.POST.get("combined_messages", "").strip()
        week_number_str = request.POST.get("week_number", "").strip()

        if not combined_messages:
            return render(request, "director_dashboard/points/points_calculator.html", {
                "error": "الرجاء إدخال الرسائل المجمعة",
                "template_message": request.POST.get("template_message", ""),
                "combined_messages": combined_messages
            })

        week_number = normalize_week_number(week_number_str)
        if week_number is None:
            return render(request, "director_dashboard/points/points_calculator.html", {
                "error": "الرجاء إدخال رقم أسبوع صحيح (بين 1 و 52)",
                "template_message": request.POST.get("template_message", ""),
                "combined_messages": combined_messages
            })

        # هنا تحتاج لمكتبة parse_report_text من main app
        # يمكنك نسخها أو استيرادها

        try:
            # مؤقتاً - يمكنك إضافة المنطق هنا لاحقاً
            summary = {'rankings': [], 'total_students': 0, 'total_points': 0}

            return render(request, "director_dashboard/points/points_result.html", {
                "summary": summary,
                "week_number": week_number,
                "is_saved": False
            })

        except Exception as e:
            return render(request, "director_dashboard/points/points_calculator.html", {
                "error": f"حدث خطأ: {str(e)}",
                "template_message": request.POST.get("template_message", ""),
                "combined_messages": combined_messages
            })

    return redirect("points_calculator")


@login_required(login_url="/accounts/login/")
def points_settings(request):
    """واجهة تخصيص إعدادات حاسبة النقاط"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    try:
        settings_obj = PointsCalculatorSettings.objects.get(user=request.user)
    except PointsCalculatorSettings.DoesNotExist:
        default_settings = PointsCalculatorSettings.get_default_settings()
        settings_obj = PointsCalculatorSettings.objects.create(
            user=request.user,
            program_name=default_settings['program_name'],
            committees=default_settings['committees'],
            batches=[],
            default_committee_name=default_settings['default_committee_name'],
            current_week=default_settings.get('current_week', 1)
        )

    if request.method == "POST":
        settings_obj.program_name = request.POST.get("program_name", "")
        settings_obj.default_committee_name = request.POST.get("default_committee_name", "")

        try:
            settings_obj.current_week = int(request.POST.get("current_week", 1))
        except:
            settings_obj.current_week = 1

        batches = []
        batch_names = request.POST.getlist("batch_name")
        batch_counts = request.POST.getlist("batch_student_count")
        batch_emojis = request.POST.getlist("batch_emoji")
        batch_students = request.POST.getlist("batch_students")

        for i in range(len(batch_names)):
            if batch_names[i].strip():
                try:
                    count = int(batch_counts[i]) if batch_counts[i] else 0
                except:
                    count = 0

                students_text = batch_students[i] if i < len(batch_students) else ""
                students_list = []
                if students_text.strip():
                    for line in students_text.strip().split('\n'):
                        for name in line.split(','):
                            name = name.strip()
                            if name:
                                students_list.append(name)

                batches.append({
                    'name': batch_names[i].strip(),
                    'student_count': count,
                    'emoji': batch_emojis[i] if i < len(batch_emojis) else '👨‍🎓',
                    'students': students_list
                })

        settings_obj.batches = batches
        settings_obj.save()

        UserActivity.objects.create(
            user=request.user,
            action='تحديث إعدادات حاسبة النقاط',
            ip_address=get_client_ip(request)
        )

        return render(request, "director_dashboard/points/points_settings.html", {
            "settings": settings_obj,
            "success_message": "تم حفظ الإعدادات بنجاح ✅"
        })

    if not settings_obj.batches:
        default_settings = PointsCalculatorSettings.get_default_settings()
        display_settings = {
            'program_name': settings_obj.program_name,
            'committees': settings_obj.committees if settings_obj.committees else default_settings['committees'],
            'batches': default_settings['batches'],
            'default_committee_name': settings_obj.default_committee_name,
            'current_week': settings_obj.current_week
        }
    else:
        display_settings = {
            'program_name': settings_obj.program_name,
            'committees': settings_obj.committees if settings_obj.committees else [],
            'batches': settings_obj.batches,
            'default_committee_name': settings_obj.default_committee_name,
            'current_week': settings_obj.current_week
        }

    return render(request, "director_dashboard/points/points_settings.html", {
        "settings": display_settings
    })


@login_required(login_url="/accounts/login/")
def points_history(request):
    """عرض نقاط الطلاب السابقة"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    all_results = PointsResult.objects.filter(
        user=request.user
    ).exclude(program_name="نقاط الإسري").order_by('-created_at')

    weeks_data = {}
    for result in all_results:
        week = result.week_number or 'غير محدد'
        if week not in weeks_data:
            weeks_data[week] = result

    dashboard_stats = {
        'total_weeks': len(weeks_data),
        'total_points_all_weeks': 0,
        'unique_students_count': 0,
        'average_points_per_week': 0,
        'students_summary': {}
    }

    for result in all_results:
        summary = result.summary_data
        if summary and summary.get('total_points'):
            dashboard_stats['total_points_all_weeks'] += summary.get('total_points', 0)

        if summary and summary.get('rankings'):
            for student in summary['rankings']:
                student_name = student.get('student_name', '')
                student_points = student.get('total_points', 0)

                if student_name:
                    if student_name not in dashboard_stats['students_summary']:
                        dashboard_stats['students_summary'][student_name] = 0
                    dashboard_stats['students_summary'][student_name] += student_points

    dashboard_stats['unique_students_count'] = len(dashboard_stats['students_summary'])

    if dashboard_stats['total_weeks'] > 0:
        dashboard_stats['average_points_per_week'] = round(
            dashboard_stats['total_points_all_weeks'] / dashboard_stats['total_weeks'],
            2
        )

    return render(request, "director_dashboard/points/points_history.html", {
        "weeks_data": weeks_data,
        "results": all_results,
        "dashboard_stats": dashboard_stats
    })


from django.http import JsonResponse
from datetime import timedelta
from django.utils import timezone


@login_required(login_url="/accounts/login/")
def points_family_calculator(request):
    """حساب نقاط الإسري - واجهة بسيطة لإضافة/خصم النقاط مباشرة"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    # جلب النتائج المحفوظة لنقاط الإسري
    saved_results = PointsResult.objects.filter(
        user=request.user,
        program_name="نقاط الإسري"
    ).order_by('-created_at')

    latest_result = saved_results.first() if saved_results.exists() else None

    return render(request, "director_dashboard/points/points_family_calculator.html", {
        "saved_results": saved_results,
        "latest_result": latest_result
    })


@login_required(login_url="/accounts/login/")
def load_family_result(request, result_id):
    """تحميل نتيجة محفوظة لنقاط الإسري للتعديل"""
    if request.user.role != 'director':
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)

    try:
        result = PointsResult.objects.get(id=result_id, user=request.user, program_name="نقاط الإسري")

        summary = result.summary_data
        rankings = summary.get('rankings', [])

        families_data = []
        for rank_item in rankings:
            families_data.append({
                'name': rank_item.get('student_name', ''),
                'points': rank_item.get('total_points', 0)
            })

        return JsonResponse({
            'success': True,
            'families': families_data,
            'week_number': result.week_number,
            'result_id': str(result.id)
        })

    except PointsResult.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'النتيجة غير موجودة'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'حدث خطأ: {str(e)}'}, status=500)


@login_required(login_url="/accounts/login/")
def save_family_result(request):
    """حفظ نتائج نقاط الإسري"""
    if request.user.role != 'director':
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)

    if request.method == "POST":
        try:
            import json
            summary_data = json.loads(request.POST.get("summary_data", "{}"))
            week_number_str = request.POST.get("week_number", "").strip()
            program_name = request.POST.get("program_name", "نقاط الإسري")
            result_id = request.POST.get("result_id", "").strip()

            week_number = None
            if week_number_str:
                week_number = normalize_week_number(week_number_str)

            if not summary_data or not summary_data.get('rankings'):
                return JsonResponse({'success': False, 'error': 'لا توجد بيانات لحفظها'}, status=400)

            # إذا كان هناك result_id، قم بتحديث النتيجة الموجودة
            if result_id:
                try:
                    existing_result = PointsResult.objects.get(id=result_id, user=request.user,
                                                               program_name=program_name)
                    existing_result.summary_data = summary_data
                    if week_number:
                        existing_result.week_number = week_number
                    existing_result.expires_at = timezone.now() + timedelta(days=30)
                    existing_result.save()

                    from django.urls import reverse
                    return JsonResponse({
                        'success': True,
                        'message': 'تم تحديث النتائج بنجاح',
                        'result_id': str(existing_result.id),
                        'redirect_url': reverse('points_result_detail', args=[str(existing_result.id)])
                    })
                except PointsResult.DoesNotExist:
                    pass

            # إذا كان هناك week_number، تحقق من وجود نتيجة لنفس الأسبوع
            if week_number:
                existing_result = PointsResult.objects.filter(
                    user=request.user,
                    week_number=week_number,
                    program_name=program_name
                ).first()

                if existing_result:
                    existing_result.summary_data = summary_data
                    existing_result.expires_at = timezone.now() + timedelta(days=30)
                    existing_result.save()

                    from django.urls import reverse
                    return JsonResponse({
                        'success': True,
                        'message': 'تم تحديث النتائج بنجاح',
                        'result_id': str(existing_result.id),
                        'redirect_url': reverse('points_result_detail', args=[str(existing_result.id)])
                    })

            # إنشاء نتيجة جديدة
            points_result = PointsResult.objects.create(
                user=request.user,
                summary_data=summary_data,
                week_number=week_number,
                program_name=program_name,
                expires_at=timezone.now() + timedelta(days=30)
            )

            from django.urls import reverse
            return JsonResponse({
                'success': True,
                'message': 'تم حفظ النتائج بنجاح',
                'result_id': str(points_result.id),
                'redirect_url': reverse('points_result_detail', args=[str(points_result.id)])
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': f'حدث خطأ: {str(e)}'}, status=500)

    return JsonResponse({'success': False, 'error': 'طريقة الطلب غير صحيحة'}, status=405)


@login_required(login_url="/accounts/login/")
def save_points_result(request):
    """حفظ النتيجة بعد موافقة المستخدم"""
    if request.user.role != 'director':
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)

    if request.method == "POST":
        save_choice = request.POST.get("save_choice", "").strip()

        if not save_choice or save_choice not in ['yes', 'no']:
            return JsonResponse({'success': False, 'error': 'يرجى اختيار خيار الحفظ'}, status=400)

        if save_choice == 'no':
            if 'pending_points_result' in request.session:
                del request.session['pending_points_result']
            return JsonResponse({'success': True, 'saved': False, 'message': 'لم يتم حفظ النتيجة'})

        if save_choice == 'yes':
            if 'pending_points_result' not in request.session:
                return JsonResponse({'success': False, 'error': 'لا توجد بيانات لحفظها'}, status=400)

            pending_data = request.session['pending_points_result']
            week_number = pending_data.get('week_number')

            if week_number:
                existing_result = PointsResult.objects.filter(
                    user=request.user,
                    week_number=week_number
                ).first()

                if existing_result:
                    existing_result.summary_data = pending_data['summary_data']
                    existing_result.program_name = pending_data['program_name']
                    existing_result.expires_at = timezone.now() + timedelta(days=30)
                    existing_result.save()
                    del request.session['pending_points_result']

                    from django.urls import reverse
                    return JsonResponse({
                        'success': True,
                        'saved': True,
                        'message': 'تم تحديث النتيجة بنجاح',
                        'redirect_url': reverse('points_result_detail', args=[str(existing_result.id)])
                    })

            points_result = PointsResult.objects.create(
                user=request.user,
                summary_data=pending_data['summary_data'],
                week_number=pending_data.get('week_number'),
                program_name=pending_data.get('program_name', 'عشائر آل سلطان'),
                expires_at=timezone.now() + timedelta(days=30)
            )

            del request.session['pending_points_result']

            from django.urls import reverse
            return JsonResponse({
                'success': True,
                'saved': True,
                'message': 'تم حفظ النتيجة بنجاح',
                'redirect_url': reverse('points_result_detail', args=[str(points_result.id)])
            })

    return JsonResponse({'success': False, 'error': 'طريقة الطلب غير صحيحة'}, status=405)


@login_required(login_url="/accounts/login/")
def points_result_detail(request, result_id):
    """عرض نتيجة محفوظة من قاعدة البيانات"""
    if request.user.role != 'director':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('dashboard')

    try:
        result = PointsResult.objects.get(id=result_id, user=request.user)

        summary = result.summary_data
        user_settings = get_user_settings(request.user)
        program_name = result.program_name or user_settings.get('program_name', 'عشائر آل سلطان')

        is_family_points = program_name == "نقاط الإسري"

        return render(request, "director_dashboard/points/points_result.html", {
            "summary": summary,
            "week_number": result.week_number,
            "result_id": str(result.id),
            "is_saved": True,
            "is_family_points": is_family_points,
            "share_url": request.build_absolute_uri(f'/points/share/{result.share_url}/')
        })

    except PointsResult.DoesNotExist:
        messages.error(request, 'النتيجة غير موجودة')
        return redirect("points_history")


@login_required(login_url="/accounts/login/")
def delete_points_result(request, result_id):
    """حذف نتيجة محفوظة"""
    if request.user.role != 'director':
        return JsonResponse({'success': False, 'error': 'غير مصرح'}, status=403)

    if request.method == "POST":
        try:
            result = PointsResult.objects.get(id=result_id, user=request.user)
            result.delete()

            UserActivity.objects.create(
                user=request.user,
                action=f'حذف نتيجة نقاط: الأسبوع {result.week_number or "غير محدد"}',
                ip_address=get_client_ip(request)
            )

            return JsonResponse({'success': True, 'message': 'تم حذف النتيجة بنجاح'})
        except PointsResult.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'النتيجة غير موجودة'}, status=404)

    return JsonResponse({'success': False, 'error': 'طريقة الطلب غير صحيحة'}, status=405)