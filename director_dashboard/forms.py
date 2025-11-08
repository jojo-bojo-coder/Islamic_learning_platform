from django import forms
from .models import Program
from accounts.models import User


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ['name', 'description', 'manager', 'start_date', 'end_date', 'target_students']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'manager': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'target_students': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'اسم البرنامج',
            'description': 'الوصف',
            'manager': 'مدير البرنامج',
            'start_date': 'تاريخ البدء',
            'end_date': 'تاريخ الانتهاء',
            'target_students': 'الهدف من عدد الطلاب',
        }


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='كلمة المرور'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
            'phone': 'رقم الهاتف',
            'role': 'الدور',
        }


from django import forms
from .models import DirectorAlbum, AlbumPhoto, DirectorFileLibrary, DirectorAlert

class DirectorAlbumForm(forms.ModelForm):
    class Meta:
        model = DirectorAlbum
        fields = ['title', 'description', 'cover_image', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان الألبوم'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف الألبوم',
                'rows': 4
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'عنوان الألبوم',
            'description': 'الوصف',
            'cover_image': 'صورة الغلاف',
            'is_active': 'نشط',
        }


class AlbumPhotoForm(forms.ModelForm):
    class Meta:
        model = AlbumPhoto
        fields = ['title', 'image', 'description', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان الصورة'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف الصورة',
                'rows': 3
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
        }
        labels = {
            'title': 'عنوان الصورة',
            'image': 'الصورة',
            'description': 'الوصف',
            'order': 'ترتيب',
        }


class DirectorFileLibraryForm(forms.ModelForm):
    class Meta:
        model = DirectorFileLibrary
        fields = ['title', 'description', 'file_type', 'file', 'thumbnail', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان الملف'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل وصف الملف',
                'rows': 4
            }),
            'file_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'thumbnail': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'title': 'العنوان',
            'description': 'الوصف',
            'file_type': 'نوع الملف',
            'file': 'الملف',
            'thumbnail': 'صورة مصغرة',
            'is_public': 'عام',
        }


class DirectorAlertForm(forms.ModelForm):
    class Meta:
        model = DirectorAlert
        fields = ['title', 'message', 'alert_type', 'priority', 'related_user',
                 'related_program', 'related_committee', 'action_url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل عنوان التنبيه'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل رسالة التنبيه',
                'rows': 5
            }),
            'alert_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select'
            }),
            'related_user': forms.Select(attrs={
                'class': 'form-select'
            }),
            'related_program': forms.Select(attrs={
                'class': 'form-select'
            }),
            'related_committee': forms.Select(attrs={
                'class': 'form-select'
            }),
            'action_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل رابط الإجراء'
            }),
        }
        labels = {
            'title': 'العنوان',
            'message': 'الرسالة',
            'alert_type': 'نوع التنبيه',
            'priority': 'الأولوية',
            'related_user': 'المستخدم المرتبط',
            'related_program': 'البرنامج المرتبط',
            'related_committee': 'اللجنة المرتبطة',
            'action_url': 'رابط الإجراء',
        }


from django import forms
from .models import User


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور',
            'id': 'id_password'
        }),
        min_length=8
    )
    confirm_password = forms.CharField(
        label='تأكيد كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أعد إدخال كلمة المرور',
            'id': 'id_confirm_password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم المستخدم'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'أدخل البريد الإلكتروني'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل الاسم الأول'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم العائلة'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل رقم الهاتف'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
            'phone': 'رقم الهاتف',
            'role': 'الدور',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('كلمات المرور غير متطابقة')

        return cleaned_data

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('اسم المستخدم موجود مسبقاً')
        return username


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم المستخدم'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'أدخل البريد الإلكتروني'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل الاسم الأول'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل اسم العائلة'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'أدخل رقم الهاتف'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_is_active'}),
        }
        labels = {
            'username': 'اسم المستخدم',
            'email': 'البريد الإلكتروني',
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
            'phone': 'رقم الهاتف',
            'role': 'الدور',
            'is_active': 'الحساب نشط',
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('اسم المستخدم موجود مسبقاً')
        return username