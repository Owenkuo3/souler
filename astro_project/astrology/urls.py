from django.urls import path
from . import views

app_name = 'astrology'

urlpatterns = [
    path('chart/', views.chart_result, name='chart_result'),

]
