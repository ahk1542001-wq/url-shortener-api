# Swoosh Architecture & System Design

## 1. System Overview

Swoosh is designed as a monolithic, self-contained application utilizing a **FastAPI backend** and a **Vanilla HTML/JS/CSS frontend**. It operates on a multi-tenant architecture, allowing multiple users to register, create public Link Tree profiles, and manage standalone short URLs.

```mermaid
graph TD
    Client[Browser / Client] -->|HTTPS Requests| Render[Render Web Service]
    Render -->|FastAPI| App[Swoosh Backend Application]
    App -->|SQL Queries| DB[(Neon PostgreSQL)]
    App -->|Serve Static| UI[Frontend UI]
```

## 2. Frontend Architecture (Vanilla SPA)

The frontend is built without heavy frameworks (React, Vue) to prioritize speed, simplicity, and low overhead. It acts as a Single Page Application (SPA) using vanilla JavaScript for DOM manipulation and routing.

### Core Files
- **`index.html`**: The main shell. It contains the raw HTML structure for all views (Login, Feature Selection, Profile Creation, Dashboard, Link Tree).
- **`style.css`**: Utilizes CSS variables for **Adaptive Theming** (Dark/Light mode via `@media (prefers-color-scheme)`). Implements a responsive layout featuring a **Desktop Sidebar** and a **Mobile Floating Dock**.
- **`script.js`**: The core controller.

### View Routing Mechanism
The frontend uses a simple CSS-class based routing mechanism.
1. The `hideAllViews()` function iterates through all main container divs and adds the `.hidden` class.
2. Specific functions like `showDashboard()` or `showFeatureSelection()` call `hideAllViews()`, then remove the `.hidden` class from their target div.
3. State is managed entirely via DOM data attributes and `localStorage`.

### State Management & Auth
- **`swoosh_token`**: Stored in `localStorage`. Contains the JWT string for API authentication.
- **`swoosh_active_profile`**: Stored in `localStorage`. Tracks whether the user is currently managing a specific Link Tree profile or operating in "Standalone Mode".

## 3. Backend Architecture (FastAPI)

The backend is built with Python 3.11 and FastAPI, chosen for its asynchronous capabilities, automatic OpenAPI documentation, and strict type validation (Pydantic).

### Core Components
- **`src/main.py`**: The application entry point. Defines all HTTP endpoints (`/api/login`, `/api/shorten`, `/api/links`), API routers, rate limiters (`slowapi`), and the core JWT authorization logic.
- **`src/config.py`**: Handles environment variables via `os.environ`.
- **`src/database.py`**: A database connection factory. It detects if a `DATABASE_URL` is present (for Neon PostgreSQL) or falls back to a local SQLite file (`shortener.db`).

### Authentication Flow (JWT)
1. User POSTs credentials to `/api/login`.
2. Backend verifies credentials against the hashed password in the database (bcrypt).
3. Backend generates a JSON Web Token (JWT) signed with `JWT_SECRET` and returns it.
4. Client attaches the token as a header (`Authorization: Bearer <token>`) to all subsequent secure requests.
5. FastAPI's `get_current_user` dependency intercepts requests, decodes the JWT, and rejects invalid/expired tokens with a `401 Unauthorized` response.

## 4. Database Schema (Multi-Tenant)

The database structure is designed to support users having multiple Link Tree profiles, while also allowing standalone short links that aren't attached to any profile.

```mermaid
erDiagram
    USERS ||--o{ PROFILES : owns
    USERS ||--o{ LINKS : creates
    PROFILES ||--o{ LINKS : displays
    
    USERS {
        int id PK
        string username
        string password_hash
    }
    
    PROFILES {
        int id PK
        int user_id FK
        string username
        string bio
        int tree_views
        json social_links
    }
    
    LINKS {
        string short_code PK
        string original_url
        int clicks
        timestamp created_at
        int user_id FK
        int profile_id FK "Nullable"
    }
```

- **Standalone Mode**: When a user creates a link outside of a Link Tree, `profile_id` is set to `NULL`. The link is only associated with `user_id`.
- **Link Tree Mode**: Links created within a profile are assigned a `profile_id`, determining which links appear on the public `/tree/{profile_username}` page.

## 5. Security & Protection Mechanisms

Swoosh is designed to be self-hosted on public networks, meaning it is exposed to bots and malicious actors.
- **Rate Limiting**: `slowapi` enforces a strict 30 requests per minute per IP limit on write operations (like `/api/shorten`).
- **Input Validation**: Pydantic strictly validates all JSON bodies. Usernames and custom short codes are regex-checked to ensure they only contain alphanumeric characters and hyphens, preventing reserved-word collisions.
- **SQL Injection Prevention**: All queries to the SQLite/PostgreSQL database use parameterized SQL queries via the standard `sqlite3` and `psycopg2` libraries. No string formatting is used in SQL execution.
- **XSS Prevention**: When rendering the Link Tree frontend, user-provided values (like the profile bio or link titles) are sanitized before being inserted into the DOM using an `escapeHtml()` helper function.

## 6. Deployment Pipeline

The application is deployed to **Render** as a Web Service.
1. Render pulls the latest code from the `main` branch.
2. Render executes `pip install -r requirements.txt`.
3. Render runs the application using Uvicorn via `uvicorn src.main:app --host 0.0.0.0 --port $PORT`.
4. Render injects securely stored Environment Variables (`DATABASE_URL`, `JWT_SECRET`) at runtime, preventing secrets from being leaked in the Git repository.
