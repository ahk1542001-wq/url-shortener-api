# Swoosh — URL Shortener API

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Deploy](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)

> **Like bit.ly, but you own it.** A self-hosted URL shortener with click tracking, rate limiting, and a premium glassmorphism UI.

🔗 **Live:** [swoo-sh.onrender.com](https://swoo-sh.onrender.com)

---

## What Is This?

Swoosh is a self-hosted URL shortener — like bit.ly, but you own it. Paste a long URL, get a short code back. Share the short link anywhere. When someone clicks it, they get redirected to the original URL while Swoosh tracks how many times it was clicked.

With the latest update, Swoosh supports **multi-user accounts** and **Link Trees**, allowing users to manage multiple public profile pages or create standalone URLs disconnected from any public profile.

## What It Does

| Feature | Description |
|---------|-------------|
| **Multi-User Accounts** | Login securely with username/password backed by JWT authentication. (Accounts are created by admin only; no public registration). |
| **Link Tree Mode** | Create public Link Tree pages (`/u/{username}`) complete with customizable bios, social links, and avatars. |
| **Standalone Mode** | Create standard short URLs. |
| **Shorten URLs** | Paste a long URL → get a 6-character short code. |
| **Custom codes** | Choose your own short code (e.g., `swoo.sh/my-event`). |
| **Click tracking** | Every redirect increments a click counter, with basic analytics. |
| **Premium UI/UX** | Desktop Sidebar, Mobile Dock, Adaptive Themes (Light/Dark mode), fluid animations, and playful empty states. |
| **Rate limiting** | 30 requests per minute per IP to prevent abuse. |
| **Security headers** | Every response includes anti-XSS, anti-clickjacking headers. |
| **Input validation** | Rejects bad URLs, short codes with special chars, reserved words. |

## Tech Stack

- **Backend:** Python 3.11 + FastAPI
- **Authentication:** JWT (JSON Web Tokens) with bcrypt password hashing
- **Database:** Neon PostgreSQL (free, permanent) — falls back to SQLite for local dev
- **Hosting:** Render (free tier)
- **Frontend:** Vanilla HTML/CSS/JS with glassmorphism, responsive Sidebar/Dock, Adaptive Themes

## API Endpoints

### Login & Get Token
```bash
curl -X POST https://swoo-sh.onrender.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```
Response: `{"token": "ey..."}`

### Shorten a URL (Standalone)
```bash
curl -X POST https://swoo-sh.onrender.com/api/shorten \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"url": "https://example.com/very/long/path"}'
```

### Create Link Tree Profile
```bash
curl -X POST https://swoo-sh.onrender.com/api/profiles \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -d '{"username": "my-profile"}'
```

### Update Link Tree Profile (Active Profile)
```bash
curl -X PUT https://swoo-sh.onrender.com/api/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-token>" \
  -H "X-Active-Profile: my-profile" \
  -d '{"username": "my-profile", "bio": "Hello world", "social_links": [{"platform": "twitter", "url": "https://twitter.com/my-profile", "title": "Twitter"}]}'
```

### Upload Link Tree Avatar
```bash
curl -X POST https://swoo-sh.onrender.com/api/profiles/avatar \
  -H "Authorization: Bearer <your-token>" \
  -H "X-Active-Profile: my-profile" \
  -F "file=@/path/to/avatar.jpg"
```

### Visit a short link (no auth needed)
```
https://swoo-sh.onrender.com/aB3xYz
→ 302 redirect to https://example.com/very/long/path
```

### View a Link Tree
```
https://swoo-sh.onrender.com/u/my-profile
→ Renders a public link tree page for that profile.
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

# Create your .env file, then fill in the generated values
cp .env.example .env
openssl rand -hex 32
python -c "from passlib.hash import bcrypt; print(bcrypt.hash('YOUR_STRONG_ADMIN_PASSWORD'))"

# In .env, set JWT_SECRET to the first command's output and
# ADMIN_PASSWORD_HASH to the second command's output.

# Start the server
uvicorn src.main:app --reload --port 8000
```

Open `http://localhost:8000` to interact with the web interface.

## Deploy Your Own

### 1. Create a free Neon database

1. Go to [neon.tech](https://neon.tech) → sign up (free, no credit card)
2. Create a project → copy the connection string

### 2. Deploy to Render

1. Go to [render.com](https://render.com) → sign up with GitHub
2. **New +** → **Web Service** → connect your fork of this repo
3. **Start Command:** `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables** (set these in the Render dashboard):
   - `DATABASE_URL` — your Neon connection string
   - `RATE_LIMIT` — `30/minute`
   - `JWT_SECRET` — choose a secure string
   - `ADMIN_PASSWORD_HASH` — your generated bcrypt hash
5. Select **Free** → **Deploy**

## Validation Rules

| Field | Rule |
|-------|------|
| `url` | Must start with `http://` or `https://`, max 2048 characters |
| `custom_code` | 3-20 characters, letters/numbers/hyphens only, not a reserved word |

**Reserved codes:** `api`, `admin`, `static`, `health`, `docs`, `openapi`, `tree`, `u`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | (empty) | Neon PostgreSQL connection string. If empty, uses SQLite |
| `DB_NAME` | `shortener.db` | SQLite database file path (local dev only) |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `RATE_LIMIT` | `30/minute` | Rate limit on POST /api/shorten |
| `JWT_SECRET` | (required) | Secret key used to sign JWT tokens |
| `ADMIN_PASSWORD_HASH`| (required) | bcrypt hash for the default admin user |
| `R2_ENDPOINT` | (empty) | Cloudflare R2 S3 API Endpoint |
| `R2_ACCESS_KEY_ID` | (empty) | Cloudflare R2 Access Key ID |
| `R2_SECRET_ACCESS_KEY` | (empty) | Cloudflare R2 Secret Access Key |
| `R2_BUCKET` | (empty) | Cloudflare R2 Bucket Name |
| `R2_PUBLIC_BASE_URL` | (empty) | Cloudflare R2 Public Base URL for serving uploaded avatars |

## Error Responses

All errors return structured JSON:

```json
{"error": {"code": 422, "message": "body -> url: URL must start with http:// or https://"}}
```

| Code | Meaning |
|------|---------|
| 401 | Unauthorized / Invalid JWT token |
| 404 | Short code not found |
| 409 | Custom code already in use |
| 422 | Validation error |
| 429 | Rate limit exceeded |

## Project Structure

```
url-shortener-api/
├── src/
│   ├── main.py         → Main FastAPI application (app init, middleware, static files)
│   ├── routers/        → API endpoint modules
│   │   ├── auth.py     → Authentication routes
│   │   ├── admin.py    → Admin user management
│   │   ├── profiles.py → Profile and link tree routes
│   │   ├── links.py    → URL shortening and analytics routes
│   │   └── redirects.py→ Core redirect routes
│   ├── schemas.py      → Pydantic models for validation
│   ├── dependencies.py → Auth logic, rate limiting, and dependencies
│   ├── config.py       → Environment variable loading
│   ├── database.py     → PostgreSQL + SQLite connection management
│   ├── analytics.py    → Background task for analytics flush
│   └── utils.py        → Helper utilities
├── docs/
│   ├── SPEC.md         → Project specification
│   ├── PLAN.md         → Implementation plan
│   └── SHIP.md         → Deployment checklist
├── wiki/               → Architecture and pattern documentation
├── screenshots/        → Project screenshots and assets
├── slides/             → Presentation materials
├── tests/
│   ├── conftest.py     → Test fixtures
│   ├── test_shorten.py → Shorten endpoint tests
│   └── test_redirect.py → Redirect endpoint tests
├── static/
│   ├── index.html      → Frontend UI
│   ├── script.js       → Frontend logic
│   └── style.css       → Glassmorphism styles
└── .env.example        → Environment variable template
```

## License

MIT
