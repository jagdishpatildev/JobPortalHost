import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, ChatMessage, User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id    = self.scope['url_route']['kwargs']['room_id']
        self.room_group = f'chat_{self.room_id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data    = json.loads(text_data)
        message = data['message']
        user    = self.scope['user']

        saved = await self.save_message(user, self.room_id, message)
        await self.channel_layer.group_send(self.room_group, {
            'type':      'chat_message',
            'message':   message,
            'sender':    user.username,
            'timestamp': saved.timestamp.strftime('%H:%M'),
        })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message':   event['message'],
            'sender':    event['sender'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def save_message(self, user, room_id, message):
        room = ChatRoom.objects.get(pk=room_id)
        return ChatMessage.objects.create(room=room, sender=user, message=message)