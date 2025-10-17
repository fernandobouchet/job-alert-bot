import re
import math
import asyncio
import pandas as pd
from config import (
    EXCLUDED_AREA_TERMS_TITLE,
    EXCLUDED_EXPERIENCE_PHRASES,
    EXCLUDED_SENIORITYS,
    LOG_UNFILTERED_JOBS,
    REQUIRED_IT_SIGNALS,
    TAGS_KEYWORDS,
)
from datetime import datetime, timezone, timedelta, date
from json_handler import update_job_data, save_json
from bot.utils import send_jobs


async def scrape(sources, chat_id, bot=None):
    print("🚀 Iniciando búsqueda de trabajos...")
    tasks = [asyncio.to_thread(source_func) for source_func in sources]
    results = await asyncio.gather(*tasks)

    all_jobs = [job for result in results for job in result]

    if not all_jobs:
        print("No se obtuvieron trabajos de ninguna fuente.")
        return

    df = pd.DataFrame(all_jobs)

    print(df.head())
    df_filtered = filter_jobs(df)

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
        if bot:
            await send_jobs(bot, chat_id, new_jobs)
    else:
        print("No hay jobs nuevos para enviar.")


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


def updateDataFrame(df):
    FILTER_HOURS = 14

    df["dedupe_key"] = (
        df["title"].str.lower().str.strip()
        + "|"
        + df["company"].str.lower().str.strip()
    )
    df.drop_duplicates(subset=["dedupe_key"], inplace=True)
    df.drop(columns=["dedupe_key"], inplace=True)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=FILTER_HOURS)

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

    current_time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    df["date_scraped"] = current_time_iso

    df["published_at"] = df["published_at"].dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    recent_jobs = df.to_dict(orient="records")

    return recent_jobs


def extract_tags(text_for_extraction):

    text = text_for_extraction.lower()

    found_tags = []
    for kw in TAGS_KEYWORDS:
        # Usa \b (límite de palabra) y re.escape para buscar la palabra completa
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text):
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


def filter_jobs(df):
    """Filter jobs by seniority, area, positive IT signals and experience."""
    if df.empty:
        return df

    original_df = df.copy()

    # 1. Seniority
    pattern = "|".join([re.escape(s.lower()) for s in EXCLUDED_SENIORITYS])
    df = df[~df["title"].str.lower().str.contains(pattern, regex=True, na=False)].copy()

    # 2. Area (título)
    escaped_terms = [re.escape(term.lower()) for term in EXCLUDED_AREA_TERMS_TITLE]
    pattern = r"\b(?:" + "|".join(escaped_terms) + r")\b"
    df = df[~df["title"].str.lower().str.contains(pattern, regex=True, na=False)].copy()

    # 3. ⭐ IT SIGNALS
    df["_temp_title"] = df["title"].fillna("").str.lower()
    escaped_signals = [re.escape(s.lower()) for s in REQUIRED_IT_SIGNALS]
    pattern = r"\b(?:" + "|".join(escaped_signals) + r")\b"
    df = df[df["_temp_title"].str.contains(pattern, regex=True, na=False)].copy()
    df = df.drop(columns=["_temp_title"])

    # 4. Experience
    pattern = (
        r"\b("
        + "|".join([re.escape(e.lower()) for e in EXCLUDED_EXPERIENCE_PHRASES])
        + r")\b"
    )
    df = df[
        ~df["description"]
        .fillna("")
        .str.lower()
        .str.contains(pattern, regex=True, na=False)
    ].copy()

    if LOG_UNFILTERED_JOBS:
        unfiltered_jobs = original_df[~original_df.index.isin(df.index)]
        if not unfiltered_jobs.empty:
            save_json(
                unfiltered_jobs.to_dict(orient="records"), "data/unfiltered_jobs.json"
            )

    return df
