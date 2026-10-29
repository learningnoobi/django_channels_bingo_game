import asyncio

import pytest
from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator

from bingo.models import BingoRoom, TrackPlayers
from bingo.routing import websocket_urlpatterns
from bingo.validators import MAX_PLAYERS_PER_ROOM

pytestmark = pytest.mark.django_db(transaction=True)

router = URLRouter(websocket_urlpatterns)


async def connect(path="/ws/clicked/alpha/"):
    comm = WebsocketCommunicator(router, path)
    connected, code = await comm.connect()
    return comm, connected, code


async def join(comm, user):
    await comm.send_json_to({"command": "joined", "user": user, "info": f"{user} joined"})


async def connect_joined(name, path="/ws/clicked/alpha/", watchers=()):
    """Connect, join as ``name`` and consume the join broadcast everywhere it is delivered."""
    comm, _, _ = await connect(path)
    await join(comm, name)
    await comm.receive_json_from()
    for watcher in watchers:
        await watcher.receive_json_from()
    return comm


@database_sync_to_async
def room_names():
    return list(BingoRoom.objects.values_list("room_name", flat=True))


@database_sync_to_async
def player_names():
    return sorted(TrackPlayers.objects.values_list("username", flat=True))


@database_sync_to_async
def connection_count(name="alpha"):
    return BingoRoom.objects.get(room_name=name).connections


# --- connecting and joining ------------------------------------------------------------------


async def test_connect_creates_the_room():
    comm, connected, _ = await connect()
    assert connected and await room_names() == ["alpha"]
    await comm.disconnect()


async def test_join_is_broadcast_with_player_list_and_count():
    a, _, _ = await connect()
    b, _, _ = await connect()
    await join(a, "ann")
    for comm in (a, b):
        msg = await comm.receive_json_from()
        assert msg["command"] == "joined" and msg["user"] == "ann"
        assert msg["users_count"] == 1 and msg["all_players"] == ["ann"]
    await join(b, "bob")
    msg = await a.receive_json_from()
    assert msg["users_count"] == 2 and sorted(msg["all_players"]) == ["ann", "bob"]
    await a.disconnect()
    await b.disconnect()


@pytest.mark.parametrize("name", ["", "   ", None, 42, "n" * 51])
async def test_unusable_usernames_are_not_registered(name):
    a, _, _ = await connect()
    await a.send_json_to({"command": "joined", "user": name, "info": "x"})
    assert await a.receive_nothing()
    assert await player_names() == []
    await a.disconnect()


@pytest.mark.parametrize(
    "path", ["/ws/clicked/bad name/", "/ws/clicked/é/", "/ws/clicked/" + "r" * 51 + "/"]
)
async def test_invalid_room_names_are_rejected(path):
    comm = WebsocketCommunicator(router, path)
    connected, code = await comm.connect()
    assert connected is False and code == 4000
    assert await room_names() == []


async def test_non_object_and_unknown_messages_are_ignored():
    a, _, _ = await connect()
    await a.send_json_to([1, 2, 3])
    await a.send_json_to({"command": "nope"})
    assert await a.receive_nothing()
    await a.disconnect()


# --- gameplay messages -----------------------------------------------------------------------


async def test_click_reaches_everyone_in_the_room_as_integers():
    a = await connect_joined("ann")
    b = await connect_joined("bob", watchers=[a])
    await a.send_json_to({"command": "clicked", "dataset": "7", "dataid": 3, "user": "ann"})
    for comm in (a, b):
        assert await comm.receive_json_from() == {
            "dataset": 7, "dataid": 3, "user": "ann", "command": "clicked",
        }  # fmt: skip
    await a.disconnect()
    await b.disconnect()


async def test_rooms_are_isolated_from_each_other():
    a = await connect_joined("ann", "/ws/clicked/alpha/")
    b = await connect_joined("bob", "/ws/clicked/beta/")
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
    a = await connect_joined("ann")
    b = await connect_joined("bob", watchers=[a])
    await a.send_json_to(payload)
    assert await b.receive_nothing()
    # the room still works afterwards
    await a.send_json_to({"command": "clicked", "dataset": 5, "dataid": 5})
    assert (await b.receive_json_from())["dataset"] == 5
    await a.disconnect()
    await b.disconnect()


