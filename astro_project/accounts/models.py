from django.db import models

# Create your models here.
class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Others'),
    ]

    nickname = models.CharField(max_length=30)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    zodiac_sign = models.CharField(max_length=20)

    bithday = models.DateField(null=False, blank=False)
    birth_time = models.TimeField(null=False, blank=False)
    birth_location = models.CharField(max_length=100)

    bio = models.TextField(blank=True)


    def __str__(self):
        return self.nickname