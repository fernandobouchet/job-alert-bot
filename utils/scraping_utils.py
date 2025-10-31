import re
import asyncio
import pandas as pd
import zoneinfo
from datetime import datetime, timedelta
from collections import Counter
from config import (
    DAYS_OLD_THRESHOLD,
    TIMEZONE,
    UPLOAD_TO_FIREBASE,
    ACCEPTED_JOBS_RETENTION_DAYS,
)
from utils.date_utils import safe_parse_date_to_ISO
from utils.scoring_utils import filter_jobs_with_scoring
from bot.utils import send_jobs
from filters_scoring_config import MIN_SCORE, TAGS_KEYWORDS
from utils.firestore_utils import (
    get_new_jobs,
    save_jobs_to_firestore,
    save_daily_trend_data,
    delete_old_documents,
    delete_old_trends,
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

    # 3. NORMALIZACIÓN DE FECHAS
    df["published_at"] = df["published_at"].apply(safe_parse_date_to_ISO)
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df.dropna(subset=["published_at"], inplace=True)

    # 4. FILTRADO POR FECHA (lo antes posible)
    cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).date() - timedelta(
        days=DAYS_OLD_THRESHOLD
    )
    df = df[df["published_at"].dt.date >= cutoff_date]

    if df.empty:
        print("No hay trabajos recientes después del filtrado por fecha.")
        return

    print(f"Total de jobs únicos y recientes: {len(df)}")

    # 5. DEDUPLICATION FIREBASE (antes del enrichment)
    if UPLOAD_TO_FIREBASE:
        new_jobs_list = get_new_jobs(df.to_dict("records"))
        if not new_jobs_list:
            print(
                "No se encontraron trabajos nuevos después de la deduplicación con Firebase."
            )
            return
        df = pd.DataFrame(new_jobs_list)
        print(f"✨ {len(df)} trabajos nuevos después de deduplicación con Firebase.")

    if df.empty:
        print("No se encontraron trabajos nuevos.")
        return

    # 6. ENRICHMENT (solo para jobs nuevos)
    # Convertir a minúsculas una sola vez para optimizar
    df["text_for_extraction"] = (
        df["title"].fillna("").astype(str)
        + " "
        + df["description"].fillna("").astype(str)
    ).str.lower()

    df["tags"] = df["text_for_extraction"].apply(extract_tags)
    df["modality"] = df["text_for_extraction"].apply(extract_job_modality)
    df.drop(columns=["text_for_extraction"], inplace=True)

    # Marcar fecha y hora del scraping
    df["date_scraped"] = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).isoformat()

    # 7. SCORING (todos los jobs pasan por scoring)
    df_accepted, df_rejected = filter_jobs_with_scoring(
        df, min_score=MIN_SCORE, verbose=True
    )
    df_all_scored_jobs = pd.concat([df_accepted, df_rejected], ignore_index=True)

    # 8. GUARDAR TODOS LOS JOBS NUEVOS (aceptados y rechazados)
    all_new_jobs_list = df_all_scored_jobs.to_dict("records")

    if UPLOAD_TO_FIREBASE:
        print(
            f"💾 Guardando {len(all_new_jobs_list)} jobs nuevos (aceptados + rechazados)..."
        )
        await save_jobs_to_firestore(all_new_jobs_list)

    # 9. ENVIAR SOLO LOS ACEPTADOS
    if df_accepted.empty:
        print("No hay trabajos aceptados para enviar al bot.")
    else:
        print(
            f"✅ Se encontraron {len(df_accepted)} jobs aceptados. Enviando al bot..."
        )
        accepted_jobs_list = df_accepted.to_dict("records")

        if UPLOAD_TO_FIREBASE:
            # Calcular tendencias solo con jobs aceptados
            tags_list = [
                tag
                for tags_dict in df_accepted["tags"]
                if isinstance(tags_dict, dict)
                for tag_group in tags_dict.values()
                for tag in tag_group
            ]
            tags_counts = Counter(tags_list)
            day_key = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).strftime("%Y_%m_%d")
            trend_data = {"total_jobs": len(df_accepted), "tags": dict(tags_counts)}
            save_daily_trend_data(trend_data, day_key)

        await send_jobs(bot, channel_id, accepted_jobs_list)

    # 10. CLEANUP OLD DOCUMENTS
    if UPLOAD_TO_FIREBASE:
        delete_old_documents("jobs", ACCEPTED_JOBS_RETENTION_DAYS)
        delete_old_trends(ACCEPTED_JOBS_RETENTION_DAYS)


def extract_tags(text_for_extraction):
    """Extrae tags de un texto ya normalizado en minúsculas"""
    found_tags = {}
    for category, keywords in TAGS_KEYWORDS.items():
        found_keywords = []
        for kw in keywords:
            pattern = r"(?<!\w)" + re.escape(kw) + r"(?!\w)"
            if re.search(pattern, text_for_extraction, re.IGNORECASE):
                found_keywords.append(kw)
        if found_keywords:
            found_tags[category] = found_keywords
    return found_tags


def extract_job_modality(text_for_extraction):
    """Extrae modalidad de trabajo de un texto ya normalizado en minúsculas"""
    # 100% presencial
    if re.search(
        r"\b(100%\s*(on-site|onsite|presencial)|exclusivamente\s*presencial)\b",
        text_for_extraction,
    ):
        return "On-site"

    # Términos remotos y presenciales
    remote_terms = (
        r"\b(remoto|remote|desde\s*casa|work\s*from\s*home|wfh|teletrabajo|anywhere)\b"
    )
    onsite_terms = (
        r"\b(presencial|on-site|onsite|oficina|sede|caba|buenos\s*aires|viajes)\b"
    )

    is_remote_mentioned = re.search(remote_terms, text_for_extraction)
    is_onsite_mentioned = re.search(onsite_terms, text_for_extraction)

    # Híbrido: explícitamente mencionado o ambos términos presentes
    if re.search(r"\b(híbrido|hybrid|mixto)\b", text_for_extraction) or (
        is_remote_mentioned and is_onsite_mentioned
    ):
        return "Hybrid"

    # Solo presencial
    if is_onsite_mentioned:
        return "On-site"

    # Solo remoto
    if is_remote_mentioned:
        return "Remote"

    return "Not Specified"
