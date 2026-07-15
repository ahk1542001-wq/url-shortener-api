# Implementation Plan: Swoosh URL Shortener

## Steps

1. **Foundation** — Multi-user authentication (JWT), structured database, `config.py` (env-driven settings), `database.py` (context manager), clean `requirements.txt`.
2. **Refactor `main.py`** — Split the monolith into a modular FastAPI structure (`routers/`, `schemas.py`, `dependencies.py`, `analytics.py`, `utils.py`).
3. **Harden inputs** — Pydantic validation, custom code constraints (3-20 chars, alphanumeric + hyphens), block reserved words, max URL length 2048.
4. **Rate limiting + security headers** — `slowapi` at 30 req/min on `POST /api/shorten`. Add `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`.
5. **Multi-User / Profiles** — Support `users` and `profiles` tables. `users` can have multiple `profiles`. URLs are attached to either the user or a specific profile.
6. **PostgreSQL support** — Add `DATABASE_URL` env var, dynamic placeholders for SQLite/PostgreSQL, `_fmt_dt()` helper for datetime formatting.
7. **Frontend Evolution** — Clean single-page application using vanilla JS with an iOS-style toggle. Dynamic Tree Mode (`/u/{username}`).
8. **Docs** — README, SPEC, PLAN, SHIP, report.md, wiki/ (architecture, patterns, decisions).

## What "Good" Looks Like

- Fully modular backend in `src/routers/`.
- Every endpoint returns structured JSON errors.
- JWT token required for operations. Admin endpoints protected.
- Link history and multi-profile support.
- Security headers on every response.
- No secrets in repo.
- Live on Render + Neon PostgreSQL.
