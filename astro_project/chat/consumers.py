import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # 加入聊天室 group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # 離開聊天室 group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        from .models import ChatRoom, Message 
        from users.models import UserProfile 
        from django.contrib.auth import get_user_model

        @database_sync_to_async
        def get_real_user(user):
            return get_user_model().objects.get(id=user.id)        
        data = json.loads(text_data)
        message_text = data['message']
        user = self.scope['user']

        if not user.is_authenticated:
            await self.close()
            return
        real_user = await get_real_user(user)


        # 拿 Room 實體（注意：不能直接存 room_id，要用關聯）
        room = await database_sync_to_async(ChatRoom.objects.get)(id=self.room_id)

        # 儲存訊息
        message = await database_sync_to_async(Message.objects.create)(
            room=room,
            sender=real_user,
            content=message_text,
        )

        # 拿使用者暱稱（從 UserProfile）
        nickname = await database_sync_to_async(lambda: user.profile.nickname)()

        # 廣播給群組
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message.content,
                'sender_id': real_user.id,
                'sender_nickname': nickname,
                'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_nickname': event['sender_nickname'],
            'timestamp': event['timestamp'],
        }))
