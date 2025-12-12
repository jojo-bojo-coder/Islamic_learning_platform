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

    return render(request, 'takwin/takwin.html', {
        "num_takwins": num_takwins, "num_done_takwins": num_done_takwins, "progress_takwins": progress_takwins,
        "num_tarbawiu": num_tarbawiu, "num_done_tarbawiu": num_done_tarbawiu, "progress_tarbawiu": progress_tarbawiu,
        "num_shareiu": num_shareiu, "num_done_shareiu": num_done_shareiu, "progress_shareiu": progress_shareiu,
        "num_mhari": num_mhari, "num_done_mhari": num_done_mhari, "progress_mhari": progress_mhari,
        "num_medad": num_medad, "num_done_medad": num_done_medad, "progress_medad": progress_medad,
    })


@login_required(login_url="/accounts/login/")
def tarbawiu(request):
    takwin_list = Takwin.objects.filter(aspect='tarbawiu').order_by('-created_at')

    for t in takwin_list:
        user_takwin = UserTakwin.objects.filter(user=request.user, takwin=t).first()
        t.is_done = user_takwin.is_done if user_takwin else False

    return render(request, 'takwin/tarbawiu.html', {
        'takwin_list': takwin_list,
    })


@login_required(login_url="/accounts/login/")
def shareiu(request):
    takwin_list = Takwin.objects.filter(aspect='shareiu').order_by('-created_at')

    for t in takwin_list:
        user_takwin = UserTakwin.objects.filter(user=request.user, takwin=t).first()
        t.is_done = user_takwin.is_done if user_takwin else False

    return render(request, 'takwin/shareiu.html', {
        'takwin_list': takwin_list,
    })


@login_required(login_url="/accounts/login/")
def mhari(request):
    takwin_list = Takwin.objects.filter(aspect='mhari').order_by('-created_at')

    for t in takwin_list:
        user_takwin = UserTakwin.objects.filter(user=request.user, takwin=t).first()
        t.is_done = user_takwin.is_done if user_takwin else False

    return render(request, 'takwin/mhari.html', {
        'takwin_list': takwin_list,
    })


@login_required(login_url="/accounts/login/")
def medad(request):
    takwin_list = Takwin.objects.filter(aspect='medad').order_by('-created_at')

    for t in takwin_list:
        user_takwin = UserTakwin.objects.filter(user=request.user, takwin=t).first()
        t.is_done = user_takwin.is_done if user_takwin else False

    return render(request, 'takwin/medad.html', {
        'takwin_list': takwin_list,
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
