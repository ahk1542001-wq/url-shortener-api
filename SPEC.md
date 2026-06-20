# Spec: Swoosh URL Shortener — Production-Hardened

## Objective

A self-hosted URL shortener API that turns long URLs into short, trackable links. Password-protected to prevent public abuse. Deployed on Render with Neon PostgreSQL for permanent free storage.

**User:** Anyone wanting a private, self-hosted URL shortener.
**Success:** The API handles bad input, resists abuse, requires a password for write operations, and runs in production for free.

## Tech Stack

- **Runtime:** Python 3.11
- **Framework:** FastAPI + Uvicorn
- **Database:** Neon PostgreSQL (production) / SQLite (local dev)
- **Validation:** Pydantic
- **Testing:** pytest (26 tests)
- **Rate limiting:** slowapi (30 req/min per IP)
- **Hosting:** Render (free tier)
- **Frontend:** Vanilla HTML/CSS/JS with glassmorphism UI

## Commands

```
Dev:     uvicorn app:app --reload --port 5000
Test:    pytest -v
Lint:    ruff check . && ruff format --check .
Format:  ruff format .
```

## Features

| Feature | Description |
|---------|-------------|
| Shorten URLs | POST /api/shorten → returns 6-char code |
| Custom codes | Optional, 3-20 chars, alphanumeric + hyphens |
| Redirect | GET /{code} → 302 redirect + click tracking |
| Link listing | GET /api/links (password protected) |
| Delete links | DELETE /api/links/{code} (password protected) |
| Deduplication | Same URL returns same code |
| Rate limiting | 30 req/min per IP on POST /api/shorten |
| Password protection | POST/DELETE/GET /api/links require X-Access-Password header |
| Security headers | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection |
| Health check | GET /api/health → {"status": "ok"} |

## Validation Rules

| Field | Rule |
|-------|------|
| `url` | Must start with `http://` or `https://`, max 2048 chars |
| `custom_code` | 3-20 chars, letters/numbers/hyphens only, not a reserved word |

**Reserved codes:** `api`, `admin`, `static`, `health`, `docs`, `openapi`

## Security

- **Password protection** — POST/DELETE/GET /api/links require `X-Access-Password` header
- **Rate limiting** — 30 req/min per IP on POST /api/shorten
- **Input validation** — Pydantic validators on all inputs
- **Parameterized SQL** — no injection vulnerabilities
- **Security headers** — on every response
- **No secrets in code** — all secrets in env vars, `.gitignore` covers `.env`, `.mcp.json`

## Testing Strategy

- **Framework:** pytest + httpx
- **Test DB:** In-memory SQLite per test (no file cleanup needed)
- **Coverage:** 26 tests covering shorten, redirect, stats, password protection
- **Naming:** `test_<what>_<condition>_<expected>`

## Boundaries

- **Always:** Run `pytest` before committing, validate all inputs, use parameterized SQL, handle DB connections with context managers
- **Ask first:** Changing the DB schema, adding new endpoints, modifying rate limits
- **Never do:** Commit secrets, use f-strings in SQL, store passwords in code
