---
marp: true
theme: default
paginate: true
---

# Swoosh
## URL shortener and link-in-bio builder

**Live:** https://swoo-sh.onrender.com

Swoosh creates trackable short URLs and public Link Tree profiles from one self-hosted application.

---

# What users can do

- Sign in with an administrator-created account.
- Create standalone short links with optional custom codes.
- Create and switch among up to five public Link Tree profiles.
- Add a bio, avatar, and social or website links.
- Share a public URL or locally generated QR code.
- Review short-link clicks and Link Tree visits separately.

---

# Technical foundation

- FastAPI and Python 3.11
- Vanilla HTML, CSS, and JavaScript
- SQLite locally and Neon PostgreSQL in production
- Cloudinary avatar storage
- JWT authentication and bcrypt password hashing
- Rate limiting, validation, migrations, and security headers

---

# Delivery status

- Responsive desktop sidebar and mobile top navigation
- Olive Ink and Warm Lime brand system
- 73 local tests passing; one optional PostgreSQL test skipped
- Deployed on Render
- Open source under the MIT License

**GitHub:** github.com/ahk1542001-wq/url-shortener-api
