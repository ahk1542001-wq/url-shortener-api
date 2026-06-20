---
marp: true
theme: default
paginate: true
auto-advance: 20
---

# URL Shortener API
## Simplifying long links

A fast and efficient URL shortening API built with Python, Flask, and SQLite.
Built with Claude Code and Advanced Agent Skills.

---

# Why URL Shortener?

- **Problem:** Long URLs are difficult to share, look ugly, and consume character limits.
- **Solution:** A simple API that takes any long URL and returns a short, concise code.
- **Impact:** Cleaner communication and easier linking across platforms.

---

# Technologies Used

- **Python & Flask:** For a lightweight and responsive web framework.
- **SQLite:** A serverless database to persist shortened codes.
- **Claude Code MCP:** `mcp-server-sqlite` for seamless database inspection.
- **Advanced Skills:** API contract definitions inspired by `agent-skills`.

---

# The Architecture

- `POST /api/shorten`: Accepts `{ "url": "https://..." }`.
- Validates the input at the boundaries.
- Generates a random alphanumeric 6-character short code.
- Inserts safely into SQLite.
- `GET /<code>`: Looks up and redirects.

---

# Spec-Driven Development

- The API design strictly follows the **Contract First** principle.
- Consistent error formatting using JSON structures.
- A dedicated Claude Agent (`url-tester`) was built alongside to autonomously verify these endpoints against the SKILL contract.

---

# Future Improvements

- Add custom short codes (e.g., `/my-event`).
- Add click analytics and tracking.
- Rate limiting to prevent spam.
- **Thank you!** Check out the GitHub repo and give it a ⭐!
