from django.db import models
from users.models import UserProfile

class PlanetPosition(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    planet_name = models.CharField(max_length=50)
    zodiac_sign = models.CharField(max_length=50)
    degree = models.FloatField()
    house = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    correct_degree = models.FloatField()
    is_retrograde = models.BooleanField(default=False)  # 逆行（軸點恆為 False）


    def __str__(self):
        return f"{self.planet_name} in {self.zodiac_sign} ({self.degree}°)"