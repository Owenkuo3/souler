from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=30, unique=True)
    photo = models.ImageField(upload_to='user_photos/', blank=True, null=True)
    bio = models.TextField(blank=True)
    gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Others')],
        blank=True,
        null=True
    )
    match_gender = models.CharField(
        max_length=1,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Others'), ('A', 'All')],
        default='A',
        help_text="希望配對對象的性別"
    )
    preferred_age_min = models.PositiveIntegerField(null=True, blank=True)
    preferred_age_max = models.PositiveIntegerField(null=True, blank=True)


    def __str__(self):
        return self.nickname