from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from accounts.models import UserProfile



class MatchScore(models.Model):
    user_a = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='match_initiator'
    )
    user_b = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='match_target'
    )
    score = models.FloatField()
    matched_aspects = models.JSONField(null=True, blank=True)  
    # 儲存相位詳細資料，例如 [{"planet_a": "Mars", "planet_b": "Venus", "aspect": "Trine", "score": +3}, ...]

    ai_interpretation = models.TextField(null=True, blank=True)
    # 未來你可以存在這裡（付費解鎖後才顯示）

    is_ai_unlocked = models.BooleanField(default=False)
    # 是否已解鎖 AI 解說（未來付費功能可用）

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user_a', 'user_b')


class MatchAction(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'

    ACTION_CHOICES = [
        (LIKE, '喜歡'),
        (DISLIKE, '不喜歡'),
    ]

    from_user = models.ForeignKey(UserProfile, related_name='from_user_actions', on_delete=models.CASCADE)
    to_user = models.ForeignKey(UserProfile, related_name='to_user_actions', on_delete=models.CASCADE)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')  # 每個 from_user 對 to_user 只能操作一次

    def __str__(self):
        return f"{self.from_user} -> {self.to_user}: {self.action}"