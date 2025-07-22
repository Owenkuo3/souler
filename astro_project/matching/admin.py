from django.contrib import admin
from .models import MatchAction, MatchScore

# Register your models here.
admin.site.register(MatchAction)
admin.site.register(MatchScore)
