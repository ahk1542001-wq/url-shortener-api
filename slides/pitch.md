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
Hardened with validation, rate limiting, security headers, 31 tests
Developed using spec-driven workflow and Addy Osmani's agent-skills

---

# Why Swoosh?

**Problem:** Long URLs are ugly, break in chats, and hide analytics.

**Solution:** Short, custom, trackable links with a clean glassmorphism UI.

**What makes it production-ready:**
- Multi-User JWT Authentication (Admin-created accounts)
- Link Trees (Public Profiles) & Standalone Links
- Input validation (Pydantic)
- Rate limiting (30 req/min per IP)
- Security headers on every response
- Structured JSON errors
- URL deduplication
- Click tracking + full link lifecycle management

---

# How I Built It

**Workflow:** Spec → Plan → Build → Review → Ship (agent-skills lifecycle)

| Step | Tool | What happened |
|------|------|---------------|
| Spec | Claude Code | Wrote structured requirements doc |
| Plan | Claude Code | Broke into steps and iterated for Multi-User/Trees |
| Build | Claude Code | Modular architecture with modular routers |
| MCP | mcp-server-sqlite | Live DB inspection during dev |
| Skill | url-api-contract | Enforced API consistency across routers |
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
- `POST /api/login` — User authentication (JWT)
- `POST /api/admin/register` — Admin-created accounts
- `POST /api/profiles/avatar` — Upload avatar to Cloudinary
- `POST /api/profiles` — Create link tree profiles
- `GET /api/links` — list all saved links
- `DELETE /api/links/<code>` — remove a link
- `GET /api/health` — monitoring

---

# What Got Hardened

| Area | Before | After |
|------|--------|-------|
| Architecture | Monolithic | Modular (routers, dependencies) |
| Features | Single User | Multi-User Auth + Link Trees |
| Rate limiting | None | 30/min on POST via slowapi |
| Password | Single password | Multi-User JWT Auth (Admin-Created) |
| Database | SQLite only | SQLite/PostgreSQL Migrations + Cloudinary avatars |
| Config | Hardcoded | .env-driven + startup checks |
| Tests | None | Full audit test suite passing |
| Security | None | Headers, Rate limit, Secure secrets validation |

---

# What I'd Do Next

✅ Deployed — live on Render + Neon PostgreSQL (free, permanent)

**Next steps:**
- Add authentication for personal link management
- Add geographic analytics (clicks by country)
- Custom domain with HTTPS

**GitHub:** github.com/ahk1542001-wq/url-shortener-api

**Thank you!** ⭐
