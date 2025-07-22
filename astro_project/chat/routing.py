from django.urls import path
from . import consumers  # 等下會寫這個

websocket_urlpatterns = [
    path("ws/chat/<int:room_id>/", consumers.ChatConsumer.as_asgi()),
]