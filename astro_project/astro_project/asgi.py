"""
ASGI config for astro_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing  # 👈 等下會建立這個檔案

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'astro_project.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # 還是支援原本的 HTTP
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns  # 👈 對應聊天室 WebSocket 的入口
        )
    ),
})