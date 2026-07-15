import json
import jwt
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException

from src import config
from src.database import _placeholder, get_db
from src.schemas import LoginRequest
from src.dependencies import pwd_context, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api")
P = _placeholder()


@router.post("/login")
def login(req: LoginRequest):
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=24)

    if (
        req.username == "admin"
        and config.ADMIN_PASSWORD_HASH
        and pwd_context.verify(req.password, config.ADMIN_PASSWORD_HASH)
    ):
        token = jwt.encode(
            {"sub": "admin", "role": "admin", "iat": now, "exp": exp},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        return {"token": token, "role": "admin", "profiles": []}

    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            f"SELECT id, hashed_password FROM users WHERE username = {P}",
            (req.username,),
        )
        user = c.fetchone()

        if not user or not pwd_context.verify(req.password, user[1]):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        token = jwt.encode(
            {"sub": str(user[0]), "role": "user", "iat": now, "exp": exp},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )

        c.execute(
            f"SELECT username, bio, tree_views, social_links FROM profiles WHERE user_id = {P}",
            (user[0],),
        )
        profiles_rows = c.fetchall()

        profiles = []
        for r in profiles_rows:
            sl = []
            if r[3]:
                try:
                    sl = json.loads(r[3])
                except Exception:
                    pass
            profiles.append(
                {"username": r[0], "bio": r[1], "tree_views": r[2], "social_links": sl}
            )

    return {"token": token, "role": "user", "profiles": profiles}
