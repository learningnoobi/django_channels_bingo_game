from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import F

from .models import BingoRoom, TrackPlayers
from .validators import (
    MAX_CHAT_LENGTH,
    as_bingo_count,
    as_cell,
    clean_username,
    is_valid_room_name,
)

INVALID_ROOM_CLOSE_CODE = 4000


class BingoConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.url_route = self.scope["url_route"]["kwargs"]["room_name"]
        self.bingo_room = None
        self.user_left = ""  # the name this connection registered (and therefore owns)
        if not is_valid_room_name(self.url_route):
            await self.close(code=INVALID_ROOM_CLOSE_CODE)
            return
        await self.accept()
        self.room_name = f"bingo_room_{self.url_route}"
        await self.create_room()
        await self.channel_layer.group_add(self.room_name, self.channel_name)

    @database_sync_to_async
    def create_room(self):
        self.bingo_room, _ = BingoRoom.objects.get_or_create(room_name=self.url_route)
        BingoRoom.objects.filter(pk=self.bingo_room.pk).update(connections=F("connections") + 1)

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict) or self.bingo_room is None:
            return
        command = content.get("command")

        if command == "clicked":
            dataid = as_cell(content.get("dataset"))
            datatry = as_cell(content.get("dataid"))
            user = clean_username(content.get("user"))
            if dataid is None or datatry is None or user is None:
                return  # ignore malformed moves instead of breaking every client in the room
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "websocket_info",
                    "dataid": dataid,
                    "user": user,
                    "datatry": datatry,
                },
            )

        elif command in ("joined", "won"):
            user = clean_username(content.get("user"))
            if user is None:
                return
            if await self.create_players(user):
                self.user_left = user  # only the connection that created the row owns it
            # The text shown to other players is built here, never relayed from the client.
            info = f"{user} just Joined" if command == "joined" else f"{user} won the Game"
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "websocket_joined",
                    "info": info,
                    "user": user,
                    "command": command,
                    "bingoCount": as_bingo_count(content.get("bingoCount")),
                },
            )

        elif command == "chat":
            chat = content.get("chat")
            user = clean_username(content.get("user"))
            if not isinstance(chat, str) or not chat.strip() or user is None:
                return
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "websocket_chat",
                    "chat": chat[:MAX_CHAT_LENGTH],
                    "user": user,
                    "command": command,
                },
            )

    @database_sync_to_async
    def create_players(self, name):
        """Register the player; True only if this call created the row (this connection owns it)."""
        _, created = TrackPlayers.objects.get_or_create(room=self.bingo_room, username=name)
        return created

    @database_sync_to_async
    def players_count(self):
        names = list(self.bingo_room.trackplayers_set.values_list("username", flat=True))
        self.all_players_for_room = names
        self.players_count_all = len(names)

    async def websocket_info(self, event):
        await self.send_json(
            {
                "dataset": int(event["dataid"]),
                "user": event["user"],
                "dataid": int(event["datatry"]),
                "command": "clicked",
            }
        )

    async def websocket_chat(self, event):
        await self.send_json(
            {"user": event["user"], "chat": event["chat"], "command": event["command"]}
        )

    async def websocket_joined(self, event):
        await self.players_count()
        await self.send_json(
            {
                "command": event["command"],
                "info": event["info"],
                "user": event["user"],
                "bingoCount": event.get("bingoCount"),
                "users_count": self.players_count_all,
                "all_players": self.all_players_for_room,
            }
        )

    async def disconnect(self, close_code):
        if self.bingo_room is None:  # rejected before joining a room
            return
        if self.user_left:
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "websocket_leave", "info": f"{self.user_left} left room"},
            )
        await self.delete_player()
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    @database_sync_to_async
    def delete_player(self):
        """Remove only the player row this connection created, then drop the connection count.

        The room is deleted when its last live connection leaves, so one client can neither remove
        another player (by reusing their name) nor delete a room others are still connected to.
        """
        if self.user_left:
            TrackPlayers.objects.filter(
                room_id=self.bingo_room.pk, username=self.user_left
            ).delete()
        BingoRoom.objects.filter(pk=self.bingo_room.pk, connections__gt=0).update(
            connections=F("connections") - 1
        )
        BingoRoom.objects.filter(pk=self.bingo_room.pk, connections=0).delete()

    async def websocket_leave(self, event):
        if await self.room_is_gone():
            return
        await self.players_count()
        await self.send_json(
            {
                "command": "joined",
                "info": event["info"],
                "users_count": self.players_count_all,
                "all_players": self.all_players_for_room,
            }
        )

    @database_sync_to_async
    def room_is_gone(self):
        return not BingoRoom.objects.filter(pk=self.bingo_room.pk).exists()


class OnlineRoomConsumer(AsyncJsonWebsocketConsumer):
    GROUP = "online_bingo_room"

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add(self.GROUP, self.channel_name)
        await self.send_online_rooms()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.GROUP, self.channel_name)

    @database_sync_to_async
    def online_room(self):
        return [
            {"room_name": room.room_name, "room_id": f"{room.room_name}-{room.id}"}
            for room in BingoRoom.objects.all()
        ]

    async def send_online_rooms(self):
        # Only the newly connected client needs the full list; everyone else gets
        # incremental room_added / room_deleted events.
        await self.send_json({"command": "online_rooms", "online_rooms": await self.online_room()})

    async def websocket_room_added(self, event):
        await self.send_json(
            {
                "command": event["command"],
                "room_name": event["room_name"],
                "room_id": event["room_id"],
            }
        )

    async def websocket_room_deleted(self, event):
        await self.send_json(
            {
                "command": event["command"],
                "room_name": event["room_name"],
                "room_id": event["room_id"],
            }
        )
