# Django Channels Multiplayer Game

Real-time multiplayer Bingo built with Django Channels and JavaScript. (Not casino bingo: it is the paper-and-pencil game played in school, where players take turns calling numbers on a 5x5 grid.)

![bingonew](https://user-images.githubusercontent.com/64244098/154678098-f24b7baf-e32b-4647-b22e-53c5cafd15a4.gif)

## Features

- Create a room or join an existing one; the lobby lists live rooms and updates as rooms open and close.
- Moves, joins, wins and chat are relayed to everyone in the room over WebSockets.
- Player list and head count update when people join or leave; an empty room is deleted automatically.
- Hardened message handling: malformed moves, bad usernames, oversized chat (capped at 500 characters) and invalid room names are rejected or ignored without affecting other players.
- WebSocket origin is checked against `ALLOWED_HOSTS`; the client connects back to whichever host served the page (`ws://` locally, `wss://` over HTTPS).

## Stack

Python 3.13, Django 5.2 LTS, Channels 4, Daphne, channels-redis, WhiteNoise; SQLite by default or PostgreSQL via `DATABASE_URL`. Versions: [VERSIONS.md](./VERSIONS.md).

## Quickstart

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/kneeraazon404/django_channels_bingo_game.git
cd django_channels_bingo_game
export DJANGO_DEBUG=true
uv sync
uv run python manage.py migrate
uv run python manage.py runserver     # Daphne serves HTTP and WebSockets
```

Open http://127.0.0.1:8000, create a room, and open the same room in a second browser tab.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DJANGO_SECRET_KEY` | required unless `DJANGO_DEBUG=true` | startup fails without it in production |
| `DJANGO_DEBUG` | `false` | debug mode |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | hosts; also the allowed WebSocket origins |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | comma-separated origins |
| `DATABASE_URL` | local SQLite file | any dj-database-url URL |
| `REDIS_URL` | unset | enables the Redis channel layer; **required with more than one server process** |

Without `REDIS_URL` an in-memory channel layer is used, which only works for a single process. With `DJANGO_DEBUG=false` the app also enables HTTPS redirect, secure cookies and HSTS.

## Deployment

`Procfile` runs migrations on release and serves with `daphne mainproject.asgi:application`. Set the variables above (including `REDIS_URL` if you scale out), then run `collectstatic --noinput`. There is no separate worker process: the old `runworker` Procfile line pointed at a non-existent channel name and was removed.

## Testing

```bash
uv run pytest -q                                              # in-memory channel layer
TEST_REDIS_URL=redis://localhost:6379 uv run pytest -q        # real Redis channel layer
uv run ruff check . && uv run ruff format --check .
```

46 tests drive real WebSocket sessions with Channels' `WebsocketCommunicator`: two-player join/click/chat flows, room isolation, malformed input, disconnect edge cases, room cleanup, the lobby's live updates, the origin check, and the HTTP views. CI runs the suite on both channel layers.

## Project structure

```
mainproject/   settings, asgi (HTTP + WebSocket routing), urls, settings_test.py
bingo/         consumers (game + lobby), routing, signals, models, views, validators, tests
static/        game CSS and JavaScript
templates/     404 page; bingo/templates/ holds the game pages
```

## License

No license file is present in this repository.
