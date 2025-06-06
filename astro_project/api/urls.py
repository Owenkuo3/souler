from django.urls import path
from . import views

urlpatterns = [
    path('ping/', views.ping, name='ping'),  # 測試 API 是否正常

]
