from django.urls import path
from .views import user_chart_view


urlpatterns = [
    path('my-chart/', user_chart_view, name='user_chart'),

]
