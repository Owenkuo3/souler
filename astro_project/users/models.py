from django.db import models
from accounts.models import UserProfile
from .utils import city_name_mapping, get_lat_lng_by_city
from django.core.validators import MinValueValidator, MaxValueValidator


class UserBirthInfo(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='birth_info')
    birth_year = models.IntegerField(validators=[MinValueValidator(1900), MaxValueValidator(2100)])
    birth_month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    birth_day = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(31)])
    birth_hour = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(23)])
    birth_minute = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(59)])
    birth_latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    birth_longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    birth_location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user_profile.nickname} 的出生資訊"
    
    def save(self, *args, **kwargs):
        if self.birth_location and not self.birth_latitude:
            lat, lon = get_lat_lng_by_city(self.birth_location)
            self.birth_latitude = lat
            self.birth_longitude = lon
        super().save(*args, **kwargs)