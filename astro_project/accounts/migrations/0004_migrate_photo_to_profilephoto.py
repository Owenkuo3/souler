# 把 UserProfile.photo（單張）搬進 ProfilePhoto（多張）。
# 只複製檔案參照（同一個 storage 路徑），不搬移實體檔案。
from django.db import migrations


def forwards(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    ProfilePhoto = apps.get_model('accounts', 'ProfilePhoto')
    for profile in UserProfile.objects.exclude(photo='').exclude(photo__isnull=True):
        ProfilePhoto.objects.create(user_profile=profile, image=profile.photo.name)


def backwards(apps, schema_editor):
    pass  # 舊欄位仍保留，不需要反向搬移


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_profilephoto'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
