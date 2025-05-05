from django.db import models
from accounts.models import UserProfile
from .utils import calculate_full_chart, city_name_mapping, get_lat_lng_by_city
from django.core.validators import MinValueValidator, MaxValueValidator
from astrology.services.birth_info_service import enrich_birth_info_with_coordinates_and_signs



class City(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return self.name

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

    # 星座欄位
    sun_sign = models.CharField(max_length=20, blank=True, null=True)
    moon_sign = models.CharField(max_length=20, blank=True, null=True)
    mercury_sign = models.CharField(max_length=20, blank=True, null=True)
    venus_sign = models.CharField(max_length=20, blank=True, null=True)
    mars_sign = models.CharField(max_length=20, blank=True, null=True)
    jupiter_sign = models.CharField(max_length=20, blank=True, null=True)
    saturn_sign = models.CharField(max_length=20, blank=True, null=True)
    uranus_sign = models.CharField(max_length=20, blank=True, null=True)
    neptune_sign = models.CharField(max_length=20, blank=True, null=True)
    pluto_sign = models.CharField(max_length=20, blank=True, null=True)
    ascendant_sign = models.CharField(max_length=10, null=True, blank=True)
    descendant_sign = models.CharField(max_length=10, null=True, blank=True)
    mc_sign = models.CharField(max_length=10, null=True, blank=True)  # 天頂
    ic_sign = models.CharField(max_length=10, null=True, blank=True)  # 天底

    def __str__(self):
        return f"{self.user_profile.nickname} 的出生資訊"


    def save(self, *args, **kwargs):
        enrich_birth_info_with_coordinates_and_signs(self)
        super().save(*args, **kwargs)
