from django.urls import path
from .views import RegisterAPIView, current_user_info

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('me/', current_user_info, name='current_user_info'),

]
