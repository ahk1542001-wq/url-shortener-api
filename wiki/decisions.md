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
- **Decision**: Separate Shortener and Link Tree workspaces with an adaptive desktop sidebar and sticky mobile top navigation.
- **Reasoning**: The feature separation keeps link management and public-profile editing understandable. Moving mobile navigation to the top prevents it from covering content and action buttons.

## 6. Link Tree Product Boundary
- **Decision**: Allow each login account to create, select, and manage up to five Link Tree profiles.
- **Reasoning**: A profile chooser supports separate public identities while the five-profile cap keeps the class-project UI and data model manageable.

## 7. Brand Palette
- **Decision**: Use Olive Ink (`#2F3A1D`) for brand surfaces and Warm Lime (`#CFFF74`) for primary actions and active states.
- **Reasoning**: The pairing provides a recognizable, high-contrast identity across light and dark system themes.
