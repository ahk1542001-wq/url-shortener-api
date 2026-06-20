# Swoosh — URL Shortener API

A self-hosted URL shortener built with FastAPI. Production-hardened with input validation, rate limiting, security headers, and structured error responses. Supports both SQLite (local dev) and PostgreSQL (production via Neon).

## Setup (Local — SQLite)

```bash
git clone https://github.com/ahk1542001-wq/url-shortener-api.git
cd url-shortener-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --reload --port 5000
```

Open http://localhost:5000 for the web UI.

## Deploy to Render + Neon PostgreSQL

### 1. Create a free Neon database
1. Go to [neon.tech](https://neon.tech) and sign up (free, no credit card)
2. Create a project → copy the connection string (looks like `postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb`)

### 2. Deploy to Render
1. Go to [render.com](https://render.com) and sign up with GitHub
2. Click **New +** → **Web Service** → connect `ahk1542001-wq/url-shortener-api`
3. Set **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Add **Environment Variable**: `DATABASE_URL` = your Neon connection string
5. Add **Environment Variable**: `RATE_LIMIT` = `30/minute`
6. Select **Free** instance → **Deploy**

Your app will be live at `https://url-shortener-api.onrender.com`

## API Endpoints

### Shorten a URL

```bash
curl -X POST https://url-shortener-api.onrender.com/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/path"}'
```

Response (201):
```json
{"short_code": "aB3xYz", "original_url": "https://example.com/very/long/path", "already_exists": false}
```

### Redirect

```bash
curl -I https://url-shortener-api.onrender.com/aB3xYz
# 302 → Location: https://example.com/very/long/path
```

### List all links

```bash
curl https://url-shortener-api.onrender.com/api/links
```

### Delete a link

```bash
curl -X DELETE https://url-shortener-api.onrender.com/api/links/aB3xYz
```

### Health Check

```bash
curl https://url-shortener-api.onrender.com/api/health
# {"status": "ok"}
```

## Validation Rules

| Field | Rule |
|-------|------|
| `url` | Must start with `http://` or `https://`, max 2048 chars |
| `custom_code` | 3-20 chars, letters/numbers/hyphens only, not a reserved word |

Reserved codes: `api`, `admin`, `static`, `health`, `docs`, `openapi`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | (empty) | Neon PostgreSQL connection string. If empty, uses SQLite |
| `DB_NAME` | `shortener.db` | SQLite database file path (local dev only) |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5000` | Server port |
| `RATE_LIMIT` | `30/minute` | Rate limit on POST /api/shorten |

## Testing

```bash
pytest -v
ruff check .
ruff format --check .
```

## Error Responses

All errors return structured JSON:

```json
{"error": {"code": 422, "message": "body -> url: URL must start with http:// or https://"}}
```

| Code | Meaning |
|------|---------|
| 404 | Short code not found |
| 409 | Custom code already in use |
| 422 | Validation error |
| 429 | Rate limit exceeded |

## Security Headers

All responses include:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
