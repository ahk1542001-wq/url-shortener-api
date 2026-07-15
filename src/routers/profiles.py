import json
import io
import uuid
import logging
import cloudinary
import cloudinary.uploader
from PIL import Image
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

from src.database import _placeholder, get_db
from src.schemas import CreateProfileRequest, UpdateProfileRequest
from src.dependencies import get_current_user
from src import config

logger = logging.getLogger(__name__)


def configure_cloudinary():
    if not all(
        [
            config.CLOUDINARY_CLOUD_NAME,
            config.CLOUDINARY_API_KEY,
            config.CLOUDINARY_API_SECRET,
        ]
    ):
        return False
    cloudinary.config(
        cloud_name=config.CLOUDINARY_CLOUD_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET,
        secure=True,
    )
    return True


router = APIRouter(prefix="/api")
P = _placeholder()


@router.get("/profiles")
def get_profiles(user: dict = Depends(get_current_user)):
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            f"SELECT username, bio, avatar_url, tree_views, social_links FROM profiles WHERE user_id = {P}",
            (user["account"]["id"],),
        )
        profiles_rows = c.fetchall()

        profiles = []
        for r in profiles_rows:
            sl = []
            if r[4]:
                try:
                    sl = json.loads(r[4])
                except Exception:
                    pass
            profiles.append(
                {
                    "username": r[0],
                    "bio": r[1],
                    "avatar_url": r[2],
                    "tree_views": r[3],
                    "social_links": sl,
                }
            )
    return {"profiles": profiles}


@router.post("/profiles")
def create_profile(req: CreateProfileRequest, user: dict = Depends(get_current_user)):
    with get_db() as conn:
        c = conn.cursor()
        # Check limit
        c.execute(
            f"SELECT COUNT(*) FROM profiles WHERE user_id = {P}",
            (user["account"]["id"],),
        )
        count = c.fetchone()[0]
        if count >= 5:
            raise HTTPException(
                status_code=400, detail="Maximum of 5 profiles allowed per account"
            )

        # Check uniqueness
        c.execute(f"SELECT id FROM profiles WHERE username = {P}", (req.username,))
        if c.fetchone():
            raise HTTPException(status_code=409, detail="Username is already taken")

        c.execute(
            f"INSERT INTO profiles (user_id, username, bio, social_links) VALUES ({P}, {P}, NULL, NULL)",
            (user["account"]["id"], req.username),
        )

    return {
        "message": "Profile created",
        "username": req.username,
        "bio": None,
        "social_links": [],
    }


@router.get("/me")
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
        "avatar_url": prof.get("avatar_url"),
        "tree_views": prof["tree_views"],
        "social_links": social_links,
    }


@router.put("/me")
def update_me(req: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    prof = user.get("active_profile")
    if not prof:
        raise HTTPException(status_code=400, detail="No active profile selected")

    with get_db() as conn:
        c = conn.cursor()
        if req.username != prof["username"]:
            c.execute(
                f"SELECT id FROM profiles WHERE username = {P} AND id != {P}",
                (req.username, prof["id"]),
            )
            if c.fetchone():
                raise HTTPException(status_code=409, detail="Username is already taken")

        social_links_str = (
            json.dumps([link.model_dump() for link in req.social_links])
            if req.social_links is not None
            else None
        )

        c.execute(
            f"UPDATE profiles SET username = {P}, bio = {P}, social_links = {P} WHERE id = {P}",
            (req.username, req.bio, social_links_str, prof["id"]),
        )
    return {
        "message": "Profile updated",
        "username": req.username,
        "bio": req.bio,
        "social_links": req.social_links,
    }


@router.post("/profiles/avatar")
def upload_avatar(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    prof = user.get("active_profile")
    if not prof:
        raise HTTPException(status_code=400, detail="No active profile selected")

    # Read and limit size to 2MB
    file_bytes = file.file.read(2 * 1024 * 1024 + 1)
    if len(file_bytes) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail="File too large. Maximum size is 2MB."
        )

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.verify()  # verify format

        # reopen to process
        img = Image.open(io.BytesIO(file_bytes))

        if img.width > 2048 or img.height > 2048:
            raise HTTPException(status_code=400, detail="Image dimensions too large.")

        # Re-encode as safe JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        out_bytes = io.BytesIO()
        img.save(out_bytes, format="JPEG", quality=85)
        out_bytes.seek(0)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    if not configure_cloudinary():
        raise HTTPException(status_code=500, detail="Cloud storage not configured.")

    public_id = f"avatars/{uuid.uuid4()}"

    try:
        upload_result = cloudinary.uploader.upload(
            out_bytes,
            public_id=public_id,
            resource_type="image",
            format="jpg",
            overwrite=False,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to upload image.")

    avatar_url = upload_result.get("secure_url")
    stored_public_id = upload_result.get("public_id")
    if not avatar_url or not stored_public_id:
        try:
            cloudinary.uploader.destroy(
                public_id, resource_type="image", invalidate=True
            )
        except Exception:
            logger.exception("Failed to clean up an invalid Cloudinary upload")
        raise HTTPException(status_code=500, detail="Failed to upload image.")

    # DB update
    old_key = None
    try:
        with get_db() as conn:
            c = conn.cursor()
            c.execute(
                f"SELECT avatar_object_key FROM profiles WHERE id = {P}", (prof["id"],)
            )
            old_row = c.fetchone()
            if old_row:
                old_key = old_row[0]

            c.execute(
                f"UPDATE profiles SET avatar_url = {P}, avatar_object_key = {P} WHERE id = {P}",
                (avatar_url, stored_public_id, prof["id"]),
            )
    except Exception:
        # DB failed, roll back the Cloudinary upload.
        try:
            cloudinary.uploader.destroy(
                stored_public_id, resource_type="image", invalidate=True
            )
        except Exception:
            logger.exception("Failed to roll back Cloudinary avatar upload")
        raise HTTPException(status_code=500, detail="Database update failed.")

    # Success, now try to delete old object
    if old_key:
        try:
            cloudinary.uploader.destroy(old_key, resource_type="image", invalidate=True)
        except Exception:
            logger.exception("Failed to delete old Cloudinary avatar %s", old_key)

    return {"message": "Avatar uploaded successfully", "avatar_url": avatar_url}


@router.get("/users/{username}/tree")
def get_user_tree(username: str):
    with get_db() as conn:
        c = conn.cursor()
        # Find profile
        c.execute(
            f"SELECT id, bio, avatar_url, social_links FROM profiles WHERE username = {P}",
            (username,),
        )
        prof = c.fetchone()

        if not prof:
            raise HTTPException(status_code=404, detail="Profile not found")

        prof_id = prof[0]
        bio = prof[1]
        avatar_url = prof[2]
        social_links_raw = prof[3]

        # Increment tree views
        c.execute(
            f"UPDATE profiles SET tree_views = tree_views + 1 WHERE id = {P}",
            (prof_id,),
        )

        # Fetch links that should be shown on the tree
        c.execute(
            f"SELECT short_code, original_url, title "
            f"FROM links WHERE profile_id = {P} AND show_on_tree = {P} ORDER BY created_at DESC",
            (prof_id, True),
        )
        tree_links_rows = c.fetchall()

    social_links = []
    if social_links_raw:
        try:
            social_links = json.loads(social_links_raw)
        except Exception:
            pass

    tree_links = []
    for row in tree_links_rows:
        tree_links.append(
            {"short_code": row[0], "original_url": row[1], "title": row[2] or row[0]}
        )

    return {
        "username": username,
        "bio": bio,
        "avatar_url": avatar_url,
        "social_links": social_links,
        "tree_links": tree_links,
    }
