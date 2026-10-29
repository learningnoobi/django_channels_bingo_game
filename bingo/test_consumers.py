import pytest
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from bingo.models import BingoRoom, TrackPlayers
from bingo.routing import websocket_urlpatterns

pytestmark = pytest.mark.django_db(transaction=True)

router = URLRouter(websocket_urlpatterns)


async def connect(path):
    comm = WebsocketCommunicator(router, path)
    connected, code = await comm.connect()
    return comm, connected, code


async def join(comm, user):
    await comm.send_json_to({"command": "joined", "user": user, "info": f"{user} joined"})


@database_sync_to_async
def room_names():
    return list(BingoRoom.objects.values_list("room_name", flat=True))


@database_sync_to_async
def player_names():
    return sorted(TrackPlayers.objects.values_list("username", flat=True))


async def test_connect_creates_the_room():
    comm, connected, _ = await connect("/ws/clicked/alpha/")
    assert connected and await room_names() == ["alpha"]
    await comm.disconnect()


async def test_join_is_broadcast_with_player_list_and_count():
    a, _, _ = await connect("/ws/clicked/alpha/")
    b, _, _ = await connect("/ws/clicked/alpha/")
    await join(a, "ann")
    msg_a = await a.receive_json_from()
    msg_b = await b.receive_json_from()
    for msg in (msg_a, msg_b):
        assert msg["command"] == "joined" and msg["user"] == "ann"
        assert msg["users_count"] == 1 and msg["all_players"] == ["ann"]
    await join(b, "bob")
    msg = await a.receive_json_from()
    assert msg["users_count"] == 2 and sorted(msg["all_players"]) == ["ann", "bob"]
    await a.disconnect()
    await b.disconnect()


async def test_click_reaches_everyone_in_the_room_as_integers():
    a, _, _ = await connect("/ws/clicked/alpha/")
    b, _, _ = await connect("/ws/clicked/alpha/")
    await a.send_json_to({"command": "clicked", "dataset": "7", "dataid": 3, "user": "ann"})
    for comm in (a, b):
        assert await comm.receive_json_from() == {
            "dataset": 7, "dataid": 3, "user": "ann", "command": "clicked",
        }  # fmt: skip
    await a.disconnect()
    await b.disconnect()


async def test_rooms_are_isolated_from_each_other():
    a, _, _ = await connect("/ws/clicked/alpha/")
    b, _, _ = await connect("/ws/clicked/beta/")
    await a.send_json_to({"command": "clicked", "dataset": 1, "dataid": 1, "user": "ann"})
    await a.receive_json_from()
    assert await b.receive_nothing()
    await a.disconnect()
    await b.disconnect()


@pytest.mark.parametrize(
    "payload",
    [
        {"command": "clicked"},
        {"command": "clicked", "dataset": None, "dataid": 3},
        {"command": "clicked", "dataset": "x", "dataid": 3},
        {"command": "clicked", "dataset": 26, "dataid": 3},
        {"command": "clicked", "dataset": 0, "dataid": 3},
    ],
)
async def test_malformed_clicks_are_ignored_and_do_not_break_the_room(payload):
    a, _, _ = await connect("/ws/clicked/alpha/")
    b, _, _ = await connect("/ws/clicked/alpha/")
    await a.send_json_to({**payload, "user": "ann"})
    assert await b.receive_nothing()
    # the room still works afterwards
    await a.send_json_to({"command": "clicked", "dataset": 5, "dataid": 5, "user": "ann"})
    assert (await b.receive_json_from())["dataset"] == 5
    await a.disconnect()
    await b.disconnect()


async def test_non_object_and_unknown_messages_are_ignored():
    a, _, _ = await connect("/ws/clicked/alpha/")
    await a.send_json_to([1, 2, 3])
    await a.send_json_to({"command": "nope"})
    assert await a.receive_nothing()
    await a.disconnect()


async def test_chat_is_relayed_trimmed_and_blank_chat_ignored():
    a, _, _ = await connect("/ws/clicked/alpha/")
    await a.send_json_to({"command": "chat", "chat": "hi", "user": "ann"})
    assert await a.receive_json_from() == {"user": "ann", "chat": "hi", "command": "chat"}
    await a.send_json_to({"command": "chat", "chat": "x" * 900, "user": "ann"})
    assert len((await a.receive_json_from())["chat"]) == 500
    await a.send_json_to({"command": "chat", "chat": "   ", "user": "ann"})
    await a.send_json_to({"command": "chat", "chat": 5, "user": "ann"})
    assert await a.receive_nothing()
    await a.disconnect()


@pytest.mark.parametrize("name", ["", "   ", None, 42, "n" * 51])
async def test_unusable_usernames_are_not_registered(name):
    a, _, _ = await connect("/ws/clicked/alpha/")
    await a.send_json_to({"command": "joined", "user": name, "info": "x"})
    assert await a.receive_nothing()
    assert await player_names() == []
    await a.disconnect()


async def test_won_is_broadcast_with_the_bingo_count():
    a, _, _ = await connect("/ws/clicked/alpha/")
    await a.send_json_to({"command": "won", "user": "ann", "info": "ann won", "bingoCount": 5})
    msg = await a.receive_json_from()
    assert msg["command"] == "won" and msg["bingoCount"] == 5
    await a.disconnect()


@pytest.mark.parametrize(
    "path", ["/ws/clicked/bad name/", "/ws/clicked/é/", "/ws/clicked/" + "r" * 51 + "/"]
)
async def test_invalid_room_names_are_rejected(path):
    comm = WebsocketCommunicator(router, path)
    connected, code = await comm.connect()
    assert connected is False and code == 4000
    assert await room_names() == []


async def test_disconnect_without_joining_does_not_crash_and_cleans_up_empty_room():
    comm, connected, _ = await connect("/ws/clicked/alpha/")
    assert connected and await room_names() == ["alpha"]
    await comm.disconnect()
    assert await room_names() == []


async def test_leaving_updates_the_others_and_last_player_deletes_the_room():
    a, _, _ = await connect("/ws/clicked/alpha/")
    b, _, _ = await connect("/ws/clicked/alpha/")
    await join(a, "ann")
    await join(b, "bob")
    for comm in (a, b):  # drain the two join broadcasts each client receives
        await comm.receive_json_from()
        await comm.receive_json_from()

    await a.disconnect()
    msg = await b.receive_json_from()
    assert msg["info"] == "ann left room" and msg["users_count"] == 1
    assert msg["all_players"] == ["bob"] and await room_names() == ["alpha"]

    await b.disconnect()
    assert await room_names() == [] and await player_names() == []


async def test_joining_twice_with_the_same_name_registers_one_player():
    a, _, _ = await connect("/ws/clicked/alpha/")
    await join(a, "ann")
    await a.receive_json_from()
    await join(a, "ann")
    msg = await a.receive_json_from()
    assert msg["users_count"] == 1
    await a.disconnect()
