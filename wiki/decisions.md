# Decisions Log

## 1. Database
- **Decision**: Use SQLite for local development and Neon PostgreSQL for production.
- **Reasoning**: SQLite is zero-setup and fast for local iterations. Neon offers a generous free tier for Serverless Postgres which integrates perfectly with Render for production.
- **Implementation**: `database.py` dynamically selects the engine based on the presence of the `DATABASE_URL` environment variable.

## 2. API Framework
- **Decision**: FastAPI (Python).
- **Reasoning**: Fast, modern, async-first, and provides automatic validation via Pydantic. Excellent for a small REST API.

## 3. Frontend
- **Decision**: Vanilla HTML/JS/CSS.
- **Reasoning**: Keeps the application lightweight and monolithic. No build step required for the frontend. Glassmorphism styling achieves the "luxury" vibe requested by the user.

## 4. Auth
- **Decision**: Simple password-based authentication via headers (`X-Access-Password`).
- **Reasoning**: It's a personal URL shortener. No need for complex OAuth or JWT infrastructure. A single password in the environment variables is sufficient and secure.
