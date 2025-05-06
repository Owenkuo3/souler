from django.contrib import admin
from .models import PlanetPosition
# Register your models here.

@admin.register(PlanetPosition)
class PlanetPosition(admin.ModelAdmin):
    list_display = ('user_profile', 'planet_name', 'zodiac_sign', 'degree', 'house')
