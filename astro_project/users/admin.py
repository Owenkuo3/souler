from django.contrib import admin
from .models import UserBirthInfo, City

@admin.register(UserBirthInfo)
class UserBirthInfoAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'birth_year', 'zodiac_sign', 'birth_location')

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)