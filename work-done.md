# Work done: django_channels_bingo_game

Branch: `chore/modernize` (local, not pushed). Date: 2026-10-29. The repo had no uncommitted work.

## What was there
A Django 4.0 / Channels 3 bingo game with 2022 pins, Heroku settings (`django_heroku`, `ALLOWED_HOSTS = ['*']`, a committed secret key), an in-memory channel layer, only an empty `tests.py`, and a `Procfile` whose `worker` line pointed at a non-existent channel name. Tracked in git: `db.sqlite3`, 553 collected `staticfiles/`, a duplicate `mainproject/requirements.txt`. The browser code connected to a hardcoded `wss://bingoboi.herokuapp.com`.

## Changes by file
| File | Before | Change |
|---|---|---|
| `pyproject.toml`, `uv.lock`, `.python-version` | absent | New uv project, Python 3.13, Django 5.2 LTS, Channels 4, Daphne, channels-redis |
| `requirements.txt`, `runtime.txt` | 30 old pins | Exported from the lockfile; python-3.13 |
| `mainproject/requirements.txt` | duplicate of the root file | Deleted |
| `mainproject/settings.py` | hardcoded secret key, `ALLOWED_HOSTS=['*']`, `django_heroku`, `STATICFILES_STORAGE` (removed in Django 5.1) | Everything from the environment (fails fast without a secret key outside debug); `STORAGES`; `daphne` app; `REDIS_URL` selects the Redis channel layer, otherwise in-memory; HTTPS/HSTS/secure cookies when not debug |
| `mainproject/asgi.py` | called `django.setup()` by hand | Standard Channels pattern plus `AllowedHostsOriginValidator` so cross-origin WebSocket handshakes are refused (verified against a live server) |
| `bingo/consumers.py` | `disconnect` raised `DoesNotExist` if the user never joined and announced " left room" for them; `int(None)` in a group handler broke the connection of every player in the room; room name never validated (could crash `group_add`); no limit on username or chat length; the lobby resent the whole room list to everyone on every connect; leftover `print`s and unused imports | Validation of room names, usernames, cell numbers (1 to 25) and chat (500 characters); malformed input ignored; idempotent leave/cleanup; invalid rooms closed with code 4000; the lobby sends the list only to the new client, with `room_added` / `room_deleted` events for the rest. The JSON protocol the JavaScript uses is unchanged |
| `bingo/validators.py` | absent | New: shared room-name, username and cell validators |
| `bingo/views.py` | `roomExist` was `@csrf_exempt` and printed; room-name regex allowed non-ASCII names the consumer cannot use | GET-only, no print; same validator as the consumer; invalid names return HTTP 400 |
| `bingo/signals.py` | module-level channel layer, prints | Looks up the layer per call; tolerates no layer |
| `bingo/urls.py`, `routing.py`, `models.py` | formatting; `TrackPlayers` had no `__str__` | Formatted; `__str__` added |
| `bingo/apps.py` | imports signals in `ready()` | Kept with a noqa (ruff's autofix removed it once and the lobby tests caught it) |
| `static/js/bingo_socket.js`, `static/js/create_room.js` | hardcoded `wss://bingoboi.herokuapp.com/...` with a commented-out localhost alternative | Built from `window.location` (`ws://` or `wss://`, same host as the page) |
| `bingo/tests.py` | empty | Deleted; replaced by `test_consumers.py`, `test_online_rooms.py`, `test_asgi_and_views.py`, `conftest.py` (63 tests) |
| `Procfile` | `worker: python manage.py runworker channel_layer` (no such channel) | Removed that line; kept `release` and `web` |
| `.github/workflows/ci.yml`, `.env.example` | absent | New; CI runs the suite on in-memory and Redis layers |
| `.gitignore` | had basics | Also `staticfiles/`, `db.sqlite3`, `.venv`, caches |
| `db.sqlite3`, `staticfiles/` | tracked | Untracked with `git rm --cached` |
| `README.md` | one-line description and a GIF | Rewritten (GIF kept): features, config, scaling note, tests, structure |
| `VERSIONS.md`, `work-done.md` | absent | New |

## Follow-up: automated security review of the commit (fixed)
An automated review of the first commit flagged two issues in `bingo/consumers.py`; both were real:
1. **DOM XSS through the WebSocket relay (high).** The server relayed client-written `user`, `chat` and `info` strings and the browser inserted them with `innerHTML`, so one player could run script in every other player's page (this predates my changes but I had re-committed it). Fixed on both ends: `bingo_socket.js` and `create_room.js` now escape every relayed field (`esc()`, `encodeURIComponent` for links, plain-text mode for the SweetAlert message); the server no longer relays `info` (it builds "<name> just Joined" / "<name> won the Game" itself), validates `user` on chat and click messages, and coerces `bingoCount` to 0 to 5 or "none". A test fails if an unescaped `${data.info|chat|user}` returns to the JavaScript.
2. **Room and player removal by any client (medium).** Cleanup was keyed on usernames and on "no player rows", so a client that reused another player's name and disconnected removed that player, and a client that never joined could delete a room others were still connected to (their next "joined" then failed). Fixed: each connection owns only the player row it created; `BingoRoom.connections` (new field, migration `0002_room_connections`) counts live connections and the room is deleted when the last one leaves.

A second automated review of the fix flagged two more points, also fixed:
3. **Race and drift in the room counter (medium).** `get_or_create` plus a separate increment could leave a connection attached to a room that another connection had just deleted, and `get_or_create` raises when duplicate room rows exist (the name is not unique). Now the room is looked up as the oldest match (or created), the increment is a single `UPDATE`, and if it touches no row the lookup is retried; the decrement and the conditional delete (only when the count is zero) run in one transaction. A test covers duplicate room rows.
4. **Name squatting and impersonation (medium).** A connection could register unlimited names and chat or move as any other player. Identity is now bound to the connection on the server: a connection registers exactly one name (repeating it is harmless, other names are ignored), "won", chat and moves are accepted only after joining and are always attributed to that registered name whatever the client sends, and a room holds at most 20 players. Player rows are now keyed by connection (`TrackPlayers.channel_name`, migration `0003_player_channel_name`), so a second tab or a late disconnect after a page refresh removes only its own row, and the "left room" notice is sent only when no other connection still holds that name.

Remaining caveat: user names are not restricted to a character set (only length), so the safety of names depends on the client escaping them on output, which it now does.

## Test-suite finding
Running the suite repeatedly against one real Redis made tests flaky (the cached channel layer keeps connections tied to an earlier test's event loop, and old groups linger). `bingo/conftest.py` now gives each test a fresh layer and flushes it afterwards; four repeated Redis runs and two in-memory runs all pass.

## Verification (actual runs)
- `uv run pytest -q`: 63 passed on the in-memory layer; 63 passed on a real Redis 7 container (6 consecutive runs after the security fixes). Container removed afterwards.
- `uv run ruff check .` and `ruff format --check .`: clean. `makemigrations --check`: no changes. `collectstatic` succeeded. `check --deploy`: only the two optional HSTS warnings.
- Live check with `daphne`: home 200, room page 200, invalid room 400, `check_room` JSON, a two-client WebSocket round trip (join then click relayed), and a hostile `Origin` refused. Server stopped afterwards.
- Live check after the fixes: two clients over a real `daphne` server (join text built by the server, impersonation attempt attributed to the real sender).
- Not run: the full browser game UI, multiple server processes sharing Redis.

## Needs your attention
- The old Django secret key is in git history; rotate it. The old Heroku host name appeared only in the JavaScript, now removed.
- With more than one server process you must set `REDIS_URL`.
- Game rules (winning, turns) live in the browser JavaScript, so the server trusts clients about moves.
- No `LICENSE` file exists; add one if you want to publish it.
- Nothing pushed. To publish: `git push -u origin chore/modernize`