async def test_chat_is_relayed_trimmed_and_blank_chat_ignored():
    a = await connect_joined("ann")
    await a.send_json_to({"command": "chat", "chat": "hi", "user": "ann"})
    assert await a.receive_json_from() == {"user": "ann", "chat": "hi", "command": "chat"}
    await a.send_json_to({"command": "chat", "chat": "x" * 900, "user": "ann"})
    assert len((await a.receive_json_from())["chat"]) == 500
    await a.send_json_to({"command": "chat", "chat": "   ", "user": "ann"})
    await a.send_json_to({"command": "chat", "chat": 5, "user": "ann"})
    assert await a.receive_nothing()
    await a.disconnect()


async def test_won_is_broadcast_with_the_bingo_count():
    a = await connect_joined("ann")
    await a.send_json_to({"command": "won", "user": "ann", "bingoCount": 5})
    msg = await a.receive_json_from()
    assert msg["command"] == "won" and msg["bingoCount"] == 5 and msg["info"] == "ann won the Game"
    await a.disconnect()


# --- security: identity is bound to the connection ------------------------------------------


async def test_join_text_is_built_by_the_server_not_relayed_from_the_client():
    a, _, _ = await connect()
    await a.send_json_to(
        {"command": "joined", "user": "ann", "info": "<img src=x onerror=alert(1)>"}
    )
    assert (await a.receive_json_from())["info"] == "ann just Joined"
    await a.send_json_to({"command": "won", "user": "ann", "info": "<script>x</script>"})
    assert (await a.receive_json_from())["info"] == "ann won the Game"
    await a.disconnect()


@pytest.mark.parametrize("count", ["<b>", 7, -1, None, "9"])
async def test_bingo_count_is_coerced_to_a_small_integer_or_none(count):
    a = await connect_joined("ann")
    await a.send_json_to({"command": "won", "user": "ann", "bingoCount": count})
    assert (await a.receive_json_from())["bingoCount"] == "none"
    await a.disconnect()


async def test_connections_that_have_not_joined_cannot_chat_click_or_win():
    a, _, _ = await connect()
    b = await connect_joined("bob", watchers=[a])
    await a.send_json_to({"command": "chat", "chat": "hi", "user": "bob"})
    await a.send_json_to({"command": "clicked", "dataset": 1, "dataid": 1, "user": "bob"})
    await a.send_json_to({"command": "won", "user": "bob", "bingoCount": 5})
    assert await b.receive_nothing() and await a.receive_nothing()
    await a.disconnect()
    await b.disconnect()


async def test_messages_are_attributed_to_the_registered_name_not_the_claimed_one():
    a = await connect_joined("ann")
    b = await connect_joined("bob", watchers=[a])
    await a.send_json_to({"command": "chat", "chat": "i am bob", "user": "bob"})
    await a.send_json_to({"command": "clicked", "dataset": 2, "dataid": 2, "user": "bob"})
    for comm in (a, b):
        assert (await comm.receive_json_from())["user"] == "ann"
        assert (await comm.receive_json_from())["user"] == "ann"
    await a.disconnect()
    await b.disconnect()


async def test_a_connection_registers_exactly_one_name():
    a = await connect_joined("ann")
    await join(a, "squatter-1")
    await a.send_json_to({"command": "won", "user": "squatter-2", "bingoCount": 5})
    assert await a.receive_nothing()
    assert await player_names() == ["ann"]
    await join(a, "ann")  # repeating its own name is harmless and does not add a row
    assert (await a.receive_json_from())["users_count"] == 1
    assert await player_names() == ["ann"]
    await a.disconnect()


async def test_won_before_joining_is_ignored():
    a, _, _ = await connect()
    await a.send_json_to({"command": "won", "user": "ann", "bingoCount": 5})
    assert await a.receive_nothing() and await player_names() == []
    await a.disconnect()


