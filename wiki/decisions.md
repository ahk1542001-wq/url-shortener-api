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
- **Decision**: Multi-User Authentication via JWT (JSON Web Tokens).
- **Reasoning**: To support Link Trees and multiple profiles independently, the application requires individual user accounts. JWT provides a stateless, scalable way to authenticate API requests without relying on server-side session storage.

## 5. UI Layout
- **Decision**: Adaptive Desktop Sidebar and Mobile Dock.
- **Reasoning**: To support a richer feature set (Dashboard vs Link Trees), we moved away from a single centered card to a responsive layout that utilizes a persistent navigation structure, providing a more premium app-like experience.
