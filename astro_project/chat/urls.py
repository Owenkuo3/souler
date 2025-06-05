# chat/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.chat_room_list, name='chat_room_list'),
    path('rooms/<int:room_id>/', views.chat_room_detail, name='chat_room_detail'),  # 需要 room_id

]
