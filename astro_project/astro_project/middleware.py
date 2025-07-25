# astro_project/middleware.py

from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from urllib.parse import parse_qs
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from accounts.models import CustomUser

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope['query_string'].decode()
        token = parse_qs(query_string).get('token', [None])[0]

        if token is None:
            scope['user'] = AnonymousUser()
            return await super().__call__(scope, receive, send)

        try:
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            user = await database_sync_to_async(CustomUser.objects.get)(id=user_id)
            scope['user'] = user
        except Exception:
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
