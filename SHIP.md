# Ship Report: Swoosh URL Shortener

## Pre-Launch Checklist

### Code Quality
- [x] All tests pass (26/26)
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
- [x] Password protection on POST/DELETE/GET /api/links
- [x] XSS protection — all user-supplied content escaped via `escapeHtml()` before DOM insertion
- [x] Structured error responses (no internal details leaked)
- [x] `.env`, `.mcp.json`, and `shortener.db` in `.gitignore`

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
- [x] `slides/pitch.md` — 6 Marp slides, 20s auto-advance
- [x] `report.md` — all fields filled

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
| Password protection | Working (login gate, eye toggle, logout button) |
| XSS protection | Working (escapeHtml on all user content in innerHTML) |
| Auth failure handling | Centralized `handle401()` helper across all endpoints |
| Link history | Hidden until login |
| PostgreSQL support | Working (Neon free tier, permanent storage) |
| Tests | 26 passing |

## Deployment

**Stack:** Render (free hosting) + Neon PostgreSQL (free, permanent database)

**Live at:** https://url-shortener-api-jcbx.onrender.com

### How to Deploy
1. Create a free Neon database at [neon.tech](https://neon.tech) → copy connection string
2. Go to [render.com](https://render.com) → New Web Service → connect GitHub repo
3. Set start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Add env vars in Render dashboard:
   - `DATABASE_URL` = Neon connection string
   - `RATE_LIMIT` = `30/minute`
   - `ACCESS_PASSWORD` = choose a strong password
5. Select Free instance → Deploy

### Rollback
- Render: redeploy previous commit from dashboard
- Neon: database is independent of hosting, data persists across deploys

## Verification After Deploy

1. `curl https://url-shortener-api-jcbx.onrender.com/api/health` → `{"status": "ok"}`
2. Open in browser → password screen appears
3. Enter password → shorten form + My Links visible
4. Shorten a URL → short code returned
5. Click logout → back to password screen
