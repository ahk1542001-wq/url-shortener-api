import string
import random
from datetime import datetime


def _fmt_dt(val) -> str:
    if val is None:
        return "Never"
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(val, str):
        # sqlite
        try:
            val = datetime.fromisoformat(val)
        except ValueError:
            pass
    return str(val)


def generate_short_code(length: int = 6) -> str:
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))
