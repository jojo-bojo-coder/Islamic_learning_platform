from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم المستخدم'})
    )
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'أدخل كلمة المرور'})
    )


class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2']
        labels = {
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
            'phone': 'رقم الهاتف',
            'role': 'الدور',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from .models import User, PasswordResetToken
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل بريدك الإلكتروني',
            'autocomplete': 'email'
        })
    )

    def save(self, domain_override=None, **kwargs):
        email = self.cleaned_data["email"]
        try:
            user = User.objects.get(email=email)
            # Create reset token
            token = get_random_string(50)
            expires_at = timezone.now() + timedelta(hours=24)

            # Delete any existing tokens for this user
            PasswordResetToken.objects.filter(user=user).delete()

            # Create new token
            reset_token = PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )

            return reset_token
        except User.DoesNotExist:
            return None


class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="كلمة المرور الجديدة",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور الجديدة',
            'autocomplete': 'new-password'
        }),
    )
    new_password2 = forms.CharField(
        label="تأكيد كلمة المرور الجديدة",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أكد كلمة المرور الجديدة',
            'autocomplete': 'new-password'
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].help_text = ''