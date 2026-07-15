---
marp: true
theme: default
class: lead
paginate: true
backgroundColor: #F7FBEF
color: #2F3A1D
---

# Swoosh
## Technical Stack and Delivery Workflow

**Developer:** @ahk1542001-wq

**Project:** Vibe Coding Tour

---

# Application Stack

- **Backend:** FastAPI on Python 3.11
- **Frontend:** Vanilla HTML, CSS, and JavaScript
- **Local data:** SQLite
- **Production data:** Neon PostgreSQL
- **Avatar media:** Cloudinary
- **Deployment:** Render
- **Authentication:** JWT and bcrypt
- **Administration:** Protected user summaries, reset, status, and deletion APIs

---

# Product Architecture

```text
Responsive browser UI
        |
        v
FastAPI routers and dependencies
        |
        +-- SQLite / Neon PostgreSQL
        +-- Cloudinary avatar storage
        +-- Background analytics flush
```

Standalone links and Link Tree profiles share the application but remain separate user workspaces.

---

# Quality Workflow

1. Define behavior in `docs/SPEC.md`.
2. Record implementation steps in `docs/PLAN.md`.
3. Implement narrow backend, frontend, and migration changes.
4. Add regression and UI contract tests.
5. Run Pytest, Ruff, JavaScript syntax, and whitespace checks.
6. Update docs, slides, and desktop/mobile screenshots.
7. Review the pull request before deployment.

Screenshots are regenerated through `scripts/capture_docs_screenshots.py` at
fixed `1440x900` and `390x844` viewports.

---

# Deployment Safety

- Required secret validation at startup
- No public account registration
- Existing passwords remain unreadable; reset is one-way
- Disabled accounts invalidate login and later JWT-backed requests
- Neon branch or snapshot before migrations
- Destructive PostgreSQL tests require explicit opt-in
- Cloudinary variables validated as an all-or-nothing group
- Rollback through a prior Render commit and Neon backup branch

---

# Production Delivery

1. Merge a reviewed pull request into `main`.
2. Render starts an automatic Docker deployment.
3. Runtime secrets are injected from the Render environment.
4. `/api/health` must return HTTP `200` before acceptance.
5. Recheck login, shortening, redirect, QR, analytics, Link Tree, and avatar upload.
6. Update release evidence without committing production credentials or data.
