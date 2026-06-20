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
- [x] Database auto-creates on startup (SQLite local, Neon PostgreSQL in production)
- [x] Config loaded from environment with sensible defaults
- [x] Deployed to Render with Neon PostgreSQL (free, permanent)

### Documentation
- [x] README with setup, API docs, env vars, deploy instructions
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
| PostgreSQL support | Working (Neon free tier, permanent storage) |
| Tests | 19 passing |

## Deployment

**Stack:** Render (free hosting) + Neon PostgreSQL (free, permanent database)

**Live at:** https://url-shortener-api.onrender.com

### How to Deploy
1. Create a free Neon database at [neon.tech](https://neon.tech) → copy connection string
2. Go to [render.com](https.render.com) → New Web Service → connect GitHub repo
3. Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Add env var: `DATABASE_URL` = Neon connection string
5. Add env var: `RATE_LIMIT` = `30/minute`
6. Select Free instance → Deploy

### Rollback
- Render: redeploy previous commit from dashboard
- Neon: database is independent of hosting, data persists across deploys

## Verification After Deploy

1. `curl https://url-shortener-api.onrender.com/api/health` → `{"status": "ok"}`
2. `curl -X POST https://url-shortener-api.onrender.com/api/shorten -H "Content-Type: application/json" -d '{"url": "https://example.com"}'` → 201
3. `curl -I https://url-shortener-api.onrender.com/{code}` → 302 redirect
4. Check security headers in response
