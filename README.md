# Swoosh — URL Shortener API

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-26%20passing-brightgreen?style=for-the-badge)
![Deploy](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

> **Like bit.ly, but you own it.** A self-hosted URL shortener with click tracking, rate limiting, and a glassmorphism UI.

🔗 **Live:** [url-shortener-api-jcbx.onrender.com](https://url-shortener-api-jcbx.onrender.com)

---

## What Is This?

Swoosh is a self-hosted URL shortener — like bit.ly, but you own it. Paste a long URL, get a short code back. Share the short link anywhere. When someone clicks it, they get redirected to the original URL while Swoosh tracks how many times it was clicked.

**Live demo:** https://url-shortener-api-jcbx.onrender.com

## Why I Built This

Long URLs are ugly and hard to share. They break in emails, get truncated in chat, and look unprofessional. Swoosh solves this by turning any URL into a short, clean link you can share anywhere — with built-in analytics to track engagement.

This project was built as part of the **Vibe Code Tours** cohort — a hands-on course on driving AI coding agents with real-world projects. It demonstrates spec-driven development, agent skills, MCP integration, and production deployment.

## What It Does

| Feature | Description |
|---------|-------------|
| **Shorten URLs** | Paste a long URL → get a 6-character short code |
| **Custom codes** | Choose your own short code (e.g., `swoo.sh/my-event`) |
| **Redirect** | Visit the short link → 302 redirect to the original URL |
| **Click tracking** | Every redirect increments a click counter |
| **Link listing** | See all your shortened links in one place |
| **Delete links** | Remove links you no longer need |
| **Deduplication** | Shorten the same URL twice → get the same code back |
| **Rate limiting** | 30 requests per minute per IP to prevent abuse |
| **Security headers** | Every response includes anti-XSS, anti-clickjacking headers |
| **Input validation** | Rejects bad URLs, short codes with special chars, reserved words |
| **Password protection** | Password required for POST/DELETE/GET /api/links, login gate with show/hide toggle, logout button |
| **XSS protection** | All user content escaped before DOM insertion (`escapeHtml()`) |
| **Link history** | My Links section visible only after login |
| **Health check** | `GET /api/health` returns `{"status": "ok"}` for monitoring |

## How It Works

```
  ┌─────────────────────────────────────────────────────────┐
  │  Paste your long URL                                     │
  │  https://example.com/very/long/path/to/something?foo=bar  │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Get a short link                                        │
  │  https://url-shortener-api-jcbx.onrender.com/aB3xYz      │
  │                                                          │
  │  [Copy]                                                  │
  └────────────────────────┬────────────────────────────────┘
                           │
                           ▼
  ┌─────────────────────────────────────────────────────────┐
  │  Someone clicks it → 302 redirect to original URL        │
  │  Click count: 1 → 2 → 3 → ...                           │
  └─────────────────────────────────────────────────────────┘
```

## Tech Stack

- **Backend:** Python 3.11 + FastAPI
- **Database:** Neon PostgreSQL (free, permanent) — falls back to SQLite for local dev
- **Hosting:** Render (free tier)
- **Frontend:** Vanilla HTML/CSS/JS with glassmorphism, password gate (eye toggle), logout button, links hidden until login
- **Testing:** pytest (26 tests passing)
- **Linting:** Ruff
- **MCP:** mcp-server-sqlite for live database inspection during development
- **Agent Skills:** Addy Osmani's agent-skills for spec-driven development workflow

## Architecture

```
                    ┌──────────────────┐
                    │     Browser      │
                    │  (Glassmorphism  │
                    │      UI)         │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   Render (Free)  │
                    │                  │
                    │  ┌────────────┐  │
                    │  │  FastAPI   │  │
                    │  │            │  │
                    │  │ • Rate Limit│  │
                    │  │ • Validate │  │
                    │  │ • Headers  │  │
                    │  └─────┬──────┘  │
                    │        │         │
                    └────────┼─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Neon PostgreSQL  │
                    │  (Free, Forever) │
                    │                  │
                    │ • URLs table     │
                    │ • Click tracking │
                    │ • Deduplication  │
                    └──────────────────┘
```

## API Endpoints

### Shorten a URL

```bash
curl -X POST https://url-shortener-api-jcbx.onrender.com/api/shorten \
  -H "Content-Type: application/json" \
  -H "X-Access-Password: your-password" \
  -d '{"url": "https://example.com/very/long/path"}'
```

Response:
```json
{"short_code": "aB3xYz", "original_url": "https://example.com/very/long/path", "already_exists": false}
```

### Use a custom code

```bash
curl -X POST https://url-shortener-api-jcbx.onrender.com/api/shorten \
  -H "Content-Type: application/json" \
  -H "X-Access-Password: your-password" \
  -d '{"url": "https://example.com", "custom_code": "my-link"}'
```

### Visit a short link (no auth needed)

```
https://url-shortener-api-jcbx.onrender.com/aB3xYz
→ 302 redirect to https://example.com/very/long/path
```

### List all links

```bash
curl https://url-shortener-api-jcbx.onrender.com/api/links \
  -H "X-Access-Password: your-password"
```

### Delete a link

```bash
curl -X DELETE https://url-shortener-api-jcbx.onrender.com/api/links/aB3xYz \
  -H "X-Access-Password: your-password"
```

### Health check (no auth needed)

```bash
curl https://url-shortener-api-jcbx.onrender.com/api/health
# {"status": "ok"}
```

## Run Locally

```bash
# Clone
git clone https://github.com/ahk1542001-wq/url-shortener-api.git
cd url-shortener-api

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create your .env file
cat > .env << EOF
DB_NAME=shortener.db
HOST=0.0.0.0
PORT=5000
RATE_LIMIT=30/minute
ACCESS_PASSWORD=choose-a-strong-password
EOF

# Start the server
uvicorn app:app --reload --port 5000
```

Open http://localhost:5000 — enter your password to start shortening URLs.

## Deploy Your Own

### 1. Create a free Neon database

1. Go to [neon.tech](https://neon.tech) → sign up (free, no credit card)
2. Create a project → copy the connection string

### 2. Deploy to Render

1. Go to [render.com](https://render.com) → sign up with GitHub
2. **New +** → **Web Service** → connect your fork of this repo
3. **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables** (set these in the Render dashboard):
   - `DATABASE_URL` — your Neon connection string
   - `RATE_LIMIT` — `30/minute`
   - `ACCESS_PASSWORD` — choose a strong password
5. Select **Free** → **Deploy**

## Validation Rules

| Field | Rule |
|-------|------|
| `url` | Must start with `http://` or `https://`, max 2048 characters |
| `custom_code` | 3-20 characters, letters/numbers/hyphens only, not a reserved word |

**Reserved codes:** `api`, `admin`, `static`, `health`, `docs`, `openapi`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | (empty) | Neon PostgreSQL connection string. If empty, uses SQLite |
| `DB_NAME` | `shortener.db` | SQLite database file path (local dev only) |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `5000` | Server port |
| `RATE_LIMIT` | `30/minute` | Rate limit on POST /api/shorten |
| `ACCESS_PASSWORD` | (required) | Password required for POST/DELETE/GET /api/links requests |

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

## Security

- **Input validation** on all endpoints (Pydantic)
- **Parameterized SQL** — no injection vulnerabilities
- **Rate limiting** — 30 req/min per IP on POST /api/shorten
- **Password protection** — POST/DELETE/GET /api/links require `X-Access-Password` header
- **XSS protection** — all user-supplied content escaped via `escapeHtml()` before DOM insertion
- **Centralized auth handling** — `handle401()` helper consolidates auth failure logic across all fetch calls
- **Security headers** on every response:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
- **No secrets in code** — `.env` and `.mcp.json` in `.gitignore`

## Testing

```bash
# Run all tests
pytest -v

# Lint
ruff check .

# Format check
ruff format --check .
```

## Project Structure

```
url-shortener-api/
├── app.py              → Main FastAPI application (routes, models, middleware)
├── config.py           → Environment variable loading
├── database.py         → PostgreSQL + SQLite connection management
├── requirements.txt    → Python dependencies
├── Dockerfile          → Docker config for Render deployment
├── render.yaml         → Render service configuration
├── .env.example        → Environment variable template
├── .mcp.json           → MCP server config (sqlite + render)
├── SPEC.md             → Project specification
├── PLAN.md             → Implementation plan
├── SHIP.md             → Deployment checklist
├── slides/pitch.md     → Marp presentation slides
├── tests/
│   ├── conftest.py     → Test fixtures
│   ├── test_shorten.py → Shorten endpoint tests
│   ├── test_redirect.py → Redirect endpoint tests
│   ├── test_stats.py   → Stats endpoint tests
│   └── test_password.py → Password protection tests
├── static/
│   ├── index.html      → Frontend UI
│   ├── script.js       → Frontend logic
│   └── style.css       → Glassmorphism styles
└── .claude/
    ├── skills/url-api-contract/SKILL.md → API contract skill
    └── agents/url-tester.md             → Test automation agent
```

## License

MIT
