import re
import math
from datetime import datetime, timezone, timedelta, date


def clean_text(text):
    """Elimina HTML y exceso de espacios."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def filter_last_24h(jobs):
    """Filtra jobs publicados en las últimas 24h"""
    now = datetime.now(timezone.utc)
    filtered = []
    for job in jobs:
        pub = job.get("published_at")
        if not pub:
            continue
        try:
            dt = datetime.fromisoformat(pub)
            if dt >= now - timedelta(days=1):
                filtered.append(job)
        except Exception:
            continue
    return filtered


def safe_parse_date_to_ISO(d):
    if d is None or (isinstance(d, float) and math.isnan(d)):
        # Valor nulo o NaN → usar fecha actual UTC
        return datetime.now(timezone.utc).isoformat()

    if isinstance(d, str):
        try:
            return datetime.fromisoformat(d).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            try:
                return (
                    datetime.strptime(d, "%Y-%m-%d")
                    .replace(tzinfo=timezone.utc)
                    .isoformat()
                )
            except ValueError:
                return datetime.now(timezone.utc).isoformat()

    if isinstance(d, datetime):
        return d.replace(tzinfo=timezone.utc).isoformat()

    if isinstance(d, date):
        return datetime(d.year, d.month, d.day, tzinfo=timezone.utc).isoformat()

    # fallback
    return datetime.now(timezone.utc).isoformat()
