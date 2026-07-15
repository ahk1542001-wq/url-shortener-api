# Ch-3 Personal Project Report

**GitHub:** [ahk1542001-wq/url-shortener-api](https://github.com/ahk1542001-wq/url-shortener-api)

---

## What It Does

Swoosh is a self-hosted URL shortener API built with FastAPI. It features a complete multi-user authentication system where users (created by admin only, no public registration) can log in via JWT and manage their links securely. Swoosh supports two distinct modes: **Standalone Mode** (for private link shortening) and **Link Tree Mode** (for creating public, customizable profile pages that organize multiple links, with avatar images stored securely in Cloudinary). The project was hardened from an MVP to production quality using spec-driven development — adding input validation, rate limiting (30 req/min), security headers, structured error responses, deduplication (same URL returns same code), and full link lifecycle management. It supports both SQLite (local dev) and Neon PostgreSQL (free, permanent hosting). A premium glassmorphism frontend features a responsive Desktop Sidebar and Mobile Dock, adaptive Light/Dark themes, and playful empty states.

## How I Built It

I followed the **agent-skills lifecycle**: Spec → Plan → Build → Review → Ship.

1. **Spec** — Wrote a structured spec covering objectives, validation rules, testing strategy, and boundaries.
2. **Plan** — Broke the spec into 6 steps with a timeline and checklist, iteratively updating it for multi-user and Link Tree features.
3. **Build** — Incrementally implemented: foundation (config, database modules) → refactor app.py into modular routers (`auth.py`, `links.py`, `profiles.py`) → UI implementation with Desktop Sidebar & Mobile Dock → rate limiting + security headers → tests → docs.
4. **Review** — Ran a five-axis code review (correctness, readability, architecture, security, performance). Fixed UI rendering and API inconsistencies.
5. **Ship** — Verified all pre-launch checks pass (31 tests, ruff clean, no secrets, structured errors everywhere). Deployed to Render with Neon PostgreSQL (free, permanent database).

**What Claude Code did:** Wrote all the code, ran tests, fixed bugs, applied the agent-skills workflows automatically.
**What I did:** Drove the decisions — what to build, answered spec questions (rate limits, reserved codes, URL restrictions), approved the plan, reviewed the output.

## MCP / Skill / Agent

### MCP: `mcp-server-sqlite`
Used for live database inspection during development. When debugging the Link Tree data structures, I queried the database directly through MCP to verify that profiles and links correctly map to specific users.

### Skill: `url-api-contract`
Defined the API contract — endpoint shapes, status codes, error formats. This ensured consistency across all modular endpoints (`/api/auth`, `/api/links`, `/api/profiles`).

### Agent: `url-tester`
An autonomous agent that verifies endpoints against the API contract. It tests POST /api/shorten, GET /{code} redirect, GET /api/stats/{code}, and error cases. Used after each build step to catch regressions.

## Evidence

| Component | Path |
|-----------|------|
| MCP config | `.mcp.json` |
| Skill | `.claude/skills/url-api-contract/SKILL.md` |
| Agent | `.claude/agents/url-tester.md` |
| Spec | `docs/SPEC.md` |
| Plan | `docs/PLAN.md` |
| Ship report | `docs/SHIP.md` |
| Tests | `tests/test_shorten.py`, `tests/test_redirect.py` |
| Slides | `slides/pitch.md` |
| Screenshots | `screenshots/` |

## What I'd Do Next

1. **Custom domain** — Register a free domain and point it to the Render deployment.
2. **Geographic Analytics** — Add detailed geographic analytics (clicks by country).
