# Project Patterns

## Styling (Glassmorphism)
- Use `--glass-bg` and `--glass-border` CSS variables for cards and UI panels.
- Add `backdrop-filter: blur(16px)` to achieve the frosted glass effect.
- Keep the UI minimal and focused. Avoid clutter.

## Testing
- Tests are written in Pytest (`tests/`).
- Use the `client` fixture (from `fastapi.testclient`) for all endpoint tests.
- Database access is mocked/patched to use an in-memory SQLite database (`test.db`) during testing via `conftest.py`.

## API Responses
- All errors must return a structured JSON response:
  `{"error": {"code": 404, "message": "Short code not found"}}`
- Use Pydantic models for request/response validation.

## Security
- Always use parameterized queries (via the `P` placeholder helper in `database.py`) to prevent SQL injection.
- Validate all incoming URLs via Pydantic (`validators`).
- Set security headers on all responses via the `security_headers` middleware in `app.py`.
