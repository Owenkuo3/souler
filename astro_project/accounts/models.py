from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager() 


    def __str__(self):
        return self.email


class UserProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=30, unique=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)
    bio = models.TextField(blank=True)
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Others')],
        blank=True,
        null=True
    )
    match_gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Others'), ('A', 'All')],
        default='A',
        help_text="希望配對對象的性別"
    )
    preferred_age_min = models.PositiveIntegerField(null=True, blank=True)
    preferred_age_max = models.PositiveIntegerField(null=True, blank=True)


    def __str__(self):
        return self.nickname
    def save(self, *args, **kwargs):
        # 只在「剛上傳的新照片」時壓縮：存過的檔名會帶 user_photos/ 前綴，沒有前綴
        # 代表是這次請求新上傳的。避免每次存個人資料都重新壓縮＋重傳照片
        # （照片改存雲端後這點尤其重要，否則改個暱稱都會重傳一次圖）。
        if self.photo and not self.photo.name.startswith('user_photos/'):
            img = Image.open(self.photo)

            if img.mode != 'RGB':
                img = img.convert('RGB')

            output_io = BytesIO()
            img.save(output_io, format='JPEG', quality=70)
            output_io.seek(0)

            self.photo.save(self.photo.name, ContentFile(output_io.read()), save=False)

        super().save(*args, **kwargs)