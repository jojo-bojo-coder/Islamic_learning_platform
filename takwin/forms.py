from django import forms
from .models import Takwin


class TakwinForm(forms.ModelForm):
    class Meta:
        model = Takwin
        fields = ['aspect', 'title', 'description', 'image', 'link', 'pdf']
        widgets = {
            'aspect': forms.Select(attrs={
                'class': 'form-control',
                'style': 'padding: 12px; border-radius: 8px; border: 2px solid #e8e8e8; width: 100%;'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'style': 'padding: 12px; border-radius: 8px; border: 2px solid #e8e8e8; width: 100%;',
                'placeholder': 'أدخل عنوان التكوين'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'style': 'padding: 12px; border-radius: 8px; border: 2px solid #e8e8e8; width: 100%; height: 150px;',
                'placeholder': 'أدخل وصف التكوين',
                'rows': 5
            }),
            'link': forms.URLInput(attrs={
                'class': 'form-control',
                'style': 'padding: 12px; border-radius: 8px; border: 2px solid #e8e8e8; width: 100%;',
                'placeholder': 'أدخل رابط YouTube (اختياري)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control-file',
                'style': 'padding: 10px; border-radius: 8px; border: 2px dashed #e8e8e8; width: 100%;',
                'accept': 'image/*'
            }),
            'pdf': forms.FileInput(attrs={
                'class': 'form-control-file',
                'style': 'padding: 10px; border-radius: 8px; border: 2px dashed #e8e8e8; width: 100%;',
                'accept': '.pdf,.doc,.docx,.txt'
            }),
        }
        labels = {
            'aspect': 'الجانب',
            'title': 'عنوان التكوين',
            'description': 'وصف التكوين',
            'image': 'صورة التكوين',
            'link': 'رابط فيديو',
            'pdf': 'ملف PDF/مستند',
        }

    def clean_link(self):
        link = self.cleaned_data.get('link')
        if link and 'youtube.com' not in link and 'youtu.be' not in link:
            raise forms.ValidationError('الرجاء إدخال رابط YouTube صحيح فقط')
        return link