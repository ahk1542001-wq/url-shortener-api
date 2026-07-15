# Spec: Swoosh URL Shortener — Production-Hardened

## Objective

A self-hosted URL shortener API that turns long URLs into short, trackable links. Secured with JWT authentication to prevent public abuse, and supports multi-user profiles for creating Link Trees and Standalone URLs. Deployed on Render with Neon PostgreSQL for permanent free storage.

**User:** Anyone wanting a private, self-hosted URL shortener, either for standalone links or public Link Trees.
**Success:** The API handles bad input, resists abuse, requires JWT for write operations, and runs in production for free.

## Tech Stack

- **Runtime:** Python 3.11
- **Framework:** FastAPI + Uvicorn
- **Database:** Neon PostgreSQL (production) / SQLite (local dev)
- **Validation:** Pydantic
- **Auth:** JWT (JSON Web Tokens) with bcrypt
- **Testing:** pytest
- **Rate limiting:** slowapi (30 req/min per IP)
- **Hosting:** Render (free tier)
- **Frontend:** Vanilla HTML/CSS/JS with Premium Glassmorphism UI (desktop sidebar and mobile top navigation)

## Commands

```
Dev:     uvicorn src.main:app --reload --port 8000
Test:    pytest -v
Lint:    ruff check . && ruff format --check .
Format:  ruff format .
```

## Features

| Feature | Description |
|---------|-------------|
| Multi-User Auth | POST /api/login → returns JWT token |
| Shorten URLs | POST /api/shorten → returns 6-char code |
| Custom codes | Optional, 3-20 chars, alphanumeric + hyphens |
| Link Tree Profiles | POST /api/profiles → Create and switch among up to five public link-in-bio pages |
| Edit Link Tree | PUT /api/me → Update profile bio and social links |
| Link Tree Avatars | POST /api/profiles/avatar → Upload profile picture |
| Local QR Codes | Generate QR codes in the browser without a third-party QR request |
| Standalone Links | Shorten URLs without a profile (kept private) |
| Redirect | GET /{code} → 302 redirect + click tracking |
| Link listing | GET /api/links (JWT protected) |
| Copy short URLs | One-click copy button in My Links with ✅ feedback |
| Delete links | DELETE /api/links/{code} (JWT protected) |
| Deduplication | Same URL returns same code |
| Rate limiting | 30 req/min per IP on POST /api/shorten |
| Security headers | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection |
| Health check | GET /api/health → {"status": "ok"} |

## Validation Rules

| Field | Rule |
|-------|------|
| `url` | Must start with `http://` or `https://`, max 2048 chars |
| `custom_code` | 3-20 chars, letters/numbers/hyphens only, not a reserved word |
| `username` | 3-30 chars, alphanumeric + hyphens only |

**Reserved codes:** `api`, `admin`, `static`, `health`, `docs`, `openapi`, `tree`, `u`

## Security

- **JWT Auth** — POST/DELETE/GET endpoints require `Authorization: Bearer <token>`
- **XSS protection** — all user-supplied content (short codes, URLs) escaped via `escapeHtml()` before DOM insertion
- **Rate limiting** — 30 req/min per IP on POST /api/shorten
- **Input validation** — Pydantic validators on all inputs
- **Parameterized SQL** — no injection vulnerabilities
- **Security headers** — on every response
- **Centralized auth handling** — `handle401()` helper used across all authenticated fetch calls
- **No secrets in code** — all secrets in env vars (`JWT_SECRET`, `ADMIN_PASSWORD_HASH`)

## Testing Strategy

- **Framework:** pytest + httpx
- **Test DB:** In-memory SQLite per test (no file cleanup needed)
- **Coverage:** Tests covering multi-user auth, shorten, redirect, stats, profiles
- **Naming:** `test_<what>_<condition>_<expected>`

## Boundaries

- **UI product boundary:** The frontend exposes two distinct workspaces: Shortener and Link Tree. Each login account can create, select, and manage up to five Link Tree profiles. Standalone short links remain separate from profile Link Trees.
- **Brand palette:** Olive Ink (`#2F3A1D`) is the main brand surface and Warm Lime (`#CFFF74`) is reserved for primary actions and active states.

- **Always:** Run `pytest` before committing, validate all inputs, use parameterized SQL, handle DB connections with context managers
- **Ask first:** Changing the DB schema, adding new endpoints, modifying rate limits
- **Never do:** Commit secrets, use f-strings in SQL, store passwords in code
