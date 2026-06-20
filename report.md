# Ch-3 Personal Project Report

**GitHub:** [ahk1542001-wq/url-shortener-api](https://github.com/ahk1542001-wq/url-shortener-api)

---

## What It Does

Swoosh is a self-hosted URL shortener API built with FastAPI. Users enter a password to access the app, paste a long URL, and get a short code back. Visiting that short code redirects to the original URL while tracking click counts. The project was hardened from an MVP to production quality using spec-driven development — adding input validation, rate limiting (30 req/min), security headers, structured error responses, deduplication (same URL returns same code), link listing, deletion, and password protection with a show/hide toggle. It supports both SQLite (local dev) and Neon PostgreSQL (free, permanent hosting). A glassmorphism frontend lets users shorten links, copy them, and manage their saved links behind a password gate. Link history is hidden until the user logs in, and a logout button clears the session.

## How I Built It

I followed the **agent-skills lifecycle**: Spec → Plan → Build → Review → Ship.

1. **Spec** — Wrote a structured spec covering objectives, validation rules, testing strategy, and boundaries.
2. **Plan** — Broke the spec into 6 steps with a timeline and checklist.
3. **Build** — Incrementally implemented: foundation (config, database modules) → refactor app.py → input validation → rate limiting + security headers → tests → docs.
4. **Review** — Ran a five-axis code review (correctness, readability, architecture, security, performance). Fixed conftest duplication and a crash on missing static files.
5. **Ship** — Verified all pre-launch checks pass (26 tests, ruff clean, no secrets, structured errors everywhere). Deployed to Render with Neon PostgreSQL (free, permanent database).

**What Claude Code did:** Wrote all the code, ran tests, fixed bugs, applied the agent-skills workflows automatically.
**What I did:** Drove the decisions — what to build, answered spec questions (rate limits, reserved codes, URL restrictions), approved the plan, reviewed the output.

## MCP / Skill / Agent

### MCP: `mcp-server-sqlite`
Used for live database inspection during development. When debugging the deduplication feature, I queried the database directly through MCP to verify that the same URL returned the same short code instead of creating duplicates.

### Skill: `url-api-contract`
Defined the API contract — endpoint shapes, status codes, error formats. This ensured consistency across all endpoints. When I added the `/api/links` and `DELETE /api/links/{code}` endpoints, the skill guided the response format.

### Agent: `url-tester`
An autonomous agent that verifies endpoints against the API contract. It tests POST /api/shorten, GET /{code} redirect, GET /api/stats/{code}, and error cases. Used after each build step to catch regressions.

## Evidence

| Component | Path |
|-----------|------|
| MCP config | `.mcp.json` |
| Skill | `.claude/skills/url-api-contract/SKILL.md` |
| Agent | `.claude/agents/url-tester.md` |
| Spec | `SPEC.md` |
| Plan | `PLAN.md` |
| Ship report | `SHIP.md` |
| Tests | `tests/test_shorten.py`, `tests/test_redirect.py`, `tests/test_stats.py`, `tests/test_password.py` |
| Slides | `slides/pitch.md` |

## What I'd Do Next

1. **Authentication** — Add user accounts so people can manage their own links privately.
2. **Custom domain** — Register a free domain at DigitalPlat and point it to the Render deployment.
