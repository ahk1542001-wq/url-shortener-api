---
marp: true
theme: default
paginate: true
auto-advance: 20
---

# Swoosh URL Shortener
## Simplifying your long links

A fast, efficient URL shortening API built with Python, FastAPI, and SQLite.
Features a premium Glassmorphism UI and built-in click analytics.
Built with Claude Code and Advanced Agent Skills.

---

# Why Swoosh?

- **Problem:** Long URLs are difficult to share, look ugly, and hide analytics.
- **Solution:** A modern web app that converts long URLs into short, trackable codes.
- **Impact:** Cleaner communication, custom branded links, and actionable data.

---

# Technologies Used

- **Python & FastAPI:** For a high-performance, auto-documented web backend.
- **SQLite:** A serverless database to persist codes and analytics.
- **Frontend UI:** Vanilla HTML/CSS/JS with a Glassmorphism aesthetic.
- **Claude Code MCP:** `mcp-server-sqlite` for seamless database inspection.

---

# The Architecture

- `POST /api/shorten`: Accepts long URLs and optional custom codes.
- `GET /<code>`: Looks up, increments the `click_count`, and redirects.
- `GET /api/stats/<code>`: Exposes click counts and access times.
- **Database:** Stores IDs, short codes, original URLs, and timestamps.

---

# Spec-Driven Development

- The API design strictly follows the **Contract First** principle.
- Consistent error formatting using FastAPI's HTTPExceptions.
- A dedicated Claude Agent (`url-tester`) autonomously verifies these endpoints against the SKILL contract inspired by Addy Osmani's `agent-skills`.

---

# Future Improvements

- Add user authentication for managing personal links.
- Add geographic analytics (e.g., clicks by country).
- Rate limiting to prevent spam.
- **Thank you!** Check out the GitHub repo and give it a ⭐!
