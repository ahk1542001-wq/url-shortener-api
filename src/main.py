import os
import random
import re
import string
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src import config
from src.database import _placeholder, get_db, init_db

P = _placeholder()

RESERVED_CODES = {"api", "admin", "static", "health", "docs", "openapi", "u"}

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


def get_current_user(request: Request) -> dict:
    auth = request.headers.get("X-Access-Password", "")
    if not auth:
        raise HTTPException(status_code=401, detail="Invalid or missing password")
    
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT id, username, bio, tree_views, social_links FROM users WHERE passcode = {P}", (auth,))
        user = c.fetchone()
        
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or missing password")
        
    return {
        "id": user[0],
        "username": user[1],
        "bio": user[2],
        "tree_views": user[3],
        "social_links": user[4]
    }


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
    title: Optional[str] = None
    show_on_tree: bool = False

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


class EditLinkRequest(BaseModel):
    original_url: str
    title: Optional[str] = None
    show_on_tree: bool = False

    @field_validator("original_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if len(v) > 2048:
            raise ValueError("URL must be 2048 characters or fewer")
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class ShortenResponse(BaseModel):
    short_code: str
    original_url: str
    already_exists: bool = False


class AnalyticsResponse(BaseModel):
    short_code: str
    original_url: str
    title: Optional[str]
    show_on_tree: bool
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


@app.get("/api/me")
def get_me(user: dict = Depends(get_current_user)):
    return {
        "username": user["username"],
        "bio": user["bio"],
        "tree_views": user["tree_views"],
        "social_links": user["social_links"]
    }


@app.post("/api/shorten", response_model=ShortenResponse, status_code=201)
@limiter.limit(config.RATE_LIMIT)
def shorten_url(request: Request, req: ShortenRequest, user: dict = Depends(get_current_user)) -> ShortenResponse:
    with get_db() as conn:
        c = conn.cursor()

        if not req.custom_code:
            c.execute(
                f"SELECT short_code FROM urls WHERE original_url = {P} AND user_id = {P}", 
                (req.url, user["id"])
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
            f"INSERT INTO urls (short_code, original_url, user_id, title, show_on_tree) VALUES ({P}, {P}, {P}, {P}, {P})",
            (short_code, req.url, user["id"], req.title, req.show_on_tree),
        )

    return ShortenResponse(short_code=short_code, original_url=req.url)


@app.get("/api/stats/{code}", response_model=AnalyticsResponse)
def get_stats(code: str, user: dict = Depends(get_current_user)) -> AnalyticsResponse:
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            f"SELECT original_url, title, show_on_tree, click_count, created_at, last_accessed "
            f"FROM urls WHERE short_code = {P} AND user_id = {P}",
            (code, user["id"]),
        )
        result = c.fetchone()

    if not result:
        raise HTTPException(status_code=404, detail="Short code not found")

    return AnalyticsResponse(
        short_code=code,
        original_url=result[0],
        title=result[1],
        show_on_tree=bool(result[2]),
        click_count=result[3],
        created_at=_fmt_dt(result[4]),
        last_accessed=_fmt_dt(result[5]),
    )


@app.get("/api/links")
def list_links(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            f"SELECT short_code, original_url, title, show_on_tree, click_count, created_at, last_accessed "
            f"FROM urls WHERE user_id = {P} ORDER BY created_at DESC",
            (user["id"],)
        )
        rows = c.fetchall()

    return {
        "links": [
            {
                "short_code": row[0],
                "original_url": row[1],
                "title": row[2],
                "show_on_tree": bool(row[3]),
                "click_count": row[4],
                "created_at": _fmt_dt(row[5]),
                "last_accessed": _fmt_dt(row[6]),
            }
            for row in rows
        ]
    }


@app.delete("/api/links/{code}")
def delete_link(code: str, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT id FROM urls WHERE short_code = {P} AND user_id = {P}", (code, user["id"]))
        if not c.fetchone():
            raise HTTPException(status_code=404, detail="Short code not found")
        c.execute(f"DELETE FROM urls WHERE short_code = {P} AND user_id = {P}", (code, user["id"]))
    return {"message": f"Deleted {code}"}


@app.put("/api/links/{code}")
def update_link(code: str, req: EditLinkRequest, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT id FROM urls WHERE short_code = {P} AND user_id = {P}", (code, user["id"]))
        if not c.fetchone():
            raise HTTPException(status_code=404, detail="Short code not found")
        c.execute(
            f"UPDATE urls SET original_url = {P}, title = {P}, show_on_tree = {P} WHERE short_code = {P} AND user_id = {P}",
            (req.original_url, req.title, req.show_on_tree, code, user["id"]),
        )
    return {"message": f"Updated {code}", "original_url": req.original_url}


@app.get("/api/users/{username}/tree")
def get_user_tree(username: str):
    with get_db() as conn:
        c = conn.cursor()
        # Find user
        c.execute(f"SELECT id, bio, social_links FROM users WHERE username = {P}", (username,))
        user = c.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        user_id = user[0]
        bio = user[1]
        social_links = user[2]
        
        # Increment tree views
        c.execute(f"UPDATE users SET tree_views = tree_views + 1 WHERE id = {P}", (user_id,))
        
        # Fetch public links for tree
        c.execute(
            f"SELECT title, short_code, original_url FROM urls WHERE user_id = {P} AND show_on_tree = {P} ORDER BY created_at DESC",
            (user_id, True if _placeholder() == "%s" else 1) # Postgres uses TRUE, SQLite uses 1
        )
        rows = c.fetchall()
        
    return {
        "username": username,
        "bio": bio,
        "social_links": social_links,
        "links": [
            {
                "title": row[0] or row[2], # Fallback to original url if title is empty
                "short_code": row[1],
                "url": f"/{row[1]}" # The shortened redirect URL
            }
            for row in rows
        ]
    }


@app.get("/{code}")
def redirect_url(code: str) -> RedirectResponse:
    if code in ["u"]:
        raise HTTPException(status_code=404)
        
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


@app.get("/u/{username}")
def serve_user_tree(username: str):
    if not os.path.isfile("static/tree.html"):
        return JSONResponse(
            status_code=404,
            content={"error": {"code": 404, "message": "Tree template not found"}},
        )
    return FileResponse("static/tree.html")


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
