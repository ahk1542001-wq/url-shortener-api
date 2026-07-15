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

---

# Deployment Safety

- Required secret validation at startup
- No public account registration
- Neon branch or snapshot before migrations
- Destructive PostgreSQL tests require explicit opt-in
- Cloudinary variables validated as an all-or-nothing group
- Rollback through a prior Render commit and Neon backup branch
