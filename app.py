import sqlite3
import string
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
import os

app = FastAPI(title="URL Shortener API")
DB_NAME = "shortener.db"

# Pydantic models for validation
class ShortenRequest(BaseModel):
    url: str
    custom_code: str = None

class ShortenResponse(BaseModel):
    short_code: str
    original_url: str

class AnalyticsResponse(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    created_at: str
    last_accessed: str

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_code TEXT UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            click_count INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_accessed DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/api/shorten", response_model=ShortenResponse, status_code=201)
def shorten_url(req: ShortenRequest):
    if not req.url.startswith("http://") and not req.url.startswith("https://"):
        raise HTTPException(status_code=422, detail="Invalid URL format. Must start with http:// or https://")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if req.custom_code:
        short_code = req.custom_code
        c.execute('SELECT id FROM urls WHERE short_code = ?', (short_code,))
        if c.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="Custom short code already in use")
    else:
        while True:
            short_code = generate_short_code()
            c.execute('SELECT id FROM urls WHERE short_code = ?', (short_code,))
            if not c.fetchone():
                break

    c.execute(
        'INSERT INTO urls (short_code, original_url) VALUES (?, ?)',
        (short_code, req.url)
    )
    conn.commit()
    conn.close()

    return ShortenResponse(short_code=short_code, original_url=req.url)

@app.get("/api/stats/{code}", response_model=AnalyticsResponse)
def get_stats(code: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT original_url, click_count, created_at, last_accessed FROM urls WHERE short_code = ?', (code,))
    result = c.fetchone()
    conn.close()

    if not result:
        raise HTTPException(status_code=404, detail="Short code not found")

    return AnalyticsResponse(
        short_code=code,
        original_url=result[0],
        click_count=result[1],
        created_at=result[2],
        last_accessed=result[3] if result[3] else "Never"
    )

@app.get("/{code}")
def redirect_url(code: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, original_url FROM urls WHERE short_code = ?', (code,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        raise HTTPException(status_code=404, detail="Short code not found")
        
    db_id, original_url = result
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    c.execute('UPDATE urls SET click_count = click_count + 1, last_accessed = ? WHERE id = ?', (now, db_id))
    conn.commit()
    conn.close()

    return RedirectResponse(url=original_url, status_code=302)

# Serve static files for frontend UI
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
