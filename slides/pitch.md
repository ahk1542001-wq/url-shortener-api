---
marp: true
theme: default
paginate: true
auto-advance: 20
---

# Swoosh URL Shortener
## From MVP to Production-Hardened

A self-hosted URL shortener built with FastAPI & SQLite.
Hardened with validation, rate limiting, security headers, and 19 tests.
Built using spec-driven development and Addy Osmani's agent-skills.

---

# Why Swoosh?

- **Problem:** Long URLs are hard to share and track.
- **Solution:** Short, custom, trackable links with a clean UI.
- **Hardening:** Input validation, rate limiting (30/min), security headers, structured errors, deduplication.

---

# How I Built It

- **Spec → Plan → Build → Test → Review → Ship** (agent-skills lifecycle)
- Claude Code wrote the code; I drove the decisions.
- **MCP:** `mcp-server-sqlite` for live DB inspection during development.
- **Skill:** `url-api-contract` enforced API consistency.
- **Agent:** `url-tester` autonomously verified endpoints.

---

# Architecture

- `POST /api/shorten` — create short URL (with dedup + rate limit)
- `GET /<code>` — 302 redirect + click tracking
- `GET /api/links` — list all saved links
- `DELETE /api/links/<code>` — remove a link
- `GET /api/health` — health check
- **SQLite** via context managers, `.env`-driven config

---

# What Got Hardened

- **Validation:** Pydantic `HttpUrl`, 3-20 char codes, reserved word blocking
- **Rate Limiting:** 30 req/min on POST via `slowapi`
- **Security Headers:** `X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`
- **Structured Errors:** `{"error": {"code": 422, "message": "..."}}` everywhere
- **Tests:** 19 passing (shorten, redirect, stats, edge cases)

---

# What I'd Do Next

- Add authentication for personal link management
- Add geographic analytics (clicks by country)
- Deploy behind nginx/caddy with HTTPS
- **Thank you!** Check out the GitHub repo ⭐
