import re
import asyncio
import pandas as pd
import zoneinfo
from datetime import datetime, timedelta
from collections import Counter
from config import (
    DAYS_OLD_THRESHOLD,
    TIMEZONE,
    SOURCES_BYPASS_SCORING,
    UPLOAD_TO_FIREBASE,
    LOG_REJECTED_JOBS_TO_FIREBASE,
    ACCEPTED_JOBS_RETENTION_DAYS,
    REJECTED_JOBS_RETENTION_DAYS,
)
from utils.date_utils import safe_parse_date_to_ISO
from utils.scoring_utils import filter_jobs_with_scoring
from bot.utils import send_jobs
from filters_scoring_config import MIN_SCORE, TAGS_KEYWORDS
from utils.firestore_utils import (
    get_new_jobs,
    save_jobs_to_firestore,
    save_rejected_jobs_to_firestore,
    save_trend_data_to_firestore,
    delete_old_documents,
)


async def scrape(sources, channel_id, bot):
    print("🚀 Iniciando búsqueda de trabajos...")

    # 1. FETCH: Llamamos a cada fuente en un thread separado
    tasks = [asyncio.to_thread(source_func) for source_func in sources]
    results = await asyncio.gather(*tasks)
    all_jobs = [job for result in results for job in result]

    # Conteo por fuente
    source_counts = Counter(job["source"] for job in all_jobs)
    print("📊 Trabajos encontrados por fuente:")
    for source, count in source_counts.items():
        print(f"- {source}: {count}")

    if not all_jobs:
        print("No se obtuvieron trabajos de ninguna fuente.")
        return

    df = pd.DataFrame(all_jobs)

    # 2. DEDUPLICATION LOCAL
    df["dedupe_key"] = (
        df["title"].str.lower().str.strip()
        + "|"
        + df["company"].str.lower().str.strip()
    )
    df.drop_duplicates(subset=["dedupe_key"], inplace=True)
    df.drop(columns=["dedupe_key"], inplace=True)

    # 3. NORMALIZACIÓN Y FILTRADO POR FECHA (jobs recientes según DAYS_OLD_THRESHOLD)
    df["published_at"] = df["published_at"].apply(safe_parse_date_to_ISO)
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")

    # Filtrado por días (usando tu threshold global)
    cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).date() - timedelta(
        days=DAYS_OLD_THRESHOLD
    )
    df = df[df["published_at"].dt.date >= cutoff_date]
    df.dropna(subset=["published_at"], inplace=True)
    if df.empty:
        print("No hay trabajos recientes o únicos para procesar.")
        return

    print(f"Total de jobs únicos y recientes: {len(df)}")

    # 4. ENRICHMENT
    df["text_for_extraction"] = (
        df["title"].fillna("").astype(str)
        + " "
        + df["description"].fillna("").astype(str)
    )
    df["tags"] = df["text_for_extraction"].apply(extract_tags)
    df["modality"] = df["text_for_extraction"].apply(extract_job_modality)
    df.drop(columns=["text_for_extraction"], inplace=True)

    # Marcamos fecha y hora del scraping
    df["date_scraped"] = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).isoformat()

    # 5. DEDUPLICATION FIREBASE
    if UPLOAD_TO_FIREBASE:
        new_jobs_list = get_new_jobs(df.to_dict("records"))
        if not new_jobs_list:
            print("No se encontraron trabajos nuevos después de la deduplicación.")
            return
        df = pd.DataFrame(new_jobs_list)

    if df.empty:
        print(
            "No se encontraron trabajos nuevos después de la deduplicación con Firebase."
        )
        return

    # 6. SCORING
    df_to_score = df[~df["source"].isin(SOURCES_BYPASS_SCORING)]
    df_to_bypass = df[df["source"].isin(SOURCES_BYPASS_SCORING)]

    df_accepted_scored, df_rejected = filter_jobs_with_scoring(
        df_to_score, min_score=MIN_SCORE, verbose=True
    )

    df_accepted = pd.concat([df_accepted_scored, df_to_bypass], ignore_index=True)

    # 7. OUTPUTS
    if not df_accepted.empty:
        print(
            f"✅ Se encontraron {len(df_accepted)} jobs nuevos y aceptados. Procesando..."
        )
        accepted_jobs_list = df_accepted.to_dict("records")

        if UPLOAD_TO_FIREBASE:
            save_jobs_to_firestore(accepted_jobs_list)

            tags_list = [
                tag
                for tags_dict in df_accepted["tags"]
                for tag_group in tags_dict.values()
                for tag in tag_group
            ]
            tags_counts = Counter(tags_list)
            month_key = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).strftime("%Y_%m")
            trend_data = {"total_jobs": len(df_accepted), "tags": dict(tags_counts)}
            save_trend_data_to_firestore(trend_data, month_key)

        await send_jobs(bot, channel_id, accepted_jobs_list)
    else:
        print("No hay trabajos nuevos para enviar después del scoring.")

    if not df_rejected.empty and LOG_REJECTED_JOBS_TO_FIREBASE and UPLOAD_TO_FIREBASE:
        rejected_jobs_list = df_rejected.to_dict("records")
        save_rejected_jobs_to_firestore(rejected_jobs_list)

    # 8. CLEANUP OLD DOCUMENTS
    if UPLOAD_TO_FIREBASE:
        delete_old_documents("jobs_previous", ACCEPTED_JOBS_RETENTION_DAYS)
        delete_old_documents("rejected_jobs", REJECTED_JOBS_RETENTION_DAYS)


def extract_tags(text_for_extraction):
    text = text_for_extraction.lower()
    found_tags = {}
    for category, keywords in TAGS_KEYWORDS.items():
        found_keywords = []
        for kw in keywords:
            pattern = r"(?<!\\w)" + re.escape(kw) + r"(?!\\w)"
            if re.search(pattern, text, re.IGNORECASE):
                found_keywords.append(kw)
        if found_keywords:
            found_tags[category] = found_keywords
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
