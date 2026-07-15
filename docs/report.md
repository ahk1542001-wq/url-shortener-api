# Ch-3 Personal Project Report

**GitHub:** [ahk1542001-wq/url-shortener-api](https://github.com/ahk1542001-wq/url-shortener-api)

---

## What It Does

Swoosh is an open-source URL shortener and link-in-bio builder built with FastAPI. Users (created by an administrator; no public registration) authenticate with JWT and work in two distinct areas: **Standalone Shortener** for private link management and **Link Tree** for public profile pages. Each account can create and switch among up to five Link Tree profiles with a bio, avatar, social links, public URL, visit counter, and local QR code. The project was hardened from an MVP with input validation, rate limiting (30 req/min), security headers, structured errors, URL deduplication, migrations, and full link lifecycle management. It supports SQLite for local development, Neon PostgreSQL for production, and Cloudinary for avatar storage. The responsive Olive Ink and Warm Lime interface uses a desktop sidebar and sticky mobile top navigation.

## How I Built It

I followed the **agent-skills lifecycle**: Spec → Plan → Build → Review → Ship.

1. **Spec** — Wrote a structured spec covering objectives, validation rules, testing strategy, and boundaries.
2. **Plan** — Broke the spec into 6 steps with a timeline and checklist, iteratively updating it for multi-user and Link Tree features.
3. **Build** — Incrementally implemented: foundation (config, database modules) → modular routers (`auth.py`, `admin.py`, `links.py`, `profiles.py`) → separate Shortener and Link Tree workspaces → desktop sidebar and mobile top navigation → local QR generation → rate limiting + security headers → tests → docs.
4. **Review** — Ran a five-axis code review (correctness, readability, architecture, security, performance). Fixed UI rendering and API inconsistencies.
5. **Ship** — Verified the local suite passes (73 passed and one optional PostgreSQL test skipped), Ruff and JavaScript checks are clean, and no secrets are included. The reference deployment uses Render with Neon PostgreSQL and Cloudinary.

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

1. **Custom domain** — Point a project-owned domain to the Render deployment.
2. **Geographic Analytics** — Add privacy-conscious country-level click analytics.
3. **Accessibility audit** — Extend keyboard, screen-reader, and contrast testing across every workflow.
