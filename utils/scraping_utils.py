import re
import asyncio
import pandas as pd
import zoneinfo
from datetime import datetime, timedelta
from collections import Counter
from config import (
    DAYS_OLD_THRESHOLD,
    JOBS_RETENTION_DAYS,
    UPLOAD_TO_FIREBASE,
)
from constants import TIMEZONE
from filters_scoring_config.scoring import MIN_FILTER_SCORE
from utils.date_utils import safe_parse_date_to_ISO
from utils.scoring_utils import filter_jobs_with_scoring
from bot.utils import send_jobs
from utils.firestore_utils import (
    get_new_jobs,
    save_jobs_to_firestore,
    save_monthly_trend_data,
    delete_old_documents,
)


async def scrape(sources, channel_id, bot):
    print("🚀 Iniciando búsqueda de trabajos...")

    # 1. FETCH: Llamamos a cada fuente en un thread separado
    tasks = [asyncio.to_thread(source_func, config) for source_func, config in sources]
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

    # 3. NORMALIZACIÓN DE TEXTO
    df["title_normalized"] = normalize_text_series(df["title"])
    df["description_normalized"] = normalize_text_series(df["description"])
    df["full_text_normalized"] = (
        df["title_normalized"] + " " + df["description_normalized"]
    )

    # 2. DEDUPLICATION LOCAL
    df["dedupe_key"] = (
        df["title_normalized"] + "|" + df["company"].str.lower().str.strip()
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
    df["modality"] = df["full_text_normalized"].apply(extract_job_modality)

    # Marcar fecha y hora del scraping
    df["date_scraped"] = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).isoformat()

    # 7. SCORING (todos los jobs pasan por scoring)
    df_accepted, df_rejected = filter_jobs_with_scoring(
        df, min_score=MIN_FILTER_SCORE, verbose=True
    )

    # Asignar estado antes de guardar
    if not df_accepted.empty:
        df_accepted = df_accepted.copy()
        df_accepted.loc[:, "status"] = "accepted"
    if not df_rejected.empty:
        df_rejected = df_rejected.copy()
        df_rejected.loc[:, "status"] = "rejected"

    df_all_scored_jobs = pd.concat([df_accepted, df_rejected], ignore_index=True)

    # Eliminar campos normalizados y descripción antes de guardar en Firestore
    columns_to_drop = [
        "title_normalized",
        "description_normalized",
        "full_text_normalized",
        "description",
    ]
    df_all_scored_jobs.drop(columns=columns_to_drop, errors="ignore", inplace=True)

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
            profile_counter = Counter()
            tag_counter = Counter()

            for _, row in df_accepted.iterrows():
                profile_counter.update(row["profiles"])
                tag_counter.update(row["tags"])

            month_key = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).strftime("%Y_%m")
            trend_data = {
                "total_jobs": len(df_accepted),
                "profiles": dict(profile_counter),
                "tags": dict(tag_counter),
            }
            save_monthly_trend_data(trend_data, month_key)

        await send_jobs(bot, channel_id, accepted_jobs_list)

    # 10. CLEANUP OLD DOCUMENTS
    if UPLOAD_TO_FIREBASE:
        delete_old_documents("jobs", JOBS_RETENTION_DAYS)


def extract_job_modality(text_for_extraction):
    """Extrae modalidad de trabajo de un texto ya normalizado en minúsculas"""
    # 100% presencial
    if re.search(
        r"\b(100%\s*(on-site|onsite|presencial)|exclusivamente\s*presencial)\b",
        text_for_extraction,
    ):
        return "Presencial"

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
        return "Híbrido"

    # Solo presencial
    if is_onsite_mentioned:
        return "Presencial"

    # Solo remoto
    if is_remote_mentioned:
        return "Remoto"

    return "No especificada"


def normalize_text_series(series: pd.Series):
    """
    Normaliza una columna de texto, eliminando caracteres basura (como ????)
    mientras conserva la puntuación y los símbolos IT relevantes.
    """

    if series.empty:
        return series

    cleaned_series = series.fillna("").astype(str).str.lower()

    cleaned_series = cleaned_series.str.replace(r"[^\w\s\+#\./]", " ", regex=True)

    cleaned_series = cleaned_series.str.replace(r"\s+", " ", regex=True).str.strip()

    return cleaned_series
