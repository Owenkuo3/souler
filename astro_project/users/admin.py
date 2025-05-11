from django.contrib import admin
from .models import UserBirthInfo

@admin.register(UserBirthInfo)
class UserBirthInfoAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'birth_year', 'birth_location')
