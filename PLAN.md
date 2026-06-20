# Implementation Plan: Swoosh URL Shortener

## Steps

1. **Foundation** — Create `config.py` (env-driven settings), `database.py` (context manager), clean `requirements.txt`.
2. **Refactor app.py** — Wire in `config` + `database` modules, replace deprecated `on_event` with `lifespan`, add structured JSON errors, add `GET /api/health`.
3. **Harden inputs** — Pydantic validation, custom code constraints (3-20 chars, alphanumeric + hyphens), block reserved words, max URL length 2048.
4. **Rate limiting + security headers** — `slowapi` at 30 req/min on `POST /api/shorten`. Add `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`.
5. **Password protection** — Add `ACCESS_PASSWORD` env var, middleware to protect POST/DELETE/GET /api/links, frontend login gate with eye toggle, logout button.
6. **PostgreSQL support** — Add `DATABASE_URL` env var, dynamic placeholders for SQLite/PostgreSQL, `_fmt_dt()` helper for datetime formatting.
7. **Tests** — `tests/conftest.py` with in-memory SQLite fixtures. Test files for shorten, redirect, stats, password protection (26 tests).
8. **Docs** — README, SPEC, PLAN, SHIP, report.md, Marp slides (6 slides, 20s auto-advance).

## What "Good" Looks Like

- Every endpoint returns structured JSON errors.
- Password required for write operations and link listing.
- Link history hidden until login.
- `pytest -v` passes with 26 tests.
- `ruff check .` is clean.
- Security headers on every response.
- No secrets in repo.
- Live on Render + Neon PostgreSQL.

## Checklist

- [x] `pytest -v` passes (26 tests)
- [x] Password protection on POST/DELETE/GET /api/links
- [x] Rate limiting (30 req/min on POST /api/shorten)
- [x] Security headers on every response
- [x] Structured JSON errors everywhere
- [x] Neon PostgreSQL for production, SQLite for local dev
- [x] Frontend with login gate, eye toggle, logout button
- [x] No secrets in repo
- [x] All docs updated (README, SPEC, PLAN, SHIP, report, slides)
