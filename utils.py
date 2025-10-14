import re
import math

import pandas as pd
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


def updateDataFrame(df):
    df["dedupe_key"] = (
        df["title"].str.lower().str.strip()
        + " "
        + df["company"].str.lower().str.strip()
    )
    df.drop_duplicates(subset=["dedupe_key"], inplace=True)
    df.drop(columns=["dedupe_key"], inplace=True)

    # 4️⃣ Normalizar fechas y filtrar últimos 24h
    FILTER_HOURS = 24
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FILTER_HOURS)

    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")

    df = df[df["published_at"] >= cutoff].copy()

    if df.empty:
        print("No hay trabajos recientes o únicos para procesar.")
        return

    print(f"Total de jobs únicos y recientes: {len(df)}")

    # 5️⃣ Extraer tags (keywords) de título y descripción

    df["text_for_extraction"] = (
        df["title"].astype(str) + " " + df["description"].astype(str)
    )

    # Aplica las funciones de utilidad a la columna combinada
    df["tags"] = df.apply(lambda row: extract_tags(row["text_for_extraction"]), axis=1)
    df["modality"] = df.apply(
        lambda row: extract_job_modality(row["text_for_extraction"]), axis=1
    )

    # Limpieza
    df.drop(columns=["text_for_extraction"], inplace=True)

    current_time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    df["date_scraped"] = current_time_iso

    # 6️⃣ Convertir a lista de dicts para enviar
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
