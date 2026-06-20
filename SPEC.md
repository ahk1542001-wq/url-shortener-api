# Spec: Harden URL Shortener API to Production Quality

## Objective

Take the existing "Swoosh" URL shortener MVP (FastAPI + SQLite + vanilla frontend) and harden it for production use. The app works — we're adding the safety nets, validation, tests, and operational maturity that separate a demo from something you'd deploy.

**User:** Anyone wanting a self-hosted URL shortener.
**Success looks like:** The API handles bad input gracefully, resists abuse, has test coverage, and can be deployed with confidence.

## Tech Stack

- **Runtime:** Python 3.11+
- **Framework:** FastAPI 0.115.0 + Uvicorn 0.30.6
- **Database:** SQLite (via `sqlite3` stdlib — no ORM needed at this scale)
- **Validation:** Pydantic 2.9.2
- **Testing:** `pytest` + `pytest-asyncio` + `httpx` (TestClient for FastAPI)
- **Rate limiting:** `slowapi` (Leaky Bucket algorithm)
- **Environment:** `python-dotenv` for `.env` loading

## Commands

```
Dev:     uvicorn app:app --reload --port 5000
Test:    pytest -v
Lint:    ruff check . && ruff format --check .
Format:  ruff format .
```

## Project Structure

```
url-shortener-api/
├── app.py                  → Main FastAPI application
├── config.py               → Settings from environment variables
├── database.py             → SQLite connection management
├── models.py               → Pydantic request/response models
├── routes/
│   ├── __init__.py
│   ├── shorten.py          → POST /api/shorten
│   ├── redirect.py         → GET /{code}
│   └── stats.py            → GET /api/stats/{code}
├── tests/
│   ├── __init__.py
│   ├── conftest.py         → Fixtures (test client, temp DB)
│   ├── test_shorten.py     → Shorten endpoint tests
│   ├── test_redirect.py    → Redirect endpoint tests
│   └── test_stats.py       → Stats endpoint tests
├── static/                 → Frontend (existing, unchanged)
├── requirements.txt        → Dependencies (updated)
├── .env.example            → Template for environment config
└── SPEC.md                 → This file
```

## Code Style

- **Formatter/Linter:** Ruff (replaces Black + isort + flake8)
- **Line length:** 88 chars (Ruff default)
- **Imports:** Sorted by Ruff, stdlib → third-party → local
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes
- **Type hints:** Required on all function signatures

```python
# Good: typed, descriptive, single responsibility
def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))
```

## Testing Strategy

- **Framework:** pytest + httpx AsyncClient
- **Test DB:** In-memory SQLite (`:memory:`) per test session — no file cleanup needed
- **Coverage target:** 90%+ on routes (aim for 100% on business logic)
- **Test levels:**
  - Unit: `generate_short_code`, validation logic
  - Integration: Each API endpoint via httpx
  - Edge cases: Empty input, duplicate codes, long URLs, special characters

**Test naming:** `test_<what>_<condition>_<expected>`

```python
def test_shorten_valid_url_returns_201():
    ...

def test_shorten_missing_scheme_returns_422():
    ...

def test_redirect_unknown_code_returns_404():
    ...
```

## Boundaries

- **Always:** Run `pytest` before committing, validate all inputs via Pydantic, use parameterized SQL queries, handle DB connections with context managers
- **Ask first:** Changing the DB schema, adding new endpoints, modifying rate limit thresholds, switching from SQLite
- **Never do:** Commit `.env` or `shortener.db`, use f-strings in SQL, store secrets in code, disable CSRF protection on the frontend

## What's Being Fixed (Gap Analysis)

| Area | Current State | Target State |
|------|--------------|-------------|
| **URL Validation** | `startswith("http")` check | Pydantic `HttpUrl` + scheme validation |
| **Custom Code Validation** | No length/char limits | 3-20 chars, alphanumeric + hyphens only |
| **Rate Limiting** | None | 30 req/min per IP on `/api/shorten` |
| **Error Responses** | Raw HTTPException | Structured `{"error": {"code": "...", "message": "..."}}` |
| **DB Connections** | Open/close per request | Context manager with proper cleanup |
| **Config** | Hardcoded values | `.env`-driven via `config.py` |
| **Tests** | None | pytest suite with 90%+ route coverage |
| **Health Check** | None | `GET /api/health` returns `{"status": "ok"}` |
| **Security Headers** | None | `X-Content-Type-Options`, `X-Frame-Options` via middleware |
| **Logging** | None | Structured logging for errors and slow requests |
| **FastAPI Startup** | Deprecated `@app.on_event` | Modern `lifespan` context manager |
| **README** | One-liner | Usage docs, API reference, env config |

## Success Criteria

- [ ] `pytest -v` passes with 90%+ coverage on routes
- [ ] `POST /api/shorten` rejects: missing scheme, empty URL, codes < 3 or > 20 chars, non-alphanumeric codes
- [ ] `POST /api/shorten` returns 429 after 30 requests from same IP in 1 minute
- [ ] `GET /{code}` returns 302 for valid codes, 404 for unknown
- [ ] `GET /api/stats/{code}` returns structured analytics or 404
- [ ] `GET /api/health` returns `{"status": "ok"}`
- [ ] All errors return structured JSON `{"error": {"code": "...", "message": "..."}}`
- [ ] DB connections are managed via context managers (no leaked connections)
- [ ] Config is loaded from `.env` (with `.env.example` as template)
- [ ] `ruff check . && ruff format --check .` passes clean
- [ ] README documents setup, usage, and API endpoints

## Decisions (Resolved)

1. **Rate limits:** 30 req/min per IP on `POST /api/shorten` only. Redirects and stats are unthrottled (read-only).
2. **Reserved codes:** Block `api`, `admin`, `static`, `health` and any other codes that conflict with routes.
3. **URL restrictions:** None — accept any valid HTTP/HTTPS URL. Keep it simple.
4. **Migrations:** `ALTER TABLE` is fine for SQLite. No migration tool needed.
