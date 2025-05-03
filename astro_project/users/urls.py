from django.urls import path
from .views import enter_birth_info

urlpatterns = [
    path('birth-info/', enter_birth_info, name='enter_birth_info'),

]
