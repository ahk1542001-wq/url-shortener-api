---
marp: true
theme: default
paginate: true
---

# Swoosh
### A Production-Hardened URL Shortener

**Live:** https://swoo-sh.onrender.com

Built with FastAPI + Neon PostgreSQL
Hardened with validation, rate limiting, security headers, and tests.
Developed using spec-driven workflows.

---

# Why Swoosh?

**Problem:** Long URLs are ugly, break in chats, and hide analytics.

**Solution:** Short, custom, trackable links with a clean glassmorphism UI.

**What makes it production-ready:**
- Password-protected access (show/hide toggle + logout)
- Input validation (Pydantic)
- Rate limiting (30 req/min per IP)
- Security headers on every response
- Structured JSON errors
- URL deduplication
- Click tracking + link management

---

# How I Built It

**Workflow:** Spec → Plan → Build → Review → Ship

| Step | Tool | What happened |
|------|------|---------------|
| Spec | Claude | Wrote structured requirements doc |
| Plan | Claude | Broke into 6 steps with checklist |
| Build | Claude | Incremental implementation, test-driven |
| DB   | MCP | Live DB inspection during dev |
| API  | Skill | Enforced API consistency |
| Test | Agent | Autonomously verified endpoints |

---

# Architecture

```text
Browser → FastAPI (Render) → Neon PostgreSQL
              │
        ┌─────┴─────┐
        │ Rate Limit │  30 req/min per IP
        │ Validation │  Pydantic validators
        │ Security   │  Anti-XSS, anti-clickjacking
        └───────────┘
```

**Endpoints:**
- `POST /api/shorten` — create short URL (dedup + rate limit)
- `GET /<code>` — 302 redirect + click tracking
- `GET /api/links` — list all saved links
- `DELETE /api/links/<code>` — remove a link

---

# Next Steps

✅ Deployed — live on Render + Neon PostgreSQL

**Coming up next:**
- Add user authentication for personal link management
- Add geographic analytics (clicks by country)
- Custom domain with HTTPS

**GitHub:** github.com/ahk1542001-wq/url-shortener-api

**Thank you!** ⭐
