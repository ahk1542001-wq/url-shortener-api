import logging

import cloudinary.uploader
from fastapi import APIRouter, HTTPException, Depends

from src.database import _placeholder, get_db
from src.schemas import CreateUserRequest, UpdateAdminUserRequest
from src.dependencies import verify_admin, pwd_context
from src.routers.profiles import configure_cloudinary
from src.utils import _fmt_dt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin")
P = _placeholder()


def _get_user_row(cursor, user_id: int):
    cursor.execute(
        f"SELECT id, username, is_active, created_at FROM users WHERE id = {P}",
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return row


def _build_user_detail(conn, user_id: int) -> dict:
    cursor = conn.cursor()
    row = _get_user_row(cursor, user_id)

    cursor.execute(
        f"SELECT COUNT(*), COALESCE(SUM(click_count), 0) FROM links WHERE user_id = {P}",
        (user_id,),
    )
    link_count, total_clicks = cursor.fetchone()

    cursor.execute(
        f"SELECT COUNT(*) FROM links WHERE user_id = {P} AND profile_id IS NULL",
        (user_id,),
    )
    standalone_link_count = cursor.fetchone()[0]

    cursor.execute(
        f"SELECT id, username, bio, tree_views, created_at FROM profiles WHERE user_id = {P} ORDER BY created_at, id",
        (user_id,),
    )
    profiles = []
    for profile in cursor.fetchall():
        cursor.execute(
            f"SELECT COUNT(*), COALESCE(SUM(click_count), 0) FROM links WHERE profile_id = {P}",
            (profile[0],),
        )
        profile_link_count, profile_clicks = cursor.fetchone()
        profiles.append(
            {
                "id": profile[0],
                "username": profile[1],
                "bio": profile[2],
                "tree_views": profile[3] or 0,
                "created_at": _fmt_dt(profile[4]),
                "link_count": profile_link_count,
                "total_clicks": profile_clicks or 0,
            }
        )

    return {
        "id": row[0],
        "username": row[1],
        "is_active": bool(row[2]),
        "created_at": _fmt_dt(row[3]),
        "profile_count": len(profiles),
        "link_count": link_count,
        "standalone_link_count": standalone_link_count,
        "total_clicks": total_clicks or 0,
        "profiles": profiles,
        "is_admin": row[1].lower() == "admin",
    }


@router.post("/users", status_code=201)
def create_user(req: CreateUserRequest, user: dict = Depends(verify_admin)):
    if req.username.lower() == "admin":
        raise HTTPException(status_code=400, detail="Username 'admin' is reserved")
    hashed_pw = pwd_context.hash(req.password)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT id FROM users WHERE LOWER(username) = LOWER({P})",
            (req.username,),
        )
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="Username already exists")

        cursor.execute(
            f"INSERT INTO users (username, hashed_password, is_active) VALUES ({P}, {P}, {P})",
            (req.username, hashed_pw, True),
        )

    return {"message": "User created", "username": req.username}


@router.get("/users")
def list_users(user: dict = Depends(verify_admin)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, is_active, created_at FROM users ORDER BY created_at, id"
        )
        users = []
        for row in cursor.fetchall():
            cursor.execute(
                f"SELECT COUNT(*) FROM profiles WHERE user_id = {P}", (row[0],)
            )
            profile_count = cursor.fetchone()[0]
            cursor.execute(
                f"SELECT COUNT(*), COALESCE(SUM(click_count), 0) FROM links WHERE user_id = {P}",
                (row[0],),
            )
            link_count, total_clicks = cursor.fetchone()
            users.append(
                {
                    "id": row[0],
                    "username": row[1],
                    "is_active": bool(row[2]),
                    "created_at": _fmt_dt(row[3]),
                    "profile_count": profile_count,
                    "link_count": link_count,
                    "total_clicks": total_clicks or 0,
                    "is_admin": row[1].lower() == "admin",
                }
            )
    return {"users": users}


@router.get("/users/{user_id}")
def get_user_detail(user_id: int, user: dict = Depends(verify_admin)):
    with get_db() as conn:
        return {"user": _build_user_detail(conn, user_id)}


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    req: UpdateAdminUserRequest,
    user: dict = Depends(verify_admin),
):
    with get_db() as conn:
        cursor = conn.cursor()
        current = _get_user_row(cursor, user_id)
        if current[1].lower() == "admin":
            raise HTTPException(
                status_code=400,
                detail="The environment-managed admin account cannot be edited here",
            )

        updates = []
        values = []
        if req.username is not None and req.username != current[1]:
            if req.username.lower() == "admin":
                raise HTTPException(
                    status_code=400, detail="Username 'admin' is reserved"
                )
            cursor.execute(
                f"SELECT id FROM users WHERE LOWER(username) = LOWER({P}) AND id != {P}",
                (req.username, user_id),
            )
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="Username already exists")
            updates.append(f"username = {P}")
            values.append(req.username)

        if req.password is not None:
            updates.append(f"hashed_password = {P}")
            values.append(pwd_context.hash(req.password))

        if req.is_active is not None:
            updates.append(f"is_active = {P}")
            values.append(req.is_active)

        if updates:
            values.append(user_id)
            cursor.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = {P}",
                tuple(values),
            )

    with get_db() as conn:
        return {"message": "User updated", "user": _build_user_detail(conn, user_id)}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, user: dict = Depends(verify_admin)):
    avatar_object_keys = []
    with get_db() as conn:
        cursor = conn.cursor()
        current = _get_user_row(cursor, user_id)
        if current[1].lower() == "admin":
            raise HTTPException(
                status_code=400,
                detail="The environment-managed admin account cannot be deleted",
            )

        cursor.execute(
            f"SELECT avatar_object_key FROM profiles WHERE user_id = {P} AND avatar_object_key IS NOT NULL",
            (user_id,),
        )
        avatar_object_keys = [row[0] for row in cursor.fetchall() if row[0]]

        cursor.execute(
            f"DELETE FROM daily_stats WHERE link_id IN (SELECT id FROM links WHERE user_id = {P})",
            (user_id,),
        )
        cursor.execute(f"DELETE FROM links WHERE user_id = {P}", (user_id,))
        cursor.execute(f"DELETE FROM profiles WHERE user_id = {P}", (user_id,))
        cursor.execute(f"DELETE FROM users WHERE id = {P}", (user_id,))

    if avatar_object_keys and configure_cloudinary():
        for object_key in avatar_object_keys:
            try:
                cloudinary.uploader.destroy(object_key, invalidate=True)
            except Exception:
                logger.warning(
                    "Failed to delete Cloudinary avatar for deleted user",
                    exc_info=True,
                )

    return {"message": "User and owned application data deleted"}
