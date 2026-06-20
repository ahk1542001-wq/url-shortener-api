# Swoosh — URL Shortener API

A self-hosted URL shortener built with FastAPI and SQLite. Production-hardened with input validation, rate limiting, security headers, and structured error responses.

## Setup

```bash
# Clone and enter the repo
git clone <your-repo-url>
cd url-shortener-api

# Create venv and install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy env template and edit if needed
cp .env.example .env

# Run the server
uvicorn app:app --reload --port 5000
```

Open http://localhost:5000 for the web UI.

## API Endpoints

### Shorten a URL

```bash
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/very/long/path"}'
```

Response (201):
```json
{"short_code": "aB3xYz", "original_url": "https://example.com/very/long/path"}
```

With custom code:
```bash
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "custom_code": "my-link"}'
```

### Redirect

```bash
curl -I http://localhost:5000/aB3xYz
# 302 → Location: https://example.com/very/long/path
```

### Analytics

```bash
curl http://localhost:5000/api/stats/aB3xYz
```

Response:
```json
{
  "short_code": "aB3xYz",
  "original_url": "https://example.com/very/long/path",
  "click_count": 5,
  "created_at": "2025-01-15 10:30:00",
  "last_accessed": "2025-01-15 14:22:00"
}
```

### Health Check

```bash
curl http://localhost:5000/api/health
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
| `DB_NAME` | `shortener.db` | SQLite database file path |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5000` | Server port |
| `RATE_LIMIT` | `30/minute` | Rate limit on POST /api/shorten |

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Lint
ruff check .

# Format check
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
