from django.urls import path
from . import views

urlpatterns = [
    path('candidates/', views.show_match_candidates, name='match_candidates'),
    path('match/action/', views.send_match_action, name='send_match_action'),
]