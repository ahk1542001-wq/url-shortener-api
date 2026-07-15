from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from src.database import _placeholder, get_db
from src.analytics import analytics_buffer

router = APIRouter()
P = _placeholder()


@router.get("/{code}")
def redirect_url(code: str) -> RedirectResponse:
    """Redirects the user to the original URL and tracks analytics in the background."""
    if code in ["u"]:
        raise HTTPException(status_code=404)

    with get_db() as conn:
        c = conn.cursor()
        c.execute(f"SELECT original_url FROM links WHERE short_code = {P}", (code,))
        result = c.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Short code not found")

        original_url = result[0]

    analytics_buffer[code] += 1

    return RedirectResponse(url=original_url, status_code=302)
