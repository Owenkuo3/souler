from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from api.models import EmailVerificationCode

class Command(BaseCommand):
    help = '刪除已過期的 Email 驗證碼（10 分鐘前產生且未驗證）'

    def handle(self, *args, **options):
        expiration_threshold = timezone.now() - timedelta(minutes=10)
        expired_codes = EmailVerificationCode.objects.filter(
            is_verified=False,
            created_at__lt=expiration_threshold
        )
        count = expired_codes.count()
        expired_codes.delete()
        self.stdout.write(self.style.SUCCESS(f'成功刪除 {count} 筆過期驗證碼'))
