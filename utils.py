import asyncio
import pandas as pd
import zoneinfo
from datetime import datetime, timedelta
from collections import Counter
import logging
from config import (
    HOURS_OLD_THRESHOLD,
    TIMEZONE,
    SOURCES_BYPASS_SCORING,
    UPLOAD_TO_FIREBASE,
    LOG_REJECTED_JOBS_TO_FIREBASE,
    ACCEPTED_JOBS_RETENTION_DAYS,
    REJECTED_JOBS_RETENTION_DAYS,
)
from filters_scoring import filter_jobs_with_scoring
from bot.utils import send_jobs
from config import MIN_SCORE
from firestore_handler import (
    get_new_jobs,
    save_jobs_to_firestore,
    save_rejected_jobs_to_firestore,
    save_trend_data_to_firestore,
    delete_old_documents,
)
from enrichment import extract_tags, extract_job_modality

logger = logging.getLogger(__name__)


async def scrape(sources, channel_id, bot):
    logger.info("🚀 Iniciando búsqueda de trabajos...")

    # 1. FETCH: Llamamos a cada fuente en un thread separado
    tasks = [asyncio.to_thread(source_func) for source_func in sources]
    results = await asyncio.gather(*tasks)
    all_jobs = [job for result in results for job in result]

    # Conteo por fuente
    source_counts = Counter(job["source"] for job in all_jobs)
    logger.info("📊 Trabajos encontrados por fuente:")
    for source, count in source_counts.items():
        logger.info(f"- {source}: {count}")

    if not all_jobs:
        logger.warning("No se obtuvieron trabajos de ninguna fuente.")
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

    # 3. FILTRADO POR FECHA (jobs recientes según HOURS_OLD_THRESHOLD)
    cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(
        hours=HOURS_OLD_THRESHOLD
    )
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df.dropna(subset=["published_at"], inplace=True)
    df = df[df["published_at"] >= cutoff_date]

    if df.empty:
        logger.info("No hay trabajos recientes o únicos para procesar.")
        return

    logger.info(f"Total de jobs únicos y recientes: {len(df)}")

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
            logger.info("No se encontraron trabajos nuevos después de la deduplicación.")
            return
        df = pd.DataFrame(new_jobs_list)

    if df.empty:
        logger.warning(
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
        logger.info(
            f"✅ Se encontraron {len(df_accepted)} jobs nuevos y aceptados. Procesando..."
        )
        accepted_jobs_list = df_accepted.to_dict("records")

        if UPLOAD_TO_FIREBASE:
            save_jobs_to_firestore(accepted_jobs_list)

            tags_list = [tag for tags in df_accepted["tags"] for tag in tags]
            tags_counts = Counter(tags_list)
            month_key = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).strftime("%Y_%m")
            trend_data = {"total_jobs": len(df_accepted), "tags": dict(tags_counts)}
            save_trend_data_to_firestore(trend_data, month_key)

        await send_jobs(bot, channel_id, accepted_jobs_list)
    else:
        logger.info("No hay trabajos nuevos para enviar después del scoring.")

    if not df_rejected.empty and LOG_REJECTED_JOBS_TO_FIREBASE and UPLOAD_TO_FIREBASE:
        rejected_jobs_list = df_rejected.to_dict("records")
        save_rejected_jobs_to_firestore(rejected_jobs_list)
        logger.info(f"Se guardaron {len(df_rejected)} trabajos rechazados.")

    # 8. CLEANUP OLD DOCUMENTS
    if UPLOAD_TO_FIREBASE:
        delete_old_documents("jobs_previous", ACCEPTED_JOBS_RETENTION_DAYS)
        delete_old_documents("rejected_jobs", REJECTED_JOBS_RETENTION_DAYS)
