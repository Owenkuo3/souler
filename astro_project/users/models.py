from django.db import models
from accounts.models import UserProfile
from .utils import calculate_full_chart, city_name_mapping, get_lat_lng_by_city


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
            if self.sun_sign is not None:
                return
            
            if all(value is not None for value in [
                self.birth_year,
                self.birth_month,
                self.birth_day,
                self.birth_hour,
                self.birth_minute,
                self.birth_latitude,
                self.birth_longitude,
            ]):
            
                chart = calculate_full_chart(
                    self.birth_year,
                    self.birth_month,
                    self.birth_day,
                    self.birth_hour,
                    self.birth_minute,
                    float(self.birth_latitude),
                    float(self.birth_longitude),
                )

                self.sun_sign = chart["太陽"]["星座"]
                self.moon_sign = chart["月亮"]["星座"]
                self.mercury_sign = chart["水星"]["星座"]
                self.venus_sign = chart["金星"]["星座"]
                self.mars_sign = chart["火星"]["星座"]
                self.jupiter_sign = chart["木星"]["星座"]
                self.saturn_sign = chart["土星"]["星座"]
                self.uranus_sign = chart["天王星"]["星座"]
                self.neptune_sign = chart["海王星"]["星座"]
                self.pluto_sign = chart["冥王星"]["星座"]
                
        except Exception as e:
            print("星座計算失敗:", e)
            self.zodiac_sign = None

        super().save(*args, **kwargs)
