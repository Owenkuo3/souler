from django.db import models
from accounts.models import UserProfile
from .utils import calculate_sun_sign, city_name_mapping, get_lat_lng_by_city, calculate_moon_sign


class City(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return self.name

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
    moon_sign = models.CharField(max_length=20, blank=True, null=True)    # 月亮星座（新增）

    def __str__(self):
        return f"{self.user_profile.nickname} 的出生資訊"
    

    def save(self, *args, **kwargs):
        if self.birth_location:
            # 先把中文城市轉成英文城市
            english_city = city_name_mapping.get(self.birth_location, self.birth_location)
            lat, lng = get_lat_lng_by_city(english_city)

            if lat is not None and lng is not None:
                self.birth_latitude = lat
                self.birth_longitude = lng
            else:
                self.birth_latitude = None
                self.birth_longitude = None
        print(f"===> 檢查經緯度: {self.birth_latitude}, {self.birth_longitude}")

        try:
            if all(value is not None for value in [
                self.birth_year,
                self.birth_month,
                self.birth_day,
                self.birth_hour,
                self.birth_minute,
                self.birth_latitude,
                self.birth_longitude,
            ]):
                self.zodiac_sign = calculate_sun_sign(
                    self.birth_year,
                    self.birth_month,
                    self.birth_day,
                    self.birth_hour,
                    self.birth_minute,
                    float(self.birth_latitude),
                    float(self.birth_longitude)
                )
                self.moon_sign = calculate_moon_sign(
                    self.birth_year,
                    self.birth_month,
                    self.birth_day,
                    self.birth_hour,
                    self.birth_minute,
                    float(self.birth_latitude),
                    float(self.birth_longitude)
                )
            print("===> 實際星座計算結果:", self.zodiac_sign, "/", self.moon_sign)

        except Exception as e:
            print("星座計算失敗:", e)
            self.zodiac_sign = None

        super().save(*args, **kwargs)
