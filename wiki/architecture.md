# Architecture

## Overview
Swoosh is a monolithic FastAPI backend serving a vanilla HTML/JS/CSS frontend.

## Components
1. **Frontend**:
   - `static/index.html`: Main UI shell.
   - `static/style.css`: Glassmorphism styling and custom animations.
   - `static/script.js`: DOM manipulation, API fetching, and auth handling.

2. **Backend**:
   - `app.py`: FastAPI routes, Pydantic models, rate limiting, and security middleware.
   - `config.py`: Environment variable ingestion.
   - `database.py`: Database connection factory (SQLite or PostgreSQL based on `DATABASE_URL`).

3. **Database**:
   - Local: SQLite (`shortener.db`).
   - Production: Neon Serverless PostgreSQL.

## Deployment Architecture
- **Host**: Render (Web Service)
- **Database**: Neon (PostgreSQL)
- **Secrets Management**: Render Environment Variables (`DATABASE_URL`, `ACCESS_PASSWORD`). Secrets are *never* committed to version control.
