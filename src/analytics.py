import asyncio
import logging
from datetime import datetime, timezone
from collections import defaultdict
from src.database import _placeholder, get_db

logger = logging.getLogger(__name__)

P = _placeholder()
analytics_buffer = defaultdict(int)


def _flush_now():
    if not analytics_buffer:
        return

    to_flush = dict(analytics_buffer)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with get_db() as conn:
        c = conn.cursor()
        for code, clicks in to_flush.items():
            c.execute(f"SELECT id FROM links WHERE short_code = {P}", (code,))
            result = c.fetchone()
            if result:
                link_id = result[0]
                c.execute(
                    f"UPDATE links SET click_count = click_count + {P}, last_accessed = {P} WHERE id = {P}",
                    (clicks, datetime.now(timezone.utc), link_id),
                )
                c.execute(
                    f"SELECT id FROM daily_stats WHERE link_id = {P} AND date = {P}",
                    (link_id, today),
                )
                stat = c.fetchone()
                if stat:
                    c.execute(
                        f"UPDATE daily_stats SET clicks = clicks + {P} WHERE id = {P}",
                        (clicks, stat[0]),
                    )
                else:
                    c.execute(
                        f"INSERT INTO daily_stats (link_id, date, clicks) VALUES ({P}, {P}, {P})",
                        (link_id, today, clicks),
                    )

        for code, clicks in to_flush.items():
            analytics_buffer[code] -= clicks
            if analytics_buffer[code] <= 0:
                del analytics_buffer[code]


async def flush_analytics():
    """Background task to flush in-memory analytics to SQLite every 10 seconds."""
    try:
        while True:
            await asyncio.sleep(10)
            try:
                _flush_now()
            except Exception as e:
                logger.error(f"Error flushing analytics: {e}")
    except asyncio.CancelledError:
        logger.info("Analytics flush cancelled, doing final flush...")
        try:
            _flush_now()
        except Exception as e:
            logger.error(f"Error in final analytics flush: {e}")
