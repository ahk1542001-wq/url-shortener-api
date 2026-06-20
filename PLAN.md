# Hardening Plan: Swoosh URL Shortener

## Steps

1. **Foundation** — Create `config.py` (env-driven settings), `database.py` (connection context manager), clean `requirements.txt` (remove `nanoid`/`sqlalchemy`, add `slowapi`/`dotenv`/`pytest`/`ruff`).
2. **Refactor app.py** — Wire in `config` + `database` modules, replace deprecated `on_event` with `lifespan`, add structured JSON error responses, add `GET /api/health`.
3. **Harden inputs** — Pydantic `HttpUrl` validation, custom code constraints (3–20 chars, alphanumeric + hyphens), block reserved words (`api`, `admin`, `static`, `health`), max URL length 2048.
4. **Rate limiting + security headers** — `slowapi` at 30 req/min on `POST /api/shorten` only. Add `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection` via middleware.
5. **Tests** — `tests/conftest.py` with in-memory SQLite fixtures. Test files for shorten, redirect, stats. Target 90%+ route coverage.
6. **Docs** — Rewrite `README.md` with setup, API reference, env vars, test commands.

## Suggested Timeline (≈ one focused session)

| Step | Time | Output |
|------|------|--------|
| Foundation (config, db, deps) | 20 min | `config.py`, `database.py`, clean `requirements.txt` |
| Refactor + structured errors | 30 min | `app.py` uses modules, JSON errors, health check |
| Input validation + reserved codes | 20 min | Pydantic rejects bad URLs, bad codes, reserved words |
| Rate limiting + security headers | 15 min | 429 on abuse, headers on every response |
| Tests (fixtures + 3 test files) | 45 min | `pytest -v` passes, 90%+ coverage |
| README | 15 min | Setup, API docs, env reference |
| Final lint + smoke test | 10 min | `ruff check .` clean, manual curl passes |

Don't leave tests to the end. Write `conftest.py` right after the refactor, then add test cases as you harden each endpoint.

## What "Good" Looks Like

- Every endpoint returns structured JSON errors — no raw `HTTPException` leaking.
- `POST /api/shorten` rejects bad input with specific, helpful messages (not generic 422).
- Rate limiting returns 429 with the same JSON error shape — consistent everywhere.
- `pytest -v` passes with 90%+ coverage on routes — tests prove the behavior.
- `ruff check .` is clean — no lint warnings, consistent style.
- `curl -I` shows security headers on every response.
- README has working `curl` examples that actually match the API.
- No secrets in repo — `.env` in `.gitignore`, `.env.example` as template.

## Checklist (what to verify at the end)

- `pytest -v` passes with 90%+ route coverage
- `POST /api/shorten` rejects: missing scheme, empty URL, codes < 3 or > 20 chars, reserved words
- `POST /api/shorten` returns 429 after 30 requests from same IP
- `GET /{code}` returns 302 for valid, 404 for unknown
- `GET /api/stats/{code}` returns analytics or 404
- `GET /api/health` returns `{"status": "ok"}`
- All errors return `{"error": {"code": "...", "message": "..."}}`
- Security headers present on every response
- DB connections use context managers (no leaks)
- Config loaded from `.env` with `.env.example` as template
- `ruff check . && ruff format --check .` passes clean
- README documents setup, usage, endpoints, env vars
