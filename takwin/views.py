from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Takwin, UserTakwin
from django.http import FileResponse, Http404
from accounts.models import UserActivity  # استخدام UserActivity من accounts
import os
import mimetypes


def get_client_ip(request):
    """دالة مساعدة للحصول على IP"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@login_required(login_url="/accounts/login/")
def takwin(request):
    user = request.user
    def calc_percentage(done, total):
        return round((done / total) * 100) if total > 0 else 0

    num_tarbawiu = Takwin.objects.filter(aspect='tarbawiu').order_by('-created_at').count()
    num_done_tarbawiu = UserTakwin.objects.filter(user=request.user, takwin__aspect='tarbawiu', is_done=True).count()
    progress_tarbawiu = calc_percentage(num_done_tarbawiu, num_tarbawiu)

    num_shareiu = Takwin.objects.filter(aspect='shareiu').order_by('-created_at').count()
    num_done_shareiu = UserTakwin.objects.filter(user=request.user, takwin__aspect='shareiu', is_done=True).count()
    progress_shareiu = calc_percentage(num_done_shareiu, num_shareiu)

    num_mhari = Takwin.objects.filter(aspect='mhari').order_by('-created_at').count()
    num_done_mhari = UserTakwin.objects.filter(user=request.user, takwin__aspect='mhari', is_done=True).count()
    progress_mhari = calc_percentage(num_done_mhari, num_mhari)

    num_medad = Takwin.objects.filter(aspect='medad').order_by('-created_at').count()
    num_done_medad = UserTakwin.objects.filter(user=request.user, takwin__aspect='medad', is_done=True).count()
    progress_medad = calc_percentage(num_done_medad, num_medad)

    num_takwins = num_tarbawiu + num_shareiu + num_mhari + num_medad
    num_done_takwins = num_done_tarbawiu + num_done_shareiu + num_done_mhari + num_done_medad
    progress_takwins = calc_percentage(num_done_takwins, num_takwins)

    if user.role == 'director':
        base_template = 'director_base.html'
    elif user.role == 'program_manager':
        base_template = 'program_manager_base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'cultural':
        base_template = 'cultural_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sports':
        base_template = 'sports_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sharia':
        base_template = 'sharia_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'operations':
        base_template = 'operations_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'scientific':
        base_template = 'scientific_committee/base.html'
    else:
        base_template = 'base.html'

    return render(request, 'takwin/takwin.html', {
        "num_takwins": num_takwins, "num_done_takwins": num_done_takwins, "progress_takwins": progress_takwins,
        "num_tarbawiu": num_tarbawiu, "num_done_tarbawiu": num_done_tarbawiu, "progress_tarbawiu": progress_tarbawiu,
        "num_shareiu": num_shareiu, "num_done_shareiu": num_done_shareiu, "progress_shareiu": progress_shareiu,
        "num_mhari": num_mhari, "num_done_mhari": num_done_mhari, "progress_mhari": progress_mhari,
        "num_medad": num_medad, "num_done_medad": num_done_medad, "progress_medad": progress_medad,'base_template': base_template,
    })


@login_required(login_url="/accounts/login/")
def tarbawiu(request):
    user = request.user
    takwin_list = Takwin.objects.filter(aspect='tarbawiu').order_by('-created_at')

    for t in takwin_list:
        user_takwin = UserTakwin.objects.filter(user=request.user, takwin=t).first()
        t.is_done = user_takwin.is_done if user_takwin else False

    if user.role == 'director':
        base_template = 'director_base.html'
    elif user.role == 'program_manager':
        base_template = 'program_manager_base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'cultural':
        base_template = 'cultural_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sports':
        base_template = 'sports_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sharia':
        base_template = 'sharia_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'operations':
        base_template = 'operations_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'scientific':
        base_template = 'scientific_committee/base.html'
    else:
        base_template = 'base.html'

    return render(request, 'takwin/tarbawiu.html', {
        'takwin_list': takwin_list,
        'base_template': base_template,
    })


@login_required(login_url="/accounts/login/")
def shareiu(request):
    user = request.user
    takwin_list = Takwin.objects.filter(aspect='shareiu').order_by('-created_at')

    for t in takwin_list:
        user_takwin = UserTakwin.objects.filter(user=request.user, takwin=t).first()
        t.is_done = user_takwin.is_done if user_takwin else False

    if user.role == 'director':
        base_template = 'director_base.html'
    elif user.role == 'program_manager':
        base_template = 'program_manager_base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'cultural':
        base_template = 'cultural_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sports':
        base_template = 'sports_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sharia':
        base_template = 'sharia_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'operations':
        base_template = 'operations_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'scientific':
        base_template = 'scientific_committee/base.html'
    else:
        base_template = 'base.html'

    return render(request, 'takwin/shareiu.html', {
        'takwin_list': takwin_list,
        'base_template': base_template,
    })


@login_required(login_url="/accounts/login/")
def mhari(request):
    user = request.user
    takwin_list = Takwin.objects.filter(aspect='mhari').order_by('-created_at')

    for t in takwin_list:
        user_takwin = UserTakwin.objects.filter(user=request.user, takwin=t).first()
        t.is_done = user_takwin.is_done if user_takwin else False

    if user.role == 'director':
        base_template = 'director_base.html'
    elif user.role == 'program_manager':
        base_template = 'program_manager_base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'cultural':
        base_template = 'cultural_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sports':
        base_template = 'sports_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sharia':
        base_template = 'sharia_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'operations':
        base_template = 'operations_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'scientific':
        base_template = 'scientific_committee/base.html'
    else:
        base_template = 'base.html'

    return render(request, 'takwin/mhari.html', {
        'takwin_list': takwin_list,
        'base_template': base_template,
    })


@login_required(login_url="/accounts/login/")
def medad(request):
    user = request.user
    takwin_list = Takwin.objects.filter(aspect='medad').order_by('-created_at')

    for t in takwin_list:
        user_takwin = UserTakwin.objects.filter(user=request.user, takwin=t).first()
        t.is_done = user_takwin.is_done if user_takwin else False

    if user.role == 'director':
        base_template = 'director_base.html'
    elif user.role == 'program_manager':
        base_template = 'program_manager_base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'cultural':
        base_template = 'cultural_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sports':
        base_template = 'sports_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'sharia':
        base_template = 'sharia_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'operations':
        base_template = 'operations_committee/base.html'
    elif user.role == 'committee_supervisor' and user.supervisor_type == 'scientific':
        base_template = 'scientific_committee/base.html'
    else:
        base_template = 'base.html'

    return render(request, 'takwin/medad.html', {
        'takwin_list': takwin_list,
        'base_template': base_template,
    })


@login_required(login_url="/accounts/login/")
def toggle_takwin(request, takwin_id):
    takwin = get_object_or_404(Takwin, id=takwin_id)

    user_takwin, created = UserTakwin.objects.get_or_create(
        user=request.user,
        takwin=takwin,
        defaults={'is_done': True}
    )

    if not created:
        # لو كان موجود، غير الحالة
        user_takwin.is_done = not user_takwin.is_done
        user_takwin.save()

    # تسجيل النشاط
    action = 'تعليم تكوين كمنجز' if user_takwin.is_done else 'إلغاء إنجاز تكوين'
    UserActivity.objects.create(
        user=request.user,
        action=f'{action}: {takwin.title}',
        ip_address=get_client_ip(request)
    )

    # رجّع المستخدم للصفحة السابقة أو للصفحة الرئيسية إذا لم يكن هناك Referer
    return redirect(request.META.get('HTTP_REFERER', 'takwin'))


@login_required(login_url="/accounts/login/")
def pdf_view_takwin(request, takwin_id):
    takwin = get_object_or_404(Takwin, id=takwin_id)
    return render(request, 'takwin/documents/pdf_view_takwin.html', {'takwin': takwin})


@login_required(login_url="/accounts/login/")
def pdf_file_view_takwin(request, takwin_id):
    """خدمة الملف مباشرة - يدعم جميع أنواع الملفات"""
    takwin = get_object_or_404(Takwin, id=takwin_id)
    if not takwin.pdf:
        raise Http404("File not found")

    try:
        file_path = takwin.pdf.path
        if os.path.exists(file_path):
            # اكتشاف نوع الملف من الامتداد
            file_extension = os.path.splitext(file_path)[1].lower()

            # تحديد content_type بناءً على نوع الملف
            content_type_map = {
                '.pdf': 'application/pdf',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.txt': 'text/plain',
                '.zip': 'application/zip',
                '.rar': 'application/x-rar-compressed',
            }

            content_type = content_type_map.get(file_extension)

            # إذا لم نجد نوع محدد، استخدم mimetypes
            if not content_type:
                content_type, _ = mimetypes.guess_type(file_path)
                if not content_type:
                    content_type = 'application/octet-stream'

            response = FileResponse(
                open(file_path, 'rb'),
                content_type=content_type
            )
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
            response['X-Content-Type-Options'] = 'nosniff'
            response['Access-Control-Allow-Origin'] = '*'

            # تسجيل النشاط
            UserActivity.objects.create(
                user=request.user,
                action=f'عرض ملف: {takwin.title}',
                ip_address=get_client_ip(request)
            )

            return response
        else:
            raise Http404("File not found on disk")
    except Exception as e:
        raise Http404(f"Error loading file: {str(e)}")


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Takwin, UserTakwin
from .forms import TakwinForm
from django.http import FileResponse, Http404
from accounts.models import UserActivity
import os
import mimetypes


def is_program_manager(user):
    return user.is_authenticated and hasattr(user, 'role') and user.role == 'program_manager'



@login_required(login_url="/accounts/login/")
@user_passes_test(is_program_manager)
def takwin_management(request):
    """لوحة تحكم إدارة التكوينات"""
    takwins = Takwin.objects.all().order_by('-created_at')

    # إحصائيات
    stats = {
        'total': takwins.count(),
        'tarbawiu': takwins.filter(aspect='tarbawiu').count(),
        'shareiu': takwins.filter(aspect='shareiu').count(),
        'mhari': takwins.filter(aspect='mhari').count(),
        'medad': takwins.filter(aspect='medad').count(),
    }

    return render(request, 'takwin/management/dashboard.html', {
        'takwins': takwins,
        'stats': stats,
    })


@login_required(login_url="/accounts/login/")
@user_passes_test(is_program_manager)
def add_takwin(request):
    """إضافة تكوين جديد"""
    if request.method == 'POST':
        form = TakwinForm(request.POST, request.FILES)
        if form.is_valid():
            takwin = form.save()

            # تسجيل النشاط
            UserActivity.objects.create(
                user=request.user,
                action=f'إضافة تكوين جديد: {takwin.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إضافة التكوين بنجاح!')
            return redirect('takwin_management')
    else:
        form = TakwinForm()

    return render(request, 'takwin/management/add_takwin.html', {'form': form})


@login_required(login_url="/accounts/login/")
@user_passes_test(is_program_manager)
def edit_takwin(request, takwin_id):
    """تعديل تكوين موجود"""
    takwin = get_object_or_404(Takwin, id=takwin_id)

    if request.method == 'POST':
        form = TakwinForm(request.POST, request.FILES, instance=takwin)
        if form.is_valid():
            updated_takwin = form.save()

            # تسجيل النشاط
            UserActivity.objects.create(
                user=request.user,
                action=f'تعديل تكوين: {updated_takwin.title}',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تحديث التكوين بنجاح!')
            return redirect('takwin_management')
    else:
        form = TakwinForm(instance=takwin)

    return render(request, 'takwin/management/edit_takwin.html', {
        'form': form,
        'takwin': takwin
    })


@login_required(login_url="/accounts/login/")
@user_passes_test(is_program_manager)
def delete_takwin(request, takwin_id):
    """حذف تكوين"""
    takwin = get_object_or_404(Takwin, id=takwin_id)

    if request.method == 'POST':
        title = takwin.title

        # حذف الملفات المرتبطة إذا كانت موجودة
        if takwin.image and os.path.exists(takwin.image.path):
            os.remove(takwin.image.path)
        if takwin.pdf and os.path.exists(takwin.pdf.path):
            os.remove(takwin.pdf.path)

        takwin.delete()

        # تسجيل النشاط
        UserActivity.objects.create(
            user=request.user,
            action=f'حذف تكوين: {title}',
            ip_address=get_client_ip(request)
        )

        messages.success(request, 'تم حذف التكوين بنجاح!')
        return redirect('takwin_management')

    return render(request, 'takwin/management/delete_takwin.html', {'takwin': takwin})
