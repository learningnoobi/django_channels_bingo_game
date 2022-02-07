from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync, sync_to_async
import json
from .models import BingoRoom,TrackPlayers

class BingoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        
        await self.accept()
        self.url_route = self.scope['url_route']['kwargs']['room_name']
        self.room_name = f'bingo_room_{self.url_route}'
        await self.create_room()
        self.user_left=''
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        
    @database_sync_to_async
    def create_room(self):
        
        self.bingo_room,_ = BingoRoom.objects.get_or_create(room_name=self.url_route)

    async def receive_json(self, content):
        command = content.get("command", None)
        
        if command == "clicked":
            dataid = content.get("dataset", None)
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "websocket_info",
                    "dataid": dataid,
                    "user": content.get("user", None),
                    "datatry":content.get("dataid", None),

                }
            )
        if command == "joined" or command == "won":
            info = content.get("info", None)
            user = content.get("user", None)

            await self.create_players(user)
           
            self.user_left =content.get("user", None)
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "websocket_joined",
                    "info": info,
                    "user":user,
                    "command":command,
                    
              
                }
            )
    @database_sync_to_async
    def create_players(self,name):
        TrackPlayers.objects.get_or_create(room=self.bingo_room,username=name)

    @database_sync_to_async
    def players_count(self):
        self.all_players_for_room = [x.username for x in self.bingo_room.trackplayers_set.all()]
        self.players_count_all = self.bingo_room.trackplayers_set.all().count()

    async def websocket_info(self, event):
        await self.send_json(({
            'dataset': int(event["dataid"]),
            'user':event["user"],
            'dataid':int(event["datatry"]),
            'command':'clicked',
          
        }))
    
    async def websocket_joined(self, event):
        await self.players_count()
        await self.send_json(({
             'command':event["command"],
            'info':event["info"],
             'user':event["user"],
             "users_count":self.players_count_all,
             "all_players":self.all_players_for_room
        }))

    async def disconnect(self, close_code):
        print(close_code)
        
        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "websocket_leave",
                "info":f"{self.user_left} left room",
                
            }
        )
        await self.delete_player()
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name,
          
        )
    
    @database_sync_to_async
    def delete_player(self):
        TrackPlayers.objects.get(room=self.bingo_room,username=self.user_left).delete()
        players_count = self.bingo_room.trackplayers_set.all().count()
        if players_count == 0:
            self.bingo_room.delete()

    async def websocket_leave(self, event):
        await self.players_count()
        await self.send_json(({
            'command':'joined',
            'info':event["info"],
            "users_count":self.players_count_all,
             "all_players":self.all_players_for_room
          
        }))

        
  
     