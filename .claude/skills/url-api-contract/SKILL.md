---
name: url-api-contract
description: Guides stable API and interface design for the URL Shortener API. Use when implementing or interacting with the shorten and redirect endpoints.
---

# URL Shortener API Contract

## Overview

Design stable, well-documented interfaces for the URL Shortener. The API must make the right thing easy and the wrong thing hard. This applies to the REST API endpoints and database schema.

## When to Use

- Implementing new endpoints for the URL Shortener.
- Testing the API with the URL Tester agent.
- Modifying the SQLite database schema.

## Core Principles

### 1. Contract First
Define the interface before implementing it. The contract is the spec — implementation follows.

```python
# Create Short URL
POST /api/shorten
Input: { "url": "https://example.com/very/long/path" }
Output: { "short_code": "aB3dE", "original_url": "https://example.com/very/long/path" }

# Redirect
GET /<code>
Redirects to original_url with 302 Found.
```

### 2. Consistent Error Semantics
Pick one error strategy and use it everywhere:

```python
# Error response body
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "URL is required"
  }
}
```

### 3. Validate at Boundaries
Validate the provided URL before inserting into the SQLite database. Ensure it is a valid HTTP/HTTPS URL.

## Red Flags

- Endpoints returning different shapes.
- Missing URL validation allowing arbitrary strings.
- Exposing internal database errors to the client.

## Verification

After designing or modifying the API:
- [ ] Every endpoint has typed input and output schemas.
- [ ] Error responses follow a single consistent format.
- [ ] Validation happens at system boundaries only.
- [ ] The SQLite database is securely accessed.
