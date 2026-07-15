import jwt
from fastapi import HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from passlib.context import CryptContext

from src import config
from src.database import _placeholder, get_db, USE_POSTGRES

P = _placeholder()

SECRET_KEY = config.JWT_SECRET
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

limiter = Limiter(key_func=get_remote_address, default_limits=[config.RATE_LIMIT])


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
            with get_db() as conn:
                c = conn.cursor()
                if USE_POSTGRES:
                    c.execute(
                        "SELECT id FROM users WHERE LOWER(username) = LOWER(%s) AND is_active = TRUE",
                        ("admin",),
                    )
                else:
                    c.execute(
                        "SELECT id FROM users WHERE LOWER(username) = LOWER(?) AND is_active = 1",
                        ("admin",),
                    )
                row = c.fetchone()
                if not row:
                    raise HTTPException(status_code=401, detail="Admin user not found")
                admin_id = row[0]
            account = {"id": admin_id, "username": "admin", "role": "admin"}
        else:
            with get_db() as conn:
                c = conn.cursor()
                c.execute(
                    f"SELECT id, username, is_active FROM users WHERE id = {P}",
                    (user_id,),
                )
                user = c.fetchone()
                if not user or not user[2]:
                    raise HTTPException(status_code=401, detail="User not found")
                account = {"id": user[0], "username": user[1], "role": "user"}

        # Resolve active profile if header is present
        active_profile_username = request.headers.get("X-Active-Profile")
        active_profile = None
        if active_profile_username:
            with get_db() as conn:
                c = conn.cursor()
                c.execute(
                    f"SELECT id, username, bio, avatar_url, tree_views, social_links FROM profiles WHERE user_id = {P} AND username = {P}",
                    (account["id"], active_profile_username),
                )
                prof = c.fetchone()
                if prof:
                    active_profile = {
                        "id": prof[0],
                        "username": prof[1],
                        "bio": prof[2],
                        "avatar_url": prof[3],
                        "tree_views": prof[4],
                        "social_links": prof[5],
                    }

        return {"account": account, "active_profile": active_profile}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def verify_admin(current_user: dict = Depends(get_current_user)):
    # Depending on how it's used, current_user can be passed in from Depends
    if not current_user or current_user.get("account", {}).get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
