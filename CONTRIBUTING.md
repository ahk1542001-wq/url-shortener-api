# Contributing to Swoosh

Thank you for helping improve Swoosh. Small, focused pull requests are easiest to review and maintain.

## Before You Start

1. Search existing issues and pull requests.
2. Open an issue for large behavior, schema, or architecture changes.
3. Never include secrets, production database URLs, access tokens, or real user data.
4. Read `docs/SPEC.md`, `docs/PLAN.md`, and the relevant files in `wiki/`.

## Development Setup

Follow the local setup in `README.md`. Use Python 3.11 and an isolated virtual environment.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Use SQLite for routine development. PostgreSQL migration tests must run only against a disposable database whose name contains `test`.

## Making a Change

- Follow the existing FastAPI, SQL, and vanilla frontend patterns.
- Keep standalone shortener and Link Tree behavior separate.
- Preserve SQLite and PostgreSQL compatibility for database changes.
- Add or update tests for user-visible behavior and regression fixes.
- Update the README, specification, wiki, slides, and screenshots when the product changes.
- Include third-party licenses for vendored browser assets.

## Verification

Run before opening a pull request:

```bash
./.venv/bin/python -m pytest -v
./.venv/bin/ruff check .
./.venv/bin/ruff format --check .
node --check static/script.js
git diff --check
```

For the real PostgreSQL migration test, use a disposable Neon branch or local test database:

```bash
POSTGRES_TEST_URL='postgresql://user:pass@host/swoosh_test' \
ALLOW_DESTRUCTIVE_POSTGRES_TESTS=yes \
./.venv/bin/python -m pytest -v -m postgres
```

Never point this command at production.

## Pull Request Checklist

- Explain the problem and the user-visible result.
- List the important files changed.
- Include verification results.
- Attach desktop and mobile screenshots for UI changes.
- Note database migration, deployment, or environment-variable impact.
- Confirm no secrets or real user data are included.

## Reporting Security Problems

Do not open public issues for suspected vulnerabilities. Follow `SECURITY.md`.
