---
name: url-api-contract
description: Guides stable API and interface design for the URL Shortener API. Use when implementing or interacting with the shorten and redirect endpoints.
---

# URL Shortener API Contract

## Overview

Design stable, well-documented interfaces for the URL Shortener built with FastAPI. The API must make the right thing easy and the wrong thing hard. This applies to the REST API endpoints and database schema.

## When to Use

- Implementing new endpoints for the URL Shortener.
- Testing the API with the URL Tester agent.
- Modifying the SQLite database schema.

## Core Principles

### 1. Contract First
Define the interface before implementing it. The contract is the spec — implementation follows.

```python
# Login
POST /api/login
Input: { "username": "admin", "password": "your-password" }
Output: { "token": "ey..." }

# Create Short URL
POST /api/shorten
Headers: { "Authorization": "Bearer <token>" }
Input: { "url": "https://example.com/very/long/path", "custom_code": "optional-custom" }
Output: { "short_code": "aB3dE", "original_url": "https://example.com/..." }

# Upload Avatar (Cloudinary)
POST /api/profiles/avatar
Headers: { "Authorization": "Bearer <token>" }
Input: multipart/form-data with file
Output: { "message": "Avatar uploaded successfully", "avatar_url": "https://..." }

# Redirect
GET /<code>
Redirects to original_url with 302 Found.

# Stats
GET /api/stats/<code>
Output: { "short_code": "...", "original_url": "...", "click_count": 5, "created_at": "...", "last_accessed": "..." }
```

### 2. Consistent Error Semantics
FastAPI handles automatic validation errors (422 Unprocessable Entity) and custom HTTPExceptions, returning a standard JSON envelope:
```python
{
  "error": {
    "code": 409,
    "message": "Custom short code already in use"
  }
}
```
Auth endpoints return 401 if the JWT is missing, invalid, or expired. Rate-limited endpoints return 429.

### 3. Validate at Boundaries
Validate the provided URL before inserting into the database. Ensure it is a valid HTTP/HTTPS URL via Pydantic or custom logic.

## Red Flags
- Endpoints returning different shapes.
- Missing URL validation allowing arbitrary strings.
- Exposing internal database errors to the client.

## Verification
After designing or modifying the API:
- [ ] Every endpoint has typed input and output schemas.
- [ ] Error responses follow a single consistent format.
- [ ] Validation happens at system boundaries only.
- [ ] The database is securely accessed and properly increments clicks.
- [ ] Avatar files are validated (under 2MB, valid format) before uploading to Cloudinary.
