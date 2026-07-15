from fastapi import APIRouter, HTTPException, Depends

from src.database import _placeholder, get_db
from src.schemas import CreateUserRequest
from src.dependencies import verify_admin, pwd_context
from src.utils import _fmt_dt

router = APIRouter(prefix="/api/admin")
P = _placeholder()


@router.post("/users", status_code=201)
def create_user(req: CreateUserRequest, user: dict = Depends(verify_admin)):
    if req.username.lower() == "admin":
        raise HTTPException(status_code=400, detail="Username 'admin' is reserved")
    hashed_pw = pwd_context.hash(req.password)
    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT id FROM users WHERE username = {P}", (req.username,))
        if c.fetchone():
            raise HTTPException(status_code=409, detail="Username already exists")

        c.execute(
            f"INSERT INTO users (username, hashed_password) VALUES ({P}, {P})",
            (req.username, hashed_pw),
        )

    return {"message": "User created", "username": req.username}


@router.get("/users")
def list_users(user: dict = Depends(verify_admin)):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT id, username, created_at FROM users")
        users = []
        for r in c.fetchall():
            c.execute(f"SELECT COUNT(*) FROM profiles WHERE user_id = {P}", (r[0],))
            profile_count = c.fetchone()[0]
            users.append(
                {
                    "id": r[0],
                    "username": r[1],
                    "created_at": _fmt_dt(r[2]),
                    "profile_count": profile_count,
                }
            )
    return {"users": users}
