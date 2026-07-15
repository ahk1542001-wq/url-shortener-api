# Implementation Plan: Swoosh URL Shortener

## Steps

1. **Foundation** — Multi-user authentication (JWT), structured database, `config.py` (env-driven settings), `database.py` (context manager), clean `requirements.txt`.
2. **Refactor `main.py`** — Split the monolith into a modular FastAPI structure (`routers/`, `schemas.py`, `dependencies.py`, `analytics.py`, `utils.py`).
3. **Harden inputs** — Pydantic validation, custom code constraints (3-20 chars, alphanumeric + hyphens), block reserved words, max URL length 2048.
4. **Rate limiting + security headers** — `slowapi` at 30 req/min on `POST /api/shorten`. Add `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`.
5. **Multi-User / Profiles** — Support `users` and `profiles` tables. Allow each login account to create and switch between a maximum of five Link Tree profiles. Standalone URLs remain separate from the Link Tree workspace.
6. **PostgreSQL support** — Add `DATABASE_URL` env var, dynamic placeholders for SQLite/PostgreSQL, `_fmt_dt()` helper for datetime formatting.
7. **Frontend Evolution** — Clean single-page application using vanilla JS with separate Shortener and Link Tree workspaces, desktop sidebar navigation, sticky mobile top navigation, and a dynamic public Tree page (`/u/{username}`).
8. **Docs** — README, SPEC, PLAN, SHIP, report.md, wiki/ (architecture, patterns, decisions).
9. **Admin Operations** — Add account-owned data summaries, username updates, one-way password reset, immediate enable/disable controls, and transactional deletion while protecting the environment-managed admin identity.

## What "Good" Looks Like

- Fully modular backend in `src/routers/`.
- Every endpoint returns structured JSON errors.
- JWT token required for operations. Admin endpoints protected.
- Disabled accounts lose login and existing-token access; no endpoint exposes stored password hashes.
- Link history and multi-profile support.
- Security headers on every response.
- No secrets in repo.
- Live on Render + Neon PostgreSQL.
