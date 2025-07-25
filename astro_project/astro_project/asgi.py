"""
ASGI config for astro_project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import chat.routing



os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'astro_project.settings')

# 先初始化 Django（這行會完成 AppRegistry 的初始化）
django_asgi_app = get_asgi_application()

from .middleware import JWTAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,  # 原本的 HTTP 支援
    "websocket": JWTAuthMiddleware(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})