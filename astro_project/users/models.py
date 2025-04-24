from django.db import models
from accounts.models import UserProfile
from .utils import calculate_sun_sign


class UserBirthInfo(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='birth_info')
    birth_year = models.IntegerField()
    birth_month = models.IntegerField()
    birth_day = models.IntegerField()
    birth_hour = models.IntegerField()
    birth_minute = models.IntegerField()
    birth_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    birth_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    birth_location = models.CharField(max_length=100, blank=True, null=True) # 可選的文字地點

    zodiac_sign = models.CharField(max_length=20, blank=True, null=True) # 星座，可以在後續計算或填寫

    def __str__(self):
        return f"{self.user_profile.nickname} 的出生資訊"
    

    def save(self, *args, **kwargs):
        if self.birth_year and self.birth_month and self.birth_day and self.birth_hour is not None:
            self.zodiac_sign = calculate_sun_sign(
                self.birth_year,
                self.birth_month,
                self.birth_day,
                self.birth_hour,
                self.birth_minute or 0,
                self.birth_latitude or 0.0,
                self.birth_longitude or 0.0
            )
        super().save(*args, **kwargs)