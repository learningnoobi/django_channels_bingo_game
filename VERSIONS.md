# Versions

Resolved in `uv.lock` on 2026-10-29. "Previous" is the old `requirements.txt` (early 2022).

| Component | Version | Previous | Note |
|---|---|---|---|
| Python | 3.13 | 3.9/3.10 | `requires-python >=3.13` |
| Django | 5.2.18 | 4.0.2 | 5.2 is the LTS line |
| channels | 4.3.2 | 3.0.4 | |
| daphne | 4.2.3 | 3.0.2 | also listed first in `INSTALLED_APPS` so `runserver` serves ASGI |
| channels-redis | 4.3.0 | not used | new; used when `REDIS_URL` is set |
| WhiteNoise | resolved in lock | unpinned | |
| dj-database-url | 3.1.2 | 0.5.0 | |
| psycopg | 3.3.6 (binary) | psycopg2 2.9.3 | |
| Redis (CI, local check) | 7-alpine | n/a | not verified as the newest major |
| django-heroku | removed | 0.3.1 | unmaintained |

Dev: pytest, pytest-django, pytest-asyncio, ruff.
