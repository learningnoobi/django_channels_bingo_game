from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db import transaction
from django.db.models import F

from .models import BingoRoom, TrackPlayers
from .validators import (
    MAX_CHAT_LENGTH,
    MAX_PLAYERS_PER_ROOM,
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
        """Find or create the room and count this connection, retrying if the room vanishes.

        Rooms have no unique constraint on their name, so look up the oldest match instead of
        ``get_or_create`` (which raises when duplicates exist). The increment is a single UPDATE;
        if it touches no row the room was deleted by the last connection leaving, so try again.
        """
        for _ in range(5):
            room = BingoRoom.objects.filter(room_name=self.url_route).order_by("pk").first()
            if room is None:
                room = BingoRoom.objects.create(room_name=self.url_route)
            updated = BingoRoom.objects.filter(pk=room.pk).update(connections=F("connections") + 1)
            if updated:
                self.bingo_room = room
                return
        raise RuntimeError(f"could not join room {self.url_route!r}")

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict) or self.bingo_room is None:
            return
        command = content.get("command")

        if command in ("joined", "won"):
            user = clean_username(content.get("user"))
            if user is None:
                return
            # A connection registers exactly one name, and "won" can only come from that name.
            if self.user_left and user != self.user_left:
                return
            if not self.user_left:
                if command == "won" or not await self.register_player(user):
                    return  # must join first; room full
                self.user_left = user
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
            return

        # Everything else is only accepted from a joined connection, and is always attributed to
        # the name that connection registered, whatever the client puts in "user".
        if not self.user_left:
            return

        if command == "clicked":
            dataid = as_cell(content.get("dataset"))
            datatry = as_cell(content.get("dataid"))
            if dataid is None or datatry is None:
                return  # ignore malformed moves instead of breaking every client in the room
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "websocket_info",
                    "dataid": dataid,
                    "user": self.user_left,
                    "datatry": datatry,
                },
            )

        elif command == "chat":
            chat = content.get("chat")
            if not isinstance(chat, str) or not chat.strip():
                return
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "websocket_chat",
                    "chat": chat[:MAX_CHAT_LENGTH],
                    "user": self.user_left,
                    "command": command,
                },
            )

    @database_sync_to_async
    def register_player(self, name):
        """Register this connection as ``name``; False if the room already has too many players."""
        players = TrackPlayers.objects.filter(room_id=self.bingo_room.pk)
        if (
            not players.filter(username=name).exists()
            and players.values("username").distinct().count() >= MAX_PLAYERS_PER_ROOM
        ):
            return False
        TrackPlayers.objects.create(
            room_id=self.bingo_room.pk, username=name, channel_name=self.channel_name
        )
        return True

    @database_sync_to_async
    def players_count(self):
        names = sorted(
            set(
                TrackPlayers.objects.filter(room_id=self.bingo_room.pk).values_list(
                    "username", flat=True
                )
            )
        )
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
        name_still_present = await self.delete_player()
        await self.channel_layer.group_discard(self.room_name, self.channel_name)
        # Announce the departure only if no other connection (for example the player's refreshed
        # tab) still holds that name.
        if self.user_left and not name_still_present:
            await self.channel_layer.group_send(
                self.room_name,
                {"type": "websocket_leave", "info": f"{self.user_left} left room"},
            )

    @database_sync_to_async
    def delete_player(self):
        """Remove only this connection's player row and drop the live-connection count.

        Returns True if another connection still holds the same player name.

        The room is deleted when its last live connection leaves. The decrement and the
        conditional delete run in one transaction; the delete only matches a room whose count is
        zero, so a connection that arrived in between keeps the room alive.
        """
        with transaction.atomic():
            TrackPlayers.objects.filter(
                room_id=self.bingo_room.pk, channel_name=self.channel_name
            ).delete()
            BingoRoom.objects.filter(pk=self.bingo_room.pk, connections__gt=0).update(
                connections=F("connections") - 1
            )
            BingoRoom.objects.filter(pk=self.bingo_room.pk, connections=0).delete()
        return bool(
            self.user_left
            and TrackPlayers.objects.filter(
                room_id=self.bingo_room.pk, username=self.user_left
            ).exists()
        )

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
