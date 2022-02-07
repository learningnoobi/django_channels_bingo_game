from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync, sync_to_async
import json

class BingoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        
        await self.accept()
        self.url_route = self.scope['url_route']['kwargs']['room_name']
        self.room_name = f'bingo_room_{self.url_route}'
        self.user_left=''
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

    async def receive_json(self, content):
        command = content.get("command", None)
        print(command)
        
        if command == "clicked":
            dataid = content.get("dataset", None)
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "websocket_info",
                    "dataid": dataid,
                    "user": content.get("user", None)

                }
            )
        if command == "joined":
            info = content.get("info", None)
            user = content.get("user", None)
            self.user_left =content.get("user", None)
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "websocket_joined",
                    "info": info,
                    "user":user
                }
            )
  
            



    async def websocket_info(self, event):
        await self.send_json(({
            'dataset': int(event["dataid"]),
            'user':event["user"],
            'command':'clicked',
          
        }))
    
    async def websocket_joined(self, event):
        await self.send_json(({
            'command':'joined',
            'info':event["info"],
             'user':event["user"]
          
        }))

    async def disconnect(self, close_code):
        print(close_code)
        
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "websocket_leave",
                "info":f"{self.user_left} left room"
            }
        )
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name,
          
        )

    async def websocket_leave(self, event):
        await self.send_json(({
            'command':'joined',
            'info':event["info"],
          
        }))

        
  
     