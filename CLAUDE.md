# Claude Code Context

Welcome! This repository uses **Spec-Driven Development** (SDD) as part of the Vibe Coding Tour. 

## Context Directories
- Read the `wiki/` directory before making any architectural or structural changes.
- Read `docs/SPEC.md` and `docs/PLAN.md` to understand the feature requirements and current implementation plan.

## Technical Stack
- Backend: FastAPI (Python 3.11)
- Database: Neon PostgreSQL (Production), SQLite (Local)
- Frontend: Vanilla HTML/JS/CSS (Glassmorphism UI)

## Security Rules
- Account creation is restricted to admin only (no public registration).
- Admin APIs may reset but must never reveal passwords or password hashes; the environment-managed admin identity is not editable or deletable.
- Normal-user JWT resolution must enforce account active status.
- NEVER commit secrets (e.g., `DATABASE_URL` or `ACCESS_PASSWORD`) to version control.
- `DATABASE_URL` is injected via Render environment variables.
- Run tests via `pytest -v` before finalizing any changes.
- Ensure strict compliance with `.claude/settings.json` permissions.
