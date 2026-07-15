import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi.errors import RateLimitExceeded

from src import config
from src.database import init_db
from src.dependencies import limiter
from src.analytics import flush_analytics
from src.routers import auth, admin, profiles, links, redirects


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager to initialize DB and background tasks."""
    init_db()
    task = asyncio.create_task(flush_analytics())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="URL Shortener API", lifespan=lifespan)
app.state.limiter = limiter

# Mount routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(profiles.router)
app.include_router(links.router)
app.include_router(redirects.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": {"code": 429, "message": "Rate limit exceeded. Try again later."}
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.status_code, "message": exc.detail}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = errors[0]["msg"] if errors else "Validation Error"
    return JSONResponse(
        status_code=422,
        content={"error": {"code": 422, "message": msg}},
    )


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


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
