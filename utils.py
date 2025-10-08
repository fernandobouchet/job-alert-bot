import re
from datetime import datetime, timezone, timedelta

def clean_text(text):
    """Elimina HTML y exceso de espacios."""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def filter_last_24h(jobs):
    """Filtra los jobs publicados en las últimas 24 horas."""
    now = datetime.now(timezone.utc)
    filtered = []

    for job in jobs:
        published_ts = job.get("published_at")
        if not published_ts:
            continue

        published_at = datetime.fromtimestamp(published_ts, tz=timezone.utc)

        if published_at >= now - timedelta(days=1):
            job["published_at_str"] = published_at.strftime("%Y-%m-%d %H:%M:%S")
            filtered.append(job)

    return filtered