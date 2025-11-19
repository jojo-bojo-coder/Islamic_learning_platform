from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, UserActivity
from .forms import LoginForm, RegisterForm

def login_view(request):
    print(f"=== LOGIN VIEW STARTED ===")
    print(f"Request method: {request.method}")

    if request.method == 'POST':
        print("POST request detected")
        form = LoginForm(request.POST)
        print(f"Form created with POST data: {request.POST}")

        if form.is_valid():
            print("Form is valid")
            username_or_email = form.cleaned_data['username_or_email']  # Updated field name
            password = form.cleaned_data['password']
            print(f"Attempting authentication for: {username_or_email}")

            # Try to authenticate with both username and email
            user = None

            # First, try to authenticate directly (will work for username)
            user = authenticate(request, username=username_or_email, password=password)
            print(f"Direct authentication result: {user}")

            # If direct authentication failed, try with email
            if user is None:
                print("Direct authentication failed, trying with email...")
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    print(f"User found by email: {user_obj.username}")
                    user = authenticate(request, username=user_obj.username, password=password)
                    print(f"Email authentication result: {user}")
                except User.DoesNotExist:
                    user = None
                    print("No user found with this email or username")

            print(f"Final authentication result - User: {user}")

            if user is not None:
                print(
                    f"User authenticated successfully: {user.username}, Role: {getattr(user, 'role', 'No role attribute')}")
                login(request, user)
                print("User logged in successfully")

                # Log user activity
                try:
                    ip_address = get_client_ip(request)
                    print(f"IP Address: {ip_address}")
                    UserActivity.objects.create(
                        user=user,
                        action='تسجيل الدخول',
                        ip_address=ip_address
                    )
                    print("User activity logged successfully")
                except Exception as e:
                    print(f"Error logging user activity: {e}")

                messages.success(request, 'تم تسجيل الدخول بنجاح!')
                print("Success message added")

                # Redirect based on user role
                print(f"Checking user role: {user.role}")
                if user.role == 'program_manager':
                    print("Redirecting to program manager dashboard")
                    return redirect('pm_dashboard')
                else:
                    print("Redirecting to regular dashboard")
                    return redirect('home')
            else:
                print("Authentication failed - user is None")
                messages.error(request, 'اسم المستخدم/البريد الإلكتروني أو كلمة المرور غير صحيحة')
                print("Error message added")
        else:
            print("Form is invalid")
            print(f"Form errors: {form.errors}")
    else:
        print("GET request detected - creating empty form")
        form = LoginForm()

    print("Rendering login template")
    return render(request, 'accounts/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])  # تم التصحيح هنا
            user.save()

            UserActivity.objects.create(
                user=user,
                action='إنشاء حساب جديد',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.')
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        UserActivity.objects.create(
            user=request.user,
            action='تسجيل الخروج',
            ip_address=get_client_ip(request)
        )
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح!')
    return redirect('home')


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from .models import User, UserActivity, PasswordResetToken
from .forms import CustomPasswordResetForm, CustomSetPasswordForm


def password_reset_request(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            reset_token = form.save()

            if reset_token:
                # Send email
                subject = 'إعادة تعيين كلمة المرور - منصة التحفيظ'
                reset_url = request.build_absolute_uri(
                    f'/accounts/password-reset-confirm/{reset_token.token}/'
                )

                context = {
                    'user': reset_token.user,
                    'reset_url': reset_url,
                    'expires_hours': 24
                }

                html_message = render_to_string('accounts/password_reset_email.html', context)
                plain_message = strip_tags(html_message)

                try:
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[reset_token.user.email],
                        html_message=html_message,
                        fail_silently=False,
                    )

                    messages.success(
                        request,
                        'تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني. '
                        'يرجى التحقق من صندوق الوارد.'
                    )

                    # Log activity
                    if request.user.is_authenticated:
                        UserActivity.objects.create(
                            user=request.user,
                            action='طلب إعادة تعيين كلمة المرور',
                            ip_address=get_client_ip(request)
                        )

                except Exception as e:
                    messages.error(
                        request,
                        'حدث خطأ أثناء إرسال البريد الإلكتروني. يرجى المحاولة مرة أخرى.'
                    )
            else:
                messages.error(
                    request,
                    'لا يوجد حساب مرتبط بهذا البريد الإلكتروني.'
                )

            return redirect('password_reset_request')
    else:
        form = CustomPasswordResetForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(token=token)

        if not reset_token.is_valid():
            messages.error(request, 'رابط إعادة التعيين غير صالح أو منتهي الصلاحية.')
            return redirect('password_reset_request')

        if request.method == 'POST':
            form = CustomSetPasswordForm(reset_token.user, request.POST)
            if form.is_valid():
                form.save()

                # Mark token as used
                reset_token.is_used = True
                reset_token.save()

                # Log activity
                UserActivity.objects.create(
                    user=reset_token.user,
                    action='إعادة تعيين كلمة المرور',
                    ip_address=get_client_ip(request)
                )

                messages.success(request, 'تم إعادة تعيين كلمة المرور بنجاح. يمكنك الآن تسجيل الدخول.')
                return redirect('login')
        else:
            form = CustomSetPasswordForm(reset_token.user)

        return render(request, 'accounts/password_reset_confirm.html', {
            'form': form,
            'token': token
        })

    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'رابط إعادة التعيين غير صالح.')
        return redirect('password_reset_request')


@login_required
def password_change(request):
    if request.method == 'POST':
        form = CustomSetPasswordForm(request.user, request.POST)
        if form.is_valid():
            form.save()

            # Update session auth hash
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, form.user)

            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='تغيير كلمة المرور',
                ip_address=get_client_ip(request)
            )

            messages.success(request, 'تم تغيير كلمة المرور بنجاح.')
            return redirect('dashboard')
    else:
        form = CustomSetPasswordForm(request.user)

    return render(request, 'accounts/password_change.html', {'form': form})
