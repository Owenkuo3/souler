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


class ChartInterpretation(models.Model):
    """AI 生成的個人星盤解說。與星盤綁定快取：出生資料修改（星盤重算）時刪除，
    下次查看再重新生成 —— 修改次數本身有限制（3 次免費後 30 天一次），天然控管生成成本。"""
    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE, related_name='chart_interpretation'
    )
    content = models.TextField()
    model_used = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_profile.nickname} 的星盤解說"