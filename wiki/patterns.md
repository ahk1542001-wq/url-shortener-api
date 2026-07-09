# Project Patterns

## Styling (Glassmorphism)
- Use `--glass-bg` and `--glass-border` CSS variables for cards and UI panels.
- Add `backdrop-filter: blur(16px)` to achieve the frosted glass effect.
- Keep the UI minimal and focused. Avoid clutter.

## Testing
- Tests are written in Pytest (`tests/`).
- Use the `auth_client` fixture (from `conftest.py`) for all endpoint tests that require authentication.
- Database access is mocked/patched to use an in-memory SQLite database (`test.db`) during testing via `conftest.py`.

## API Responses
- All errors must return a structured JSON response:
  `{"error": {"code": 404, "message": "Short code not found"}}`
- Use Pydantic models for request/response validation.

## Security
- Always use parameterized queries (via the `P` placeholder helper in `database.py`) to prevent SQL injection.
- Validate all incoming URLs via Pydantic (`validators`).
- Set security headers on all responses via the `security_headers` middleware in `src/main.py`.
- Authentication is handled via JWT Bearer tokens passed in the `Authorization` header.
