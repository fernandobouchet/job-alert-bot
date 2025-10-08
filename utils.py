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
    """Filtra solo las ofertas publicadas en las últimas 24 horas."""
    now = datetime.now(timezone.utc)
    recent_jobs = []

    for job in jobs:
        published_str = job.get("published_at")
        if not published_str:
            continue

        try:
            # Parsear string ISO a datetime (timezone-aware)
            published_at = datetime.fromisoformat(published_str)
        except ValueError:
            # Si falla el parseo, descartar el job
            continue

        if published_at >= now - timedelta(hours=24):
            recent_jobs.append(job)

    return recent_jobs

def parse_date_to_iso_utc(date_str: str, fmt: str) -> str | None:
    try:
        dt = datetime.strptime(date_str, fmt)
        dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        return None