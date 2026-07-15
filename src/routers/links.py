from fastapi import APIRouter, HTTPException, Depends, Request

from src import config
from src.database import _placeholder, get_db
from src.schemas import (
    ShortenRequest,
    ShortenResponse,
    AnalyticsResponse,
    EditLinkRequest,
)
from src.dependencies import get_current_user, limiter
from src.utils import _fmt_dt, generate_short_code
from src.analytics import analytics_buffer

router = APIRouter(prefix="/api")
P = _placeholder()


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
@limiter.limit(config.RATE_LIMIT)
def shorten_url(
    request: Request, req: ShortenRequest, user: dict = Depends(get_current_user)
) -> ShortenResponse:
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None

    with get_db() as conn:
        c = conn.cursor()

        if not req.custom_code:
            if profile_id is not None:
                c.execute(
                    f"SELECT short_code FROM links WHERE original_url = {P} AND profile_id = {P}",
                    (req.url, profile_id),
                )
            else:
                c.execute(
                    f"SELECT short_code FROM links WHERE original_url = {P} AND profile_id IS NULL AND user_id = {P}",
                    (req.url, user["account"]["id"]),
                )

            existing = c.fetchone()
            if existing:
                return ShortenResponse(
                    short_code=existing[0], original_url=req.url, already_exists=True
                )
            while True:
                short_code = generate_short_code()
                c.execute(f"SELECT id FROM links WHERE short_code = {P}", (short_code,))
                if not c.fetchone():
                    break
        else:
            short_code = req.custom_code
            c.execute(f"SELECT id FROM links WHERE short_code = {P}", (short_code,))
            if c.fetchone():
                raise HTTPException(
                    status_code=409, detail="Custom short code already in use"
                )

        c.execute(
            f"INSERT INTO links (short_code, original_url, user_id, profile_id, title, show_on_tree) VALUES ({P}, {P}, {P}, {P}, {P}, {P})",
            (
                short_code,
                req.url,
                user["account"]["id"],
                profile_id,
                req.title,
                req.show_on_tree,
            ),
        )

    return ShortenResponse(short_code=short_code, original_url=req.url)


@router.get("/stats/{code}", response_model=AnalyticsResponse)
def get_stats(code: str, user: dict = Depends(get_current_user)) -> AnalyticsResponse:
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None

    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(
                f"SELECT original_url, click_count, created_at, last_accessed "
                f"FROM links WHERE short_code = {P} AND profile_id = {P}",
                (code, profile_id),
            )
        else:
            c.execute(
                f"SELECT original_url, click_count, created_at, last_accessed "
                f"FROM links WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}",
                (code, user["account"]["id"]),
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


@router.get("/links")
def list_links(user: dict = Depends(get_current_user)):
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None

    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(
                f"SELECT short_code, original_url, click_count, created_at, last_accessed, title, show_on_tree "
                f"FROM links WHERE profile_id = {P} ORDER BY created_at DESC",
                (profile_id,),
            )
        else:
            c.execute(
                f"SELECT short_code, original_url, click_count, created_at, last_accessed, title, show_on_tree "
                f"FROM links WHERE profile_id IS NULL AND user_id = {P} ORDER BY created_at DESC",
                (user["account"]["id"],),
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
                "title": row[5],
                "show_on_tree": bool(row[6]),
            }
            for row in rows
        ]
    }


@router.get("/analytics", response_model=dict)
def get_analytics(user: dict = Depends(get_current_user)):
    """Fetches per-link analytics data for the active profile."""
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None

    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(
                f"SELECT id, short_code, click_count FROM links WHERE profile_id = {P}",
                (profile_id,),
            )
        else:
            c.execute(
                f"SELECT id, short_code, click_count FROM links WHERE profile_id IS NULL AND user_id = {P}",
                (user["account"]["id"],),
            )
        links = c.fetchall()

        analytics = []
        for link in links:
            link_id, code, total_clicks = link
            buffered = analytics_buffer.get(code, 0)

            c.execute(
                f"SELECT date, clicks FROM daily_stats WHERE link_id = {P} ORDER BY date ASC",
                (link_id,),
            )
            daily = [{"date": r[0], "clicks": r[1]} for r in c.fetchall()]

            analytics.append(
                {
                    "short_code": code,
                    "title": code,
                    "total_clicks": total_clicks + buffered,
                    "daily": daily,
                }
            )

    return {"analytics": analytics}


@router.delete("/links/{code}")
def delete_link(code: str, user: dict = Depends(get_current_user)):
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None

    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(
                f"SELECT id FROM links WHERE short_code = {P} AND profile_id = {P}",
                (code, profile_id),
            )
        else:
            c.execute(
                f"SELECT id FROM links WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}",
                (code, user["account"]["id"]),
            )

        if not c.fetchone():
            raise HTTPException(status_code=404, detail="Short code not found")

        if profile_id is not None:
            c.execute(
                f"DELETE FROM links WHERE short_code = {P} AND profile_id = {P}",
                (code, profile_id),
            )
        else:
            c.execute(
                f"DELETE FROM links WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}",
                (code, user["account"]["id"]),
            )
    return {"message": f"Deleted {code}"}


@router.put("/links/{code}")
def update_link(
    code: str, req: EditLinkRequest, user: dict = Depends(get_current_user)
):
    prof = user.get("active_profile")
    profile_id = prof["id"] if prof else None

    with get_db() as conn:
        c = conn.cursor()
        if profile_id is not None:
            c.execute(
                f"SELECT id FROM links WHERE short_code = {P} AND profile_id = {P}",
                (code, profile_id),
            )
        else:
            c.execute(
                f"SELECT id FROM links WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}",
                (code, user["account"]["id"]),
            )

        if not c.fetchone():
            raise HTTPException(status_code=404, detail="Short code not found")

        if profile_id is not None:
            c.execute(
                f"UPDATE links SET original_url = {P}, title = {P}, show_on_tree = {P} WHERE short_code = {P} AND profile_id = {P}",
                (req.original_url, req.title, req.show_on_tree, code, profile_id),
            )
        else:
            c.execute(
                f"UPDATE links SET original_url = {P}, title = {P}, show_on_tree = {P} WHERE short_code = {P} AND profile_id IS NULL AND user_id = {P}",
                (
                    req.original_url,
                    req.title,
                    req.show_on_tree,
                    code,
                    user["account"]["id"],
                ),
            )
    return {"message": f"Updated {code}", "original_url": req.original_url}
