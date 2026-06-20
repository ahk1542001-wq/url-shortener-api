---
marp: true
theme: default
paginate: true
auto-advance: 20
---

# Swoosh
### A Production-Hardened URL Shortener

**Live:** url-shortener-api-jcbx.onrender.com

Built with FastAPI + Neon PostgreSQL
Hardened with validation, rate limiting, security headers, 19 tests
Developed using spec-driven workflow and Addy Osmani's agent-skills

---

# Why Swoosh?

**Problem:** Long URLs are ugly, break in chats, and hide analytics.

**Solution:** Short, custom, trackable links with a clean glassmorphism UI.

**What makes it production-ready:**
- Input validation (Pydantic)
- Rate limiting (30 req/min per IP)
- Security headers on every response
- Structured JSON errors
- URL deduplication
- Click tracking + link management

---

# How I Built It

**Workflow:** Spec → Plan → Build → Review → Ship (agent-skills lifecycle)

| Step | Tool | What happened |
|------|------|---------------|
| Spec | Claude Code | Wrote structured requirements doc |
| Plan | Claude Code | Broke into 6 steps with checklist |
| Build | Claude Code | Incremental implementation, test-driven |
| MCP | mcp-server-sqlite | Live DB inspection during dev |
| Skill | url-api-contract | Enforced API consistency |
| Agent | url-tester | Autonomously verified endpoints |

---

# Architecture

```
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
- `GET /api/health` — monitoring

---

# What Got Hardened

| Area | Before | After |
|------|--------|-------|
| URL validation | `startswith("http")` | Pydantic HttpUrl, 2048 char limit |
| Custom codes | No limits | 3-20 chars, alphanumeric, reserved words blocked |
| Rate limiting | None | 30/min on POST via slowapi |
| Errors | Raw HTTPException | Structured JSON everywhere |
| Database | SQLite, open/close per request | Context managers, Neon PostgreSQL |
| Config | Hardcoded | .env-driven |
| Tests | None | 19 passing |
| Security | None | Headers on every response |

---

# What I'd Do Next

✅ Deployed — live on Render + Neon PostgreSQL (free, permanent)

**Next steps:**
- Add authentication for personal link management
- Add geographic analytics (clicks by country)
- Custom domain with HTTPS

**GitHub:** github.com/ahk1542001-wq/url-shortener-api

**Thank you!** ⭐
