# Ch-3 Personal Project Report

**GitHub:** [ahk1542001-wq/url-shortener-api](https://github.com/ahk1542001-wq/url-shortener-api)

---

## What It Does

Swoosh is an open-source URL shortener and link-in-bio builder built with FastAPI. Users (created by an administrator; no public registration) authenticate with JWT and work in two distinct areas: **Standalone Shortener** for private link management and **Link Tree** for public profile pages. Each account can create and switch among up to five Link Tree profiles with a bio, avatar, social links, public URL, visit counter, and local QR code. Administrators can review an account's owned profile/link totals, rename it, reset its password, disable access, or delete its application data without ever viewing the existing one-way bcrypt password. The project was hardened from an MVP with input validation, rate limiting (30 req/min), security headers, structured errors, URL deduplication, migrations, and full link lifecycle management. It supports SQLite for local development, Neon PostgreSQL for production, and Cloudinary for avatar storage. The responsive Olive Ink and Warm Lime interface uses a desktop sidebar and sticky mobile top navigation.

## How I Built It

I followed the **agent-skills lifecycle**: Spec → Plan → Build → Review → Ship.

1. **Spec** — Wrote a structured spec covering objectives, validation rules, testing strategy, and boundaries.
2. **Plan** — Broke the spec into 6 steps with a timeline and checklist, iteratively updating it for multi-user and Link Tree features.
3. **Build** — Incrementally implemented: foundation (config, database modules) → modular routers (`auth.py`, `admin.py`, `links.py`, `profiles.py`) → secure admin account management → separate Shortener and Link Tree workspaces → desktop sidebar and mobile top navigation → local QR generation → rate limiting + security headers → tests → docs.
4. **Review** — Ran a five-axis code review (correctness, readability, architecture, security, performance). Fixed UI rendering and API inconsistencies.
5. **Ship** — Verified the local suite passes (80 passed and one optional PostgreSQL test skipped), Ruff and JavaScript checks are clean, and no secrets are included. The reference deployment uses Render with Neon PostgreSQL and Cloudinary. Render automatically deploys the `main` branch and checks `/api/health` before marking a release live.

**How AI-assisted development was used:** Coding agents helped inspect the repository, implement narrow changes, run automated checks, identify migration and UI regressions, and keep the documentation synchronized. Every suggested change was reviewed in the application and through Git before it was merged.

**What I did:** I defined the product direction, answered specification questions (rate limits, reserved codes, URL restrictions, profile limits, and visual identity), manually reviewed desktop and mobile workflows, selected the final behavior, and approved each release.

## Technology and Service Choices

| Area | Choice | Why It Was Used |
|---|---|---|
| Backend | FastAPI + Python 3.11 | Typed request validation, modular routing, and automatic API documentation |
| Frontend | Vanilla HTML, CSS, and JavaScript | A small self-contained interface without a separate build pipeline |
| Local database | SQLite | Zero-service local setup and fast disposable testing |
| Production database | Neon PostgreSQL | Managed PostgreSQL with branching for migration rehearsal and recovery |
| Authentication | JWT + bcrypt | Expiring bearer sessions and one-way password storage |
| Avatar media | Cloudinary | Persistent image storage independent of Render's ephemeral filesystem |
| QR codes | Vendored QRCodeJS | Local browser generation without sharing URLs with a QR service |
| Hosting | Render Docker Web Service | Reproducible container builds, environment variables, health checks, and automatic `main` deployment |
| UI verification | Playwright + manual review | Stable desktop/mobile captures plus interaction checks at real breakpoints |

## UI and Screenshot Verification

The documentation contains 33 true PNG captures at `1440x900` and `390x844`.
They cover landing, login, administrator account management, workspace selection, profile
selection, Shortener, portfolio actions, QR, editing, both analytics modes,
profile settings, and the public Link Tree. A reusable Playwright script logs in
through the real UI and captures each state from a disposable demo database.
The full index and regeneration workflow are documented in
[`docs/SCREENSHOTS.md`](SCREENSHOTS.md).

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
| Screenshot guide | `docs/SCREENSHOTS.md` |
| Screenshot automation | `scripts/capture_docs_screenshots.py` |
| Screenshots | `screenshots/` (33 desktop/mobile PNG files) |

## What I'd Do Next

1. **Custom domain** — Point a project-owned domain to the Render deployment.
2. **Geographic Analytics** — Add privacy-conscious country-level click analytics.
3. **Accessibility audit** — Extend keyboard, screen-reader, and contrast testing across every workflow.
