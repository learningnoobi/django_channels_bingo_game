import pytest
from channels.testing import WebsocketCommunicator
from django.urls import reverse

from bingo.models import BingoRoom
from bingo.validators import as_cell, clean_username, is_valid_room_name
from mainproject.asgi import application


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    ("origin", "allowed"),
    [(b"http://localhost", True), (b"http://evil.example", False)],
)
async def test_websocket_origin_is_checked_against_allowed_hosts(origin, allowed):
    comm = WebsocketCommunicator(
        application, "/ws/online-rooms/", headers=[(b"origin", origin), (b"host", b"localhost")]
    )
    connected, _ = await comm.connect()
    assert connected is allowed
    if connected:
        await comm.disconnect()


def test_create_room_page(client, db):
    assert client.get(reverse("create_room")).status_code == 200


def test_bingo_page_renders_for_valid_names(client, db):
    assert client.get(reverse("bingo", args=["my-room_1"])).status_code == 200


@pytest.mark.parametrize("name", ["bad name", "é", "x" * 51, "a.b"])
def test_bingo_page_rejects_invalid_names_with_400(client, db, name):
    assert client.get(reverse("bingo", args=[name])).status_code == 400


def test_check_room_reports_existence(client, db):
    BingoRoom.objects.create(room_name="alpha")
    url = "/room/check_room/{}/"
    assert client.get(url.format("alpha")).json() == {"room_exist": True}
    assert client.get(url.format("nope")).json() == {"room_exist": False}


def test_check_room_is_get_only_and_not_csrf_exempt(client, db):
    assert client.post("/room/check_room/alpha/").status_code == 405


@pytest.mark.parametrize(
    ("name", "valid"),
    [("abc", True), ("A-b_9", True), ("", False), ("a b", False), ("é", False), ("a/b", False)],
)
def test_room_name_validator(name, valid):
    assert is_valid_room_name(name) is valid


def test_clean_username_trims_and_limits():
    assert clean_username("  ann ") == "ann"
    assert clean_username("") is None and clean_username(None) is None
    assert clean_username("x" * 51) is None and clean_username("x" * 50) == "x" * 50


def test_as_cell_accepts_only_1_to_25():
    assert as_cell("7") == 7 and as_cell(25) == 25
    assert all(as_cell(v) is None for v in (0, 26, None, "x", -1))
