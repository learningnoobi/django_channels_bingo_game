import re

# Room names end up in channel-layer group names, which must be ASCII letters, digits, hyphens,
# underscores or periods (and under 100 characters); BingoRoom.room_name is limited to 50.
ROOM_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,50}$")
MAX_USERNAME_LENGTH = 50  # TrackPlayers.username
MAX_CHAT_LENGTH = 500


def is_valid_room_name(name: str) -> bool:
    return bool(ROOM_NAME_RE.fullmatch(name or ""))


def clean_username(name) -> str | None:
    """Return a trimmed username, or None if it is missing or too long for the database."""
    if not isinstance(name, str):
        return None
    name = name.strip()
    if not name or len(name) > MAX_USERNAME_LENGTH:
        return None
    return name


def as_cell(value) -> int | None:
    """Convert a bingo cell number from the client to an int in 1..25, else None."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 1 <= number <= 25 else None
