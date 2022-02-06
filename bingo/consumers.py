from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync, sync_to_async
import json

class BingoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):

        await self.accept()
        self.url_route = self.scope['url_route']['kwargs']['room_name']
        self.room_name = f'bingo_room_{self.url_route}'
        print(self.room_name)
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

    async def receive_json(self, content):
        dataid = content.get("dataset", None)
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "websocket_info",
                "dataid": dataid,
                "user": content.get("user", None)

            }
        )


    async def websocket_info(self, event):
        print('event came boi')
        await self.send_json(({
            'dataset': int(event["dataid"]),
            'user':event["user"]
          
        }))

    async def disconnect(self, close_code):
        print('disconnected')
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )