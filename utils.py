import re
import math
from config import TAGS_KEYWORDS
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


def is_job_recent(published_at_iso: str, hours_threshold: int = 24) -> bool:
    if not published_at_iso:
        return False

    now = datetime.now(timezone.utc)
    time_threshold = now - timedelta(hours=hours_threshold)

    try:
        published_dt = datetime.fromisoformat(published_at_iso).replace(
            tzinfo=timezone.utc
        )

        return published_dt >= time_threshold

    except Exception:
        return False


def safe_parse_date_to_ISO(d):
    now = datetime.now(timezone.utc)

    if d is None or (isinstance(d, float) and math.isnan(d)):
        dt = now - timedelta(hours=1)
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    if isinstance(d, (int, float)):
        try:
            dt = datetime.fromtimestamp(d, tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        except Exception:
            return now.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    if isinstance(d, str):
        d_lower = d.lower()
        try:
            if "hour" in d_lower or "hora" in d_lower:
                hours = int(re.search(r"\d+", d).group())
                dt = now - timedelta(hours=hours)
                return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            elif "day" in d_lower or "día" in d_lower:
                days = int(re.search(r"\d+", d).group())
                dt = now - timedelta(days=days)
                return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            elif "week" in d_lower or "semana" in d_lower:
                weeks = int(re.search(r"\d+", d).group())
                dt = now - timedelta(weeks=weeks)
                return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        except (ValueError, AttributeError):
            pass

        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%d-%m-%Y",
        ):
            try:
                dt = datetime.strptime(d, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            except ValueError:
                continue

    if isinstance(d, datetime):
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    if isinstance(d, date):
        dt = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    return now.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def extract_tags(title, description):

    text = f"{title} {description}".lower()

    found_tags = []
    for kw in TAGS_KEYWORDS:
        # Usa \b (límite de palabra) y re.escape para buscar la palabra completa
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text):
            found_tags.append(kw)

    return found_tags
