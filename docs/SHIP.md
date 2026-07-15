# Ship Report: Swoosh URL Shortener

## Pre-Launch Checklist

### Code Quality
- [x] All tests pass (23/23)
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
- [x] JWT Authentication protection on POST/DELETE/GET /api/links and /api/shorten
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
| Multi-User Auth | Working (JWT token, user registration, centralized auth helper) |
| XSS protection | Working (escapeHtml on all user content in innerHTML) |
| Link Trees | Working (Multiple public profiles per user) |
| Link Tree Avatars | Working (Image upload to Cloudflare R2) |
| Copy short URLs | One-click copy in My Links with ✅ feedback |
| Standalone mode | Working (Links without a profile) |
| PostgreSQL support | Working (Neon free tier, permanent storage) |
| Tests | 23 passing |

## Deployment & Rehearsal

**Stack:** Render (free hosting) + Neon PostgreSQL (free, permanent database) + Cloudflare R2 (avatar storage)

**Live at:** https://swoo-sh.onrender.com

### Pre-Deployment Checklist (Database Backup & Rehearsal)
1. **Neon Backup:**
   - Before deploying, log in to the Neon console at [neon.tech](https://neon.tech).
   - Go to your database instance and create a new **Branch** or **Snapshot** (e.g. `backup-before-migration-version-1`) of your production database. This serves as an instant backup.
2. **Migration Rehearsal:**
   - Create a disposable test database or branch on Neon.
   - Run the migration script locally against the test database using:
     ```bash
     POSTGRES_TEST_URL="postgresql://user:pass@test-host/testdb" .venv311/bin/pytest -v -m postgres
     ```
   - Verify that the tables, foreign keys, sequences, and data merges complete correctly before modifying the production database.

### How to Deploy
1. Create a free Neon database at [neon.tech](https://neon.tech) → copy connection string
2. Create a Cloudflare R2 bucket → obtain endpoint, credentials, and public dev domain
3. Go to [render.com](https://render.com) → New Web Service → connect GitHub repo
4. Set runtime to Docker (uses the Dockerfile in the repository root)
5. Add env vars in Render dashboard:
   - `DATABASE_URL` = Neon connection string
   - `RATE_LIMIT` = `30/minute`
   - `JWT_SECRET` = choose a secure secret string (min 32 characters, generated with `openssl rand -hex 32`)
   - `ADMIN_PASSWORD_HASH` = bcrypt hash of your admin password
   - `R2_ENDPOINT` = Cloudflare R2 S3 Endpoint
   - `R2_ACCESS_KEY_ID` = Cloudflare R2 Access Key ID
   - `R2_SECRET_ACCESS_KEY` = Cloudflare R2 Secret Access Key
   - `R2_BUCKET` = Cloudflare R2 Bucket Name
   - `R2_PUBLIC_BASE_URL` = Cloudflare R2 Public Base URL
6. Select Free instance → Deploy

### Rollback
- Render: redeploy previous commit from dashboard
- Neon: if database migration fails, point `DATABASE_URL` back to the backup branch/snapshot created in the pre-deployment step, or restore the database state.

## Verification After Deploy

1. `curl https://swoo-sh.onrender.com/api/health` → `{"status": "ok"}`
2. Open in browser → password screen appears
3. Enter password → shorten form + My Links visible
4. Shorten a URL → short code returned
5. Click logout → back to password screen