async def wait_for_players(count, timeout=5.0):
    """Poll until ``count`` players are registered (joins are processed asynchronously)."""
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if len(await player_names()) >= count:
            return
        await asyncio.sleep(0.05)
    raise AssertionError(f"only {len(await player_names())} of {count} players registered")


async def test_room_has_a_player_cap():
    clients = []
    for i in range(MAX_PLAYERS_PER_ROOM):
        comm, _, _ = await connect()
        await join(comm, f"p{i}")
        clients.append(comm)
    await wait_for_players(MAX_PLAYERS_PER_ROOM)

    extra, _, _ = await connect()
    await join(extra, "one-too-many")
    await asyncio.sleep(0.3)  # give the server time to (not) register it
    assert "one-too-many" not in await player_names()
    assert len(await player_names()) == MAX_PLAYERS_PER_ROOM
    for comm in [*clients, extra]:
        await comm.disconnect()
    assert await room_names() == []


# --- leaving and cleanup ---------------------------------------------------------------------


async def test_disconnect_without_joining_does_not_crash_and_cleans_up_empty_room():
    comm, connected, _ = await connect()
    assert connected and await room_names() == ["alpha"]
    await comm.disconnect()
    assert await room_names() == []


async def test_leaving_updates_the_others_and_last_player_deletes_the_room():
    a = await connect_joined("ann")
    b = await connect_joined("bob", watchers=[a])

    await a.disconnect()
    msg = await b.receive_json_from()
    assert msg["info"] == "ann left room" and msg["users_count"] == 1
    assert msg["all_players"] == ["bob"] and await room_names() == ["alpha"]

    await b.disconnect()
    assert await room_names() == [] and await player_names() == []


async def test_a_second_connection_with_the_same_name_cannot_remove_the_first_player():
    owner = await connect_joined("ann")
    twin, _, _ = await connect()
    await join(twin, "ann")  # e.g. a second tab or a quick refresh
    await owner.receive_json_from()
    await twin.receive_json_from()
    await twin.disconnect()

    assert await owner.receive_nothing()  # ann is still here, so nobody is told she left
    assert await player_names() == ["ann"]  # the other connection's row is untouched
    assert await room_names() == ["alpha"]
    await owner.disconnect()
    assert await player_names() == [] and await room_names() == []


async def test_a_refreshing_player_stays_listed_when_the_old_connection_drops_late():
    old = await connect_joined("ann")
    fresh, _, _ = await connect()
    await join(fresh, "ann")
    await old.receive_json_from()
    await fresh.receive_json_from()
    await old.disconnect()  # the old tab's disconnect arrives after the new tab joined
    assert await fresh.receive_nothing()  # no misleading "ann left room"
    await fresh.send_json_to({"command": "chat", "chat": "still here", "user": "ann"})
    assert (await fresh.receive_json_from())["chat"] == "still here"
    assert await player_names() == ["ann"]
    await fresh.disconnect()


async def test_a_bystander_leaving_does_not_delete_a_room_others_are_in():
    player, _, _ = await connect()  # connected, has not joined yet
    bystander, _, _ = await connect()
    assert await connection_count() == 2
    await bystander.disconnect()
    assert await room_names() == ["alpha"] and await connection_count() == 1
    await join(player, "ann")  # would fail on a deleted room
    assert (await player.receive_json_from())["users_count"] == 1
    await player.disconnect()
    assert await room_names() == []


async def test_connection_count_tracks_live_connections():
    a, _, _ = await connect()
    b, _, _ = await connect()
    c, _, _ = await connect()
    assert await connection_count() == 3
    await a.disconnect()
    await b.disconnect()
    assert await connection_count() == 1
    await c.disconnect()
    assert await room_names() == []


async def test_duplicate_room_rows_do_not_break_connecting():
    await database_sync_to_async(BingoRoom.objects.create)(room_name="alpha")
    await database_sync_to_async(BingoRoom.objects.create)(room_name="alpha")
    comm, connected, _ = await connect()
    assert connected
    await join(comm, "ann")
    assert (await comm.receive_json_from())["users_count"] == 1
    await comm.disconnect()
