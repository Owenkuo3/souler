from django.db import models
from django.utils import timezone
from datetime import timedelta


# Create your models here.
class EmailVerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    
    def is_expired(self):
        expiration_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiration_time
