# Ship Report: Swoosh URL Shortener

## Pre-Launch Checklist

### Code Quality
- [x] All tests pass (19/19)
- [x] Lint passes (`ruff check .`)
- [x] Format passes (`ruff format --check .`)
- [x] No TODO/FIXME comments
- [x] No `console.log` or debug `print()` statements
- [x] Error handling covers expected failure modes

### Security
- [x] No secrets in code or version control
- [x] Input validation on all endpoints (Pydantic validators)
- [x] Security headers configured (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`)
- [x] Rate limiting on POST /api/shorten (30 req/min per IP)
- [x] Structured error responses (no internal details leaked)
- [x] `.env` and `shortener.db` in `.gitignore`

### Infrastructure
- [x] Environment variables documented (`.env.example`)
- [x] Health check endpoint (`GET /api/health` → `{"status": "ok"}`)
- [x] SQLite database auto-creates on startup
- [x] Config loaded from environment with sensible defaults

### Documentation
- [x] README with setup, API docs, env vars, test commands
- [x] `.env.example` as template
- [x] `SPEC.md` with requirements
- [x] `PLAN.md` with implementation plan

## What's In This Ship

| Feature | Status |
|---------|--------|
| URL shortening | Working |
| Custom short codes | Working (3-20 chars, alphanumeric + hyphens) |
| Reserved code blocking | Working (api, admin, static, health, docs, openapi) |
| URL deduplication | Working (returns existing code for same URL) |
| Redirect (302) | Working |
| Click tracking | Working |
| Link listing | Working (`GET /api/links`) |
| Link deletion | Working (`DELETE /api/links/{code}`) |
| Health check | Working |
| Rate limiting | Working (30/min on POST /api/shorten) |
| Security headers | Working |
| Structured errors | Working |
| Input validation | Working (URL, custom code, length limits) |
| Frontend UI | Working (glass-morphism design, scrollable, delete buttons) |
| Tests | 19 passing |

## Known Limitations

- SQLite only — not suitable for multi-server deployments
- No authentication — anyone can create/delete links
- No HTTPS — needs a reverse proxy (nginx/caddy) in front
- No persistent monitoring — no error tracking or metrics collection
- Rate limit is per-process (resets on restart)

## How to Deploy

```bash
# 1. Clone the repo
git clone <repo-url>
cd url-shortener-api

# 2. Set up environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env for production settings

# 3. Run
uvicorn app:app --host 0.0.0.0 --port 8000

# 4. Behind a reverse proxy (recommended)
# Point nginx/caddy to localhost:8000
# Enable HTTPS at the proxy layer
```

## Rollback Plan

This is a greenfield deploy — rollback means stopping the server. No database migrations to reverse. The SQLite file is portable and can be backed up before any changes.

## Verification After Deploy

1. `curl http://localhost:8000/api/health` → `{"status": "ok"}`
2. `curl -X POST http://localhost:8000/api/shorten -H "Content-Type: application/json" -d '{"url": "https://example.com"}'` → 201 with short code
3. `curl -I http://localhost:8000/{code}` → 302 redirect
4. Check security headers in response
