import os
import random
import re
import string
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import config
from database import _placeholder, get_db, init_db

P = _placeholder()

RESERVED_CODES = {"api", "admin", "static", "health", "docs", "openapi"}

limiter = Limiter(key_func=get_remote_address, default_limits=[config.RATE_LIMIT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="URL Shortener API", lifespan=lifespan)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": {"code": 429, "message": "Rate limit exceeded. Try again later."}
        },
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


@app.middleware("http")
async def password_guard(request: Request, call_next):
    if config.ACCESS_PASSWORD:
        needs_auth = False
        if request.method in ("POST", "DELETE"):
            needs_auth = True
        elif request.method == "GET" and request.url.path == "/api/links":
            needs_auth = True
        if needs_auth:
            auth = request.headers.get("X-Access-Password", "")
            if auth != config.ACCESS_PASSWORD:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": {
                            "code": 401,
                            "message": "Invalid or missing password",
                        }
                    },
                )
    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    messages = [
        f"{' -> '.join(str(p) for p in err['loc'])}: {err['msg']}"
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"error": {"code": 422, "message": "; ".join(messages)}},
    )


# --- Models ---


class ShortenRequest(BaseModel):
    url: str
    custom_code: Optional[str] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if len(v) > 2048:
            raise ValueError("URL must be 2048 characters or fewer")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("custom_code")
    @classmethod
    def validate_custom_code(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if len(v) < 3 or len(v) > 20:
            raise ValueError("Custom code must be 3-20 characters")
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError(
                "Custom code must contain only letters, numbers, and hyphens"
            )
        if v.lower() in RESERVED_CODES:
            raise ValueError(f"'{v}' is a reserved code and cannot be used")
        return v


class ShortenResponse(BaseModel):
    short_code: str
    original_url: str
    already_exists: bool = False


class AnalyticsResponse(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    created_at: str
    last_accessed: str


# --- Helpers ---


def _fmt_dt(val) -> str:
    if val is None:
        return "Never"
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    return str(val)


def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


# --- Routes ---


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/shorten", response_model=ShortenResponse, status_code=201)
@limiter.limit(config.RATE_LIMIT)
def shorten_url(request: Request, req: ShortenRequest) -> ShortenResponse:
    with get_db() as conn:
        c = conn.cursor()

        if not req.custom_code:
            c.execute(
                f"SELECT short_code FROM urls WHERE original_url = {P}", (req.url,)
            )
            existing = c.fetchone()
            if existing:
                return ShortenResponse(
                    short_code=existing[0],
                    original_url=req.url,
                    already_exists=True,
                )
            while True:
                short_code = generate_short_code()
                c.execute(f"SELECT id FROM urls WHERE short_code = {P}", (short_code,))
                if not c.fetchone():
                    break
        else:
            short_code = req.custom_code
            c.execute(f"SELECT id FROM urls WHERE short_code = {P}", (short_code,))
            if c.fetchone():
                raise HTTPException(
                    status_code=409, detail="Custom short code already in use"
                )

        c.execute(
            "INSERT INTO urls (short_code, original_url) VALUES ({0}, {0})".format(P),
            (short_code, req.url),
        )

    return ShortenResponse(short_code=short_code, original_url=req.url)


@app.get("/api/stats/{code}", response_model=AnalyticsResponse)
def get_stats(code: str) -> AnalyticsResponse:
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            f"SELECT original_url, click_count, created_at, last_accessed "
            f"FROM urls WHERE short_code = {P}",
            (code,),
        )
        result = c.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Short code not found")

    return AnalyticsResponse(
        short_code=code,
        original_url=result[0],
        click_count=result[1],
        created_at=_fmt_dt(result[2]),
        last_accessed=_fmt_dt(result[3]),
    )


@app.get("/api/links")
def list_links():
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT short_code, original_url, click_count, created_at, last_accessed "
            "FROM urls ORDER BY created_at DESC"
        )
        rows = c.fetchall()

    return {
        "links": [
            {
                "short_code": row[0],
                "original_url": row[1],
                "click_count": row[2],
                "created_at": _fmt_dt(row[3]),
                "last_accessed": _fmt_dt(row[4]),
            }
            for row in rows
        ]
    }


@app.delete("/api/links/{code}")
def delete_link(code: str):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT id FROM urls WHERE short_code = {P}", (code,))
        if not c.fetchone():
            raise HTTPException(status_code=404, detail="Short code not found")
        c.execute(f"DELETE FROM urls WHERE short_code = {P}", (code,))
    return {"message": f"Deleted {code}"}


@app.get("/{code}")
def redirect_url(code: str) -> RedirectResponse:
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT original_url FROM urls WHERE short_code = {P}", (code,))
        result = c.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Short code not found")

        original_url = result[0]
        now = datetime.now(timezone.utc)
        c.execute(
            f"UPDATE urls SET click_count = click_count + 1, last_accessed = {P} "
            f"WHERE short_code = {P}",
            (now, code),
        )

    return RedirectResponse(url=original_url, status_code=302)


# --- Static files ---

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_frontend():
    if not os.path.isfile("static/index.html"):
        return JSONResponse(
            status_code=404,
            content={"error": {"code": 404, "message": "Frontend not found"}},
        )
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.HOST, port=config.PORT)
