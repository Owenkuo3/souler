from django.db import models
from django.utils import timezone
from datetime import timedelta


# Create your models here.
class EmailVerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self, minutes=15):
        return timezone.now() > self.created_at + timedelta(minutes=minutes)

class VapidKeyPair(models.Model):
    """Web Push 用的 VAPID 金鑰（自簽、免第三方服務）。
    存 DB 是為了跨部署持久（Render 免費層無持久碟）；全站只會有一列。"""
    private_pem = models.TextField()
    public_key_b64 = models.CharField(max_length=255)  # 瀏覽器 applicationServerKey 用
    created_at = models.DateTimeField(auto_now_add=True)


class PushSubscription(models.Model):
    """一個瀏覽器/裝置的推播訂閱。一個使用者可以有多個（手機+電腦）。"""
    user = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.CASCADE, related_name='push_subscriptions'
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
