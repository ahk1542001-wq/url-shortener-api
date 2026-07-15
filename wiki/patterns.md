# Project Patterns

## Styling (Glassmorphism)
- Use `--glass-bg` and `--glass-border` CSS variables for cards and UI panels.
- Add `backdrop-filter: blur(16px)` to achieve the frosted glass effect.
- Keep the UI minimal and focused. Avoid clutter.
- Use Olive Ink (`#2F3A1D`) for primary surfaces and Warm Lime (`#CFFF74`) for primary actions and active states.
- Use the desktop sidebar at larger viewports and the sticky labeled top navigation on mobile.
- Keep Shortener and Link Tree controls in their own workspaces.
- Verify changed layouts at desktop and mobile widths before shipping.

## Testing
- Tests are written in Pytest (`tests/`).
- Use the `auth_client` fixture (from `conftest.py`) for all endpoint tests that require authentication.
- Database access is mocked/patched to use an in-memory SQLite database (`test.db`) during testing via `conftest.py`.
- UI contract tests assert required navigation, QR, profile switching, and public-tree elements without requiring a browser.

## API Responses
- All errors must return a structured JSON response:
  `{"error": {"code": 404, "message": "Short code not found"}}`
- Use Pydantic models for request/response validation.

## Security
- Always use parameterized queries (via the `P` placeholder helper in `database.py`) to prevent SQL injection.
- Validate all incoming URLs via Pydantic (`validators`).
- Set security headers on all responses via the `security_headers` middleware in `src/main.py`.
- Authentication is handled via JWT Bearer tokens passed in the `Authorization` header.
- Never return `hashed_password` or imply that an existing password can be viewed. Admin password changes are one-way resets.
- Recheck `users.is_active` while resolving every normal-user JWT so account disablement takes effect immediately.
- Protect the environment-managed `admin` identity from edit and delete operations.
