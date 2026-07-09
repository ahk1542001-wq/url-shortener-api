import asyncio
from collections import defaultdict
import json
import os
import random
import re
import string
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List

import jwt
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from pydantic import BaseModel, field_validator
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src import config
from src.database import _placeholder, get_db, init_db

P = _placeholder()

RESERVED_CODES = {"api", "static", "health", "docs", "openapi", "u", "admin"}

SECRET_KEY = config.JWT_SECRET
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

limiter = Limiter(key_func=get_remote_address, default_limits=[config.RATE_LIMIT])
analytics_buffer = defaultdict(int)

async def flush_analytics():
    """Background task to flush in-memory analytics to SQLite every 10 seconds."""
    while True:
        await asyncio.sleep(10)
        try:
            if not analytics_buffer:
                continue
            
            to_flush = dict(analytics_buffer)
            analytics_buffer.clear()
            
            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            with get_db() as conn:
                c = conn.cursor()
                for code, clicks in to_flush.items():
                    c.execute(f"SELECT id FROM urls WHERE short_code = {P}", (code,))
                    result = c.fetchone()
                    if result:
                        link_id = result[0]
                        c.execute(f"UPDATE urls SET click_count = click_count + {clicks}, last_accessed = {P} WHERE id = {P}", (datetime.now(timezone.utc), link_id))
                        c.execute(f"SELECT id FROM daily_stats WHERE link_id = {P} AND date = {P}", (link_id, today))
                        stat = c.fetchone()
                        if stat:
                            c.execute(f"UPDATE daily_stats SET clicks = clicks + {clicks} WHERE id = {P}", (stat[0],))
                        else:
                            c.execute(f"INSERT INTO daily_stats (link_id, date, clicks) VALUES ({P}, {P}, {P})", (link_id, today, clicks))
        except Exception as e:
            print(f"Error flushing analytics: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager to initialize DB and background tasks."""
    init_db()
    task = asyncio.create_task(flush_analytics())
    yield
    task.cancel()

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
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        role = payload.get("role", "user")
        
        if role == "admin":
            account = {"id": "admin", "username": "admin", "role": "admin"}
        else:
            with get_db() as conn:
                c = conn.cursor()
                c.execute(f"SELECT id, username FROM users WHERE id = {P}", (user_id,))
                user = c.fetchone()
                if not user:
                    raise HTTPException(status_code=401, detail="User not found")
                account = {"id": user[0], "username": user[1], "role": "user"}
                
        # Resolve active profile if header is present
        active_profile_username = request.headers.get("X-Active-Profile")
        active_profile = None
        if active_profile_username and role != "admin":
            with get_db() as conn:
                c = conn.cursor()
                c.execute(f"SELECT id, username, bio, tree_views, social_links FROM profiles WHERE user_id = {P} AND username = {P}", (account["id"], active_profile_username))
                prof = c.fetchone()
                if prof:
                    active_profile = {
                        "id": prof[0],
                        "username": prof[1],
                        "bio": prof[2],
                        "tree_views": prof[3],
                        "social_links": prof[4]
                    }
        
        return {"account": account, "active_profile": active_profile}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


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


class LoginRequest(BaseModel):
    username: str
    password: str

class CreateUserRequest(BaseModel):
    username: str
    password: str

class CreateProfileRequest(BaseModel):
    username: str
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError("Username must contain only letters, numbers, and hyphens")
        if v.lower() in RESERVED_CODES:
            raise ValueError(f"'{v}' is a reserved name and cannot be used")
        return v.lower()

class UpdateProfileRequest(BaseModel):
    username: str
    bio: Optional[str] = None
    social_links: Optional[List[dict]] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Username must be 3-30 characters")
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError(
                "Username must contain only letters, numbers, and hyphens (e.g. my-name-123, digital-creator)"
            )
        if v.lower() in RESERVED_CODES:
            raise ValueError(f"'{v}' is a reserved name and cannot be used")
        return v.lower()
        
    @field_validator("bio")
    @classmethod
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if "<" in v or ">" in v:
                raise ValueError("HTML is not allowed in bio")
            if len(v) > 500:
                raise ValueError("Bio must be 500 characters or fewer")
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


@app.post("/api/login")
def login(req: LoginRequest):
    if req.username == "admin" and config.ADMIN_PASSWORD_HASH and pwd_context.verify(req.password, config.ADMIN_PASSWORD_HASH):
        token = jwt.encode({"sub": "admin", "role": "admin"}, SECRET_KEY, algorithm=ALGORITHM)
        return {"token": token, "role": "admin", "profiles": []}
        
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT id, hashed_password FROM users WHERE username = {P}", (req.username,))
        user = c.fetchone()
        
        if not user or not pwd_context.verify(req.password, user[1]):
            raise HTTPException(status_code=401, detail="Invalid username or password")
            
        token = jwt.encode({"sub": str(user[0]), "role": "user"}, SECRET_KEY, algorithm=ALGORITHM)
        
        c.execute(f"SELECT username, bio, tree_views, social_links FROM profiles WHERE user_id = {P}", (user[0],))
        profiles_rows = c.fetchall()
        
        profiles = []
        for r in profiles_rows:
            sl = []
            if r[3]:
                try: sl = json.loads(r[3])
                except: pass
            profiles.append({
                "username": r[0],
                "bio": r[1],
                "tree_views": r[2],
                "social_links": sl
            })
            
    return {"token": token, "role": "user", "profiles": profiles}

@app.post("/api/admin/users")
def create_user(req: CreateUserRequest, user: dict = Depends(get_current_user)):
    if user["account"]["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    hashed_pw = pwd_context.hash(req.password)
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT id FROM users WHERE username = {P}", (req.username,))
        if c.fetchone():
            raise HTTPException(status_code=409, detail="Username already exists")
            
        c.execute(f"INSERT INTO users (username, hashed_password) VALUES ({P}, {P})", (req.username, hashed_pw))
        
    return {"message": "User created", "username": req.username}

@app.get("/api/admin/users")
def list_users(user: dict = Depends(get_current_user)):
    if user["account"]["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
        
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT id, username, created_at FROM users")
        users = []
        for r in c.fetchall():
            c.execute(f"SELECT COUNT(*) FROM profiles WHERE user_id = {P}", (r[0],))
            profile_count = c.fetchone()[0]
            users.append({
                "id": r[0],
                "username": r[1],
                "created_at": _fmt_dt(r[2]),
                "profile_count": profile_count
            })
    return {"users": users}


@app.get("/api/profiles")
def get_profiles(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT username, bio, tree_views, social_links FROM profiles WHERE user_id = {P}", (user["account"]["id"],))
        profiles_rows = c.fetchall()
        
        profiles = []
        for r in profiles_rows:
            sl = []
            if r[3]:
                try: sl = json.loads(r[3])
                except: pass
            profiles.append({
                "username": r[0],
                "bio": r[1],
                "tree_views": r[2],
                "social_links": sl
            })
    return {"profiles": profiles}

@app.post("/api/profiles")
def create_profile(req: CreateProfileRequest, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        c = conn.cursor()
        # Check limit
        c.execute(f"SELECT COUNT(*) FROM profiles WHERE user_id = {P}", (user["account"]["id"],))
        count = c.fetchone()[0]
        if count >= 5:
            raise HTTPException(status_code=400, detail="Maximum of 5 profiles allowed per account")
            
        # Check uniqueness
        c.execute(f"SELECT id FROM profiles WHERE username = {P}", (req.username,))
        if c.fetchone():
            raise HTTPException(status_code=409, detail="Username is already taken")
            
        c.execute(f"INSERT INTO profiles (user_id, username, bio, social_links) VALUES ({P}, {P}, NULL, NULL)", (user["account"]["id"], req.username))
        
    return {"message": "Profile created", "username": req.username, "bio": None, "social_links": []}


@app.get("/api/me")
def get_me(user: dict = Depends(get_current_user)):
    prof = user.get("active_profile")
    if not prof:
        raise HTTPException(status_code=400, detail="No active profile selected")
        
    social_links = []
    if prof["social_links"]:
        try:
            social_links = json.loads(prof["social_links"])
        except Exception:
            pass

    return {
        "username": prof["username"],
        "bio": prof["bio"],
        "tree_views": prof["tree_views"],
        "social_links": social_links
    }


@app.put("/api/me")
def update_me(req: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    prof = user.get("active_profile")
    if not prof:
        raise HTTPException(status_code=400, detail="No active profile selected")
        
    with get_db() as conn:
        c = conn.cursor()
        if req.username != prof["username"]:
            c.execute(f"SELECT id FROM profiles WHERE username = {P} AND id != {P}", (req.username, prof["id"]))
            if c.fetchone():
                raise HTTPException(status_code=409, detail="Username is already taken")
                
        social_links_str = json.dumps(req.social_links) if req.social_links is not None else None
        
        c.execute(
            f"UPDATE profiles SET username = {P}, bio = {P}, social_links = {P} WHERE id = {P}",
            (req.username, req.bio, social_links_str, prof["id"]),
        )
    return {"message": "Profile updated", "username": req.username, "bio": req.bio, "social_links": req.social_links}


@app.post("/api/shorten", response_model=ShortenResponse, status_code=201)
@limiter.limit(config.RATE_LIMIT)
def shorten_url(request: Request, req: ShortenRequest, user: dict = Depends(get_current_user)) -> ShortenResponse:
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None
        
    with get_db() as conn:
        c = conn.cursor()

        if not req.custom_code:
            if profile_id is not None:
                c.execute(f"SELECT short_code FROM urls WHERE original_url = {P} AND profile_id = {P}", (req.url, profile_id))
            else:
                c.execute(f"SELECT short_code FROM urls WHERE original_url = {P} AND profile_id IS NULL AND user_id = {P}", (req.url, user["account"]["id"]))
            
            existing = c.fetchone()
            if existing:
                return ShortenResponse(short_code=existing[0], original_url=req.url, already_exists=True)
            while True:
                short_code = generate_short_code()
                c.execute(f"SELECT id FROM urls WHERE short_code = {P}", (short_code,))
                if not c.fetchone():
                    break
        else:
            short_code = req.custom_code
            c.execute(f"SELECT id FROM urls WHERE short_code = {P}", (short_code,))
            if c.fetchone():
                raise HTTPException(status_code=409, detail="Custom short code already in use")

        c.execute(
            f"INSERT INTO urls (short_code, original_url, user_id, profile_id, title, show_on_tree) VALUES ({P}, {P}, {P}, {P}, {P}, {P})",
            (short_code, req.url, user["account"]["id"], profile_id, req.title, req.show_on_tree),
        )

    return ShortenResponse(short_code=short_code, original_url=req.url)


@app.get("/api/stats/{code}", response_model=AnalyticsResponse)
def get_stats(code: str, user: dict = Depends(get_current_user)) -> AnalyticsResponse:
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None
        
    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(
                f"SELECT original_url, title, show_on_tree, click_count, created_at, last_accessed "
                f"FROM urls WHERE short_code = {P} AND profile_id = {P}",
                (code, profile_id),
            )
        else:
            c.execute(
                f"SELECT original_url, title, show_on_tree, click_count, created_at, last_accessed "
                f"FROM urls WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}",
                (code, user["account"]["id"]),
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
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None
        
    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(
                f"SELECT short_code, original_url, title, show_on_tree, click_count, created_at, last_accessed "
                f"FROM urls WHERE profile_id = {P} ORDER BY created_at DESC",
                (profile_id,)
            )
        else:
            c.execute(
                f"SELECT short_code, original_url, title, show_on_tree, click_count, created_at, last_accessed "
                f"FROM urls WHERE profile_id IS NULL AND user_id = {P} ORDER BY created_at DESC",
                (user["account"]["id"],)
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


@app.get("/api/analytics", response_model=dict)
def get_analytics(user: dict = Depends(get_current_user)):
    """Fetches per-link analytics data for the active profile."""
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None
        
    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(f"SELECT id, short_code, title, click_count FROM urls WHERE profile_id = {P}", (profile_id,))
        else:
            c.execute(f"SELECT id, short_code, title, click_count FROM urls WHERE profile_id IS NULL AND user_id = {P}", (user["account"]["id"],))
        links = c.fetchall()
        
        analytics = []
        for link in links:
            link_id, code, title, total_clicks = link
            buffered = analytics_buffer.get(code, 0)
            
            c.execute(f"SELECT date, clicks FROM daily_stats WHERE link_id = {P} ORDER BY date ASC", (link_id,))
            daily = [{"date": r[0], "clicks": r[1]} for r in c.fetchall()]
            
            analytics.append({
                "short_code": code,
                "title": title or code,
                "total_clicks": total_clicks + buffered,
                "daily": daily
            })
            
    return {"analytics": analytics}


@app.delete("/api/links/{code}")
def delete_link(code: str, user: dict = Depends(get_current_user)):
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None
        
    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(f"SELECT id FROM urls WHERE short_code = {P} AND profile_id = {P}", (code, profile_id))
        else:
            c.execute(f"SELECT id FROM urls WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}", (code, user["account"]["id"]))
            
        if not c.fetchone():
            raise HTTPException(status_code=404, detail="Short code not found")
            
        if profile_id is not None:
            c.execute(f"DELETE FROM urls WHERE short_code = {P} AND profile_id = {P}", (code, profile_id))
        else:
            c.execute(f"DELETE FROM urls WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}", (code, user["account"]["id"]))
    return {"message": f"Deleted {code}"}


@app.put("/api/links/{code}")
def update_link(code: str, req: EditLinkRequest, user: dict = Depends(get_current_user)):
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None
        
    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(f"SELECT id FROM urls WHERE short_code = {P} AND profile_id = {P}", (code, profile_id))
        else:
            c.execute(f"SELECT id FROM urls WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}", (code, user["account"]["id"]))
            
        if not c.fetchone():
            raise HTTPException(status_code=404, detail="Short code not found")
            
        if profile_id is not None:
            c.execute(
                f"UPDATE urls SET original_url = {P}, title = {P}, show_on_tree = {P} WHERE short_code = {P} AND profile_id = {P}",
                (req.original_url, req.title, req.show_on_tree, code, profile_id),
            )
        else:
            c.execute(
                f"UPDATE urls SET original_url = {P}, title = {P}, show_on_tree = {P} WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}",
                (req.original_url, req.title, req.show_on_tree, code, user["account"]["id"]),
            )
    return {"message": f"Updated {code}", "original_url": req.original_url}


@app.get("/api/users/{username}/tree")
def get_user_tree(username: str):
    with get_db() as conn:
        c = conn.cursor()
        # Find profile
        c.execute(f"SELECT id, bio, social_links FROM profiles WHERE username = {P}", (username,))
        prof = c.fetchone()
        
        if not prof:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        prof_id = prof[0]
        bio = prof[1]
        social_links_raw = prof[2]
        
        # Increment tree views
        c.execute(f"UPDATE profiles SET tree_views = tree_views + 1 WHERE id = {P}", (prof_id,))
        
        # Fetch public links for tree
        c.execute(
            f"SELECT title, short_code, original_url FROM urls WHERE profile_id = {P} AND show_on_tree = {P} ORDER BY created_at DESC",
            (prof_id, True if _placeholder() == "%s" else 1)
        )
        rows = c.fetchall()
        
    social_links = []
    if social_links_raw:
        try:
            social_links = json.loads(social_links_raw)
        except Exception:
            pass

    return {
        "username": username,
        "bio": bio,
        "social_links": social_links,
        "links": [
            {
                "title": row[0] or row[2],
                "short_code": row[1],
                "url": f"/{row[1]}"
            }
            for row in rows
        ]
    }


@app.get("/{code}")
def redirect_url(code: str) -> RedirectResponse:
    """Redirects the user to the original URL and tracks analytics in the background."""
    if code in ["u"]:
        raise HTTPException(status_code=404)
        
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT original_url FROM urls WHERE short_code = {P}", (code,))
        result = c.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Short code not found")

        original_url = result[0]
        
    analytics_buffer[code] += 1

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
