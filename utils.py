import re
import math
import asyncio
import pandas as pd
try:
    from config import (
        DAYS_OLD_TRHESHOLD,
        HOURS_OLD_THRESHOLD,
        TIMEZONE
    )
except ImportError:
    TIMEZONE = "UTC"
import zoneinfo
from datetime import datetime, timezone, timedelta, date
from filters_scoring import filter_jobs_with_scoring
from json_handler import update_job_data
from bot.utils import send_jobs
from filters_scoring_config import TAGS_KEYWORDS


async def scrape(sources, chat_id, bot):
    print("🚀 Iniciando búsqueda de trabajos...")
    tasks = [asyncio.to_thread(source_func) for source_func in sources]
    results = await asyncio.gather(*tasks)

    all_jobs = [job for result in results for job in result]

    if not all_jobs:
        print("No se obtuvieron trabajos de ninguna fuente.")
        return

    df = pd.DataFrame(all_jobs)

    df_filtered = filter_jobs_with_scoring(df, min_score=50, verbose=True)

    if df_filtered.empty:
        print("No se encontraron trabajos nuevos con los filtros aplicados.")
        return

    recent_jobs = updateDataFrame(df_filtered)

    if not recent_jobs:
        print("No hay trabajos nuevos para enviar.")
        return

    new_jobs = update_job_data(recent_jobs)

    if new_jobs:
        print(f"✅ Se encontraron {len(new_jobs)} jobs nuevos. Enviando a Telegram...")
        await send_jobs(bot, chat_id, new_jobs)
    else:
        print("No hay jobs nuevos para enviar.")


def safe_parse_date_to_ISO(d):
    now = datetime.now(zoneinfo.ZoneInfo(TIMEZONE))

    if d is None or (isinstance(d, float) and math.isnan(d)):
        dt = now - timedelta(hours=1)
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    if isinstance(d, (int, float)):
        try:
            dt = datetime.fromtimestamp(d, tz=zoneinfo.ZoneInfo(TIMEZONE))
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
                    dt = dt.replace(tzinfo=zoneinfo.ZoneInfo(TIMEZONE))
                return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
            except ValueError:
                continue

    if isinstance(d, datetime):
        if d.tzinfo is None:
            d = d.replace(tzinfo=zoneinfo.ZoneInfo(TIMEZONE))
        return d.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    if isinstance(d, date):
        dt = datetime(d.year, d.month, d.day, tzinfo=zoneinfo.ZoneInfo(TIMEZONE))
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    return now.strftime("%Y-%m-%dT%H:%M:%S+00:00")


def updateDataFrame(df):

    df["dedupe_key"] = (
        df["title"].str.lower().str.strip()
        + "|"
        + df["company"].str.lower().str.strip()
    )
    df.drop_duplicates(subset=["dedupe_key"], inplace=True)
    df.drop(columns=["dedupe_key"], inplace=True)

    cutoff = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(hours=HOURS_OLD_THRESHOLD)

    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")

    df = df.dropna(subset=["published_at"])

    df = df[df["published_at"] >= cutoff].copy()

    if df.empty:
        print("No hay trabajos recientes o únicos para procesar.")
        return []
    print(f"Total de jobs únicos y recientes: {len(df)}")

    df["text_for_extraction"] = (
        df["title"].fillna("").astype(str)
        + " "
        + df["description"].fillna("").astype(str)
    )

    df["tags"] = df["text_for_extraction"].apply(extract_tags)
    df["modality"] = df["text_for_extraction"].apply(extract_job_modality)

    df.drop(columns=["text_for_extraction"], inplace=True)

    current_time_iso = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    df["date_scraped"] = current_time_iso

    df["published_at"] = df["published_at"].dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    recent_jobs = df.to_dict(orient="records")

    return recent_jobs


def extract_tags(text_for_extraction):

    text = text_for_extraction.lower()

    found_tags = []
    for kw in TAGS_KEYWORDS:
        pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
        if re.search(pattern, text, re.IGNORECASE):
            found_tags.append(kw)

    return found_tags


def extract_job_modality(text_for_extraction):
    text = text_for_extraction.lower()

    if re.search(
        r"\b(100%\s*(on-site|onsite|presencial)|exclusivamente\s*presencial)\b", text
    ):
        return "On-site"

    remote_terms = (
        r"\b(remoto|remote|desde\s*casa|work\s*from\s*home|wfh|teletrabajo|anywhere)\b"
    )

    onsite_terms = (
        r"\b(presencial|on-site|onsite|oficina|sede|caba|buenos\s*aires|viajes)\b"
    )

    is_remote_mentioned = re.search(remote_terms, text)
    is_onsite_mentioned = re.search(onsite_terms, text)

    # --- 1. Check for Explicit Hybrid or Ambiguity ---
    if re.search(r"\b(híbrido|hybrid|mixto)\b", text) or (
        is_remote_mentioned and is_onsite_mentioned
    ):
        return "Hybrid"

    # --- 2. Check for On-site ---
    if is_onsite_mentioned:
        return "On-site"

    # --- 3. Check for Remote ---
    if is_remote_mentioned:
        return "Remote"

    # --- 4. Fallback ---
    return "Not Specified"


def its_job_days_old(published_at_iso, days_limit=DAYS_OLD_TRHESHOLD):
    """Comprueba si un trabajo es más antiguo que el límite de días."""
    try:
        published_date = datetime.fromisoformat(published_at_iso.replace("Z", "+00:00"))
        cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(days=days_limit)
        return published_date < cutoff_date
    except (ValueError, TypeError):
        return False
