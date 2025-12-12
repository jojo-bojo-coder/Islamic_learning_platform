from django.db import models
from django.conf import settings
from accounts.models import User
import os
import re
from urllib.parse import urlparse, parse_qs

ASPECT_CHOICES = [
    ('tarbawiu', 'تربوي'),
    ('shareiu', 'شرعي'),
    ('mhari', 'مهاري'),
    ('medad', 'مداد'),
]


class Takwin(models.Model):
    aspect = models.CharField(
        max_length=20,
        choices=ASPECT_CHOICES,
        verbose_name="الجانب"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان التكوين")
    description = models.TextField(verbose_name="وصف التكوين")
    image = models.ImageField(
        upload_to="takwin_images/",
        blank=True,
        null=True,
        verbose_name="صورة"
    )
    link = models.URLField(blank=True, null=True, verbose_name="رابط")
    created_at = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to="pdfs/", blank=True, null=True, verbose_name="ملف pdf")

    def get_image_url(self):
        if self.image and hasattr(self.image, "url"):
            return self.image.url
        return os.path.join(settings.MEDIA_URL, "takwin_images/medad_logo2.webp")

    def get_youtube_video_id(self):
        """
        استخراج معرف الفيديو من رابط YouTube
        """
        if not self.link:
            return None

        url = str(self.link).strip()
        if not url:
            return None

        try:
            # إضافة https:// إذا لم يكن موجوداً
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # استخدام urllib.parse
            parsed = urlparse(url)

            # للروابط من نوع youtu.be
            if 'youtu.be' in parsed.netloc.lower():
                # استخراج معرف الفيديو من المسار (قبل أي معاملات)
                video_id = parsed.path.lstrip('/').split('?')[0].split('&')[0].split('/')[0]
                # تنظيف معرف الفيديو من أي أحرف إضافية
                video_id = re.sub(r'[^a-zA-Z0-9_-]', '', video_id)
                # التأكد من أن الطول صحيح (11 حرف)
                if len(video_id) == 11:
                    return video_id

            # للروابط من نوع youtube.com/watch?v=
            if 'youtube.com' in parsed.netloc.lower():
                if parsed.path == '/watch' or parsed.path == '/watch/':
                    query_params = parse_qs(parsed.query)
                    if 'v' in query_params and query_params['v']:
                        video_id = query_params['v'][0]
                        video_id = re.sub(r'[^a-zA-Z0-9_-]', '', video_id)
                        if len(video_id) == 11:
                            return video_id
                # للروابط من نوع youtube.com/embed/VIDEO_ID
                elif parsed.path.startswith('/embed/'):
                    video_id = parsed.path.replace('/embed/', '').split('?')[0].split('&')[0]
                    video_id = re.sub(r'[^a-zA-Z0-9_-]', '', video_id)
                    if len(video_id) == 11:
                        return video_id

            # استخدام regex كبديل
            patterns = [
                r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|m\.youtube\.com\/watch\?v=|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
                r'(?:youtube\.com\/watch\?.*[&?]v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
                r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})',
                r'youtu\.be\/([a-zA-Z0-9_-]{11})',
                r'(?:v=|youtu\.be\/|embed\/)([a-zA-Z0-9_-]{11})',
            ]

            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    video_id = match.group(1)
                    video_id = re.sub(r'[^a-zA-Z0-9_-]', '', video_id)
                    if len(video_id) == 11:
                        return video_id
        except Exception:
            pass

        return None

    class Meta:
        verbose_name = "تكوين"
        verbose_name_plural = "التكوين"

    def __str__(self):
        return self.title


class UserTakwin(models.Model):
    # استخدام User من accounts بدلاً من settings.AUTH_USER_MODEL
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="user_takwins"
    )
    takwin = models.ForeignKey(Takwin, on_delete=models.CASCADE, related_name="user_takwins")
    is_done = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تكوين المستخدم"
        verbose_name_plural = "تكوين المستخدمين"

    def __str__(self):
        status = 'منجز' if self.is_done else 'غير منجز'
        return f"{self.user.email} - {self.takwin.title} ({status})"