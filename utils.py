import math
import re
import asyncio
import pandas as pd
import zoneinfo
from datetime import datetime, timedelta, date
from collections import Counter
from config import (
    HOURS_OLD_THRESHOLD,
    TIMEZONE,
    SOURCES_BYPASS_SCORING,
    UPLOAD_TO_FIREBASE,
    LOG_JSON_TO_GIT,
)
from filters_scoring import filter_jobs_with_scoring
from json_handler import save_json
from bot.utils import send_jobs
from filters_scoring_config import MIN_SCORE, TAGS_KEYWORDS
from firestore_handler import (
    get_all_job_ids_from_firestore,
    save_jobs_to_firestore,
    save_trend_data_to_firestore,
)


async def scrape(sources, channel_id, bot):
    print("🚀 Iniciando búsqueda de trabajos...")
    # 1. FETCH
    tasks = [asyncio.to_thread(source_func) for source_func in sources]
    results = await asyncio.gather(*tasks)
    all_jobs = [job for result in results for job in result]

    if not all_jobs:
        print("No se obtuvieron trabajos de ninguna fuente.")
        return

    df = pd.DataFrame(all_jobs)

    # 2. CLEANUP & ENRICHMENT (formerly updateDataFrame)
    df["dedupe_key"] = (
        df["title"].str.lower().str.strip()
        + "|"
        + df["company"].str.lower().str.strip()
    )
    df.drop_duplicates(subset=["dedupe_key"], inplace=True)
    df.drop(columns=["dedupe_key"], inplace=True)

    cutoff = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(
        hours=HOURS_OLD_THRESHOLD
    )
    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
    df.dropna(subset=["published_at"], inplace=True)
    df = df[df["published_at"] >= cutoff].copy()

    if df.empty:
        print("No hay trabajos recientes o únicos para procesar.")
        return

    print(f"Total de jobs únicos y recientes: {len(df)}")

    df["text_for_extraction"] = (
        df["title"].fillna("").astype(str)
        + " "
        + df["description"].fillna("").astype(str)
    )
    df["tags"] = df["text_for_extraction"].apply(extract_tags)
    df["modality"] = df["text_for_extraction"].apply(extract_job_modality)
    df.drop(columns=["text_for_extraction"], inplace=True)

    current_time_iso = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).strftime(
        "%Y-%m-%dT%H:%M:%S+00:00"
    )
    df["date_scraped"] = current_time_iso
    df["published_at"] = df["published_at"].dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # 3. DEDUPLICATION (against Firebase)
    if UPLOAD_TO_FIREBASE:
        print("🔍 Consultando IDs existentes en Firebase para deduplicación...")
        existing_ids = get_all_job_ids_from_firestore()
        df = df[~df["id"].isin(existing_ids)]

    if df.empty:
        print(
            "No se encontraron trabajos nuevos después de la deduplicación con Firebase."
        )
        return

    # 4. SCORING
    df_to_score = df[~df["source"].isin(SOURCES_BYPASS_SCORING)]
    df_to_bypass = df[df["source"].isin(SOURCES_BYPASS_SCORING)]

    df_accepted_scored, df_rejected = filter_jobs_with_scoring(
        df_to_score, min_score=MIN_SCORE, verbose=True
    )

    df_accepted = pd.concat([df_accepted_scored, df_to_bypass], ignore_index=True)

    # 5. HANDLE OUTPUTS
    if not df_accepted.empty:
        print(
            f"✅ Se encontraron {len(df_accepted)} jobs nuevos y aceptados. Procesando..."
        )
        accepted_jobs_list = df_accepted.to_dict("records")

        if UPLOAD_TO_FIREBASE:
            # Upload accepted jobs
            save_jobs_to_firestore(accepted_jobs_list)

            # Calculate and upload trend data
            tags_list = [tag for tags in df_accepted["tags"] for tag in tags]
            tags_counts = Counter(tags_list)
            month_key = datetime.now().strftime("%Y_%m")
            trend_data = {
                "total_jobs": len(df_accepted),
                "tags": dict(tags_counts),
            }
            save_trend_data_to_firestore(trend_data, month_key)

        if LOG_JSON_TO_GIT:
            print("💾 Guardando jobs aceptados en data/accepted_jobs.json...")
            save_json(accepted_jobs_list, "data/accepted_jobs.json")

        # Send to Telegram
        await send_jobs(bot, channel_id, accepted_jobs_list)

    else:
        print("No hay trabajos nuevos para enviar después del scoring.")

    if not df_rejected.empty and LOG_JSON_TO_GIT:
        print(
            f"💾 Guardando {len(df_rejected)} jobs rechazados en data/rejected_jobs.json..."
        )
        save_json(df_rejected.to_dict("records"), "data/rejected_jobs.json")


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
    if re.search(r"\b(híbrido|hybrid|mixto)\b", text) or (
        is_remote_mentioned and is_onsite_mentioned
    ):
        return "Hybrid"
    if is_onsite_mentioned:
        return "On-site"
    if is_remote_mentioned:
        return "Remote"
    return "Not Specified"


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


def its_job_days_old(published_at_iso, days_limit=1):
    """Comprueba si un trabajo es más antiguo que el límite de días."""
    try:
        published_date = datetime.fromisoformat(published_at_iso.replace("Z", "+00:00"))
        cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(
            days=days_limit
        )
        return published_date < cutoff_date
    except (ValueError, TypeError):
        return False
