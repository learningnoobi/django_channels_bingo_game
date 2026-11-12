import pytest
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from bingo.models import BingoRoom
from bingo.routing import websocket_urlpatterns

pytestmark = pytest.mark.django_db(transaction=True)

router = URLRouter(websocket_urlpatterns)


async def open_lobby():
    comm = WebsocketCommunicator(router, "/ws/online-rooms/")
    connected, _ = await comm.connect()
    assert connected
    return comm


async def test_new_client_receives_the_current_rooms():
    await database_sync_to_async(BingoRoom.objects.create)(room_name="alpha")
    lobby = await open_lobby()
    msg = await lobby.receive_json_from()
    assert msg["command"] == "online_rooms"
    assert [r["room_name"] for r in msg["online_rooms"]] == ["alpha"]
    await lobby.disconnect()


async def test_lobby_with_no_rooms_gets_an_empty_list():
    lobby = await open_lobby()
    assert (await lobby.receive_json_from())["online_rooms"] == []
    await lobby.disconnect()


async def test_existing_clients_are_not_resent_the_whole_list_when_someone_connects():
    first = await open_lobby()
    await first.receive_json_from()
    second = await open_lobby()
    await second.receive_json_from()
    assert await first.receive_nothing()
    await first.disconnect()
    await second.disconnect()


async def test_creating_and_deleting_a_room_is_pushed_to_the_lobby():
    lobby = await open_lobby()
    await lobby.receive_json_from()
    room = await database_sync_to_async(BingoRoom.objects.create)(room_name="beta")
    added = await lobby.receive_json_from()
    assert added["command"] == "room_added" and added["room_name"] == "beta"
    assert added["room_id"] == room.id
    await database_sync_to_async(room.delete)()
    removed = await lobby.receive_json_from()
    assert removed["command"] == "room_deleted" and removed["room_name"] == "beta"
    await lobby.disconnect()


async def test_updating_a_room_does_not_announce_it_again():
    lobby = await open_lobby()
    await lobby.receive_json_from()
    room = await database_sync_to_async(BingoRoom.objects.create)(room_name="gamma")
    await lobby.receive_json_from()
    room.room_name = "gamma2"
    await database_sync_to_async(room.save)()
    assert await lobby.receive_nothing()
    await lobby.disconnect()
