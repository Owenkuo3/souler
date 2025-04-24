from django.db import models
from accounts.models import UserProfile

class UserBirthInfo(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='birth_info')
    birth_year = models.IntegerField()
    birth_month = models.IntegerField()
    birth_day = models.IntegerField()
    birth_hour = models.IntegerField()
    birth_minute = models.IntegerField()
    birth_second = models.IntegerField(blank=True, null=True)
    birth_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    birth_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    birth_location = models.CharField(max_length=100, blank=True, null=True) # 可選的文字地點

    zodiac_sign = models.CharField(max_length=20, blank=True, null=True) # 星座，可以在後續計算或填寫

    def __str__(self):
        return f"{self.user_profile.nickname} 的出生資訊"