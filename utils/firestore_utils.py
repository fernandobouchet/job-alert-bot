import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import zoneinfo
from google.cloud.firestore_v1.field_path import FieldPath
from google.cloud.firestore_v1.base_query import FieldFilter
import pandas as pd
import asyncio

from config import TIMEZONE
from utils.revalidation_utils import revalidate_path

# Inicialización de Firebase Admin
if not firebase_admin._apps:
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK inicializado.")
    except Exception as e:
        print(f"❌ Error al inicializar Firebase Admin SDK: {e}")


db = firestore.client()


def get_new_jobs(jobs_list):
    """
    Filtra una lista de trabajos y devuelve solo aquellos que no existen en Firestore.
    """
    if not jobs_list:
        return []

    print("🔍 Verificando nuevos trabajos en Firestore por ID...")

    job_ids_to_check = {str(job["id"]) for job in jobs_list if job.get("id")}
    if not job_ids_to_check:
        return jobs_list

    existing_ids = set()
    job_ids_list = list(job_ids_to_check)

    try:
        # Verificar en lotes de 30
        for i in range(0, len(job_ids_list), 30):
            chunk = job_ids_list[i : i + 30]

            docs = db.get_all(
                [db.collection("jobs").document(doc_id) for doc_id in chunk]
            )

            existing_ids.update(doc.id for doc in docs if doc.exists)

    except Exception as e:
        print(f"❌ Error al verificar trabajos en Firestore: {e}")
        return jobs_list

    new_job_ids = job_ids_to_check - existing_ids
    new_jobs = [job for job in jobs_list if str(job.get("id")) in new_job_ids]

    print(f"✨ {len(new_jobs)} trabajos nuevos encontrados.")
    return new_jobs


async def save_jobs_to_firestore(jobs_list):
    if not jobs_list:
        return

    print(f"💾 Guardando {len(jobs_list)} jobs en Firestore...")

    jobs_batch = db.batch()
    jobs_collection = db.collection("jobs")
    today_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).date()

    today_jobs_count = 0
    previous_jobs_count = 0

    for job in jobs_list:
        job_id = job.get("id")
        if not job_id:
            print(f"⚠️ Job sin ID encontrado: {job.get('title', 'N/A')}")
            continue

        try:
            published_date = pd.to_datetime(job["published_at"]).date()
        except (ValueError, TypeError, KeyError):
            published_date = today_date

        doc_ref_jobs = jobs_collection.document(str(job_id))
        jobs_batch.set(doc_ref_jobs, job)

        if published_date == today_date:
            today_jobs_count += 1
        else:
            previous_jobs_count += 1

    try:
        jobs_batch.commit()

        revalidation_tasks = []

        if today_jobs_count > 0:
            print(f"✅ {today_jobs_count} jobs de hoy guardados.")
            revalidation_tasks.append(revalidate_path("/"))

        if previous_jobs_count > 0:
            print(f"✅ {previous_jobs_count} jobs anteriores guardados.")
            revalidation_tasks.append(revalidate_path("/archive"))

        if revalidation_tasks:
            await asyncio.gather(*revalidation_tasks)

    except Exception as e:
        print(f"❌ Error al guardar jobs en Firestore: {e}")


def save_daily_trend_data(trend_data, day_key):
    if not trend_data:
        return

    trends_collection = db.collection("trends")
    doc_ref = trends_collection.document(day_key)

    # Se añade un timestamp para facilitar el borrado futuro
    trend_data["date_saved"] = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).isoformat()

    try:
        doc_ref.set(trend_data)
        print(f"📈 Tendencias para {day_key} guardadas en Firestore.")
    except Exception as e:
        print(f"❌ Error al guardar tendencias en Firestore: {e}")


def delete_old_documents(collection_name, days_to_keep):
    """
    Elimina documentos de una colección que son más antiguos que un número de días.
    """
    if not days_to_keep or days_to_keep <= 0:
        print(f"⚠️ La retención de '{collection_name}' está desactivada (días <= 0).")
        return

    print(
        f"🧹 Limpiando documentos antiguos de '{collection_name}' (retención: {days_to_keep} días)..."
    )

    try:
        cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(
            days=days_to_keep
        )
        cutoff_iso = cutoff_date.isoformat()

        deleted_total = 0

        # Loop hasta que no haya más documentos que borrar
        while True:
            docs_to_delete = list(
                db.collection(collection_name)
                .where(filter=FieldFilter("date_scraped", "<", cutoff_iso))
                .limit(500)
                .stream()
            )

            if not docs_to_delete:
                break

            batch = db.batch()
            for doc in docs_to_delete:
                batch.delete(doc.reference)

            batch.commit()
            deleted_total += len(docs_to_delete)

            print(f"  Eliminados {len(docs_to_delete)} documentos...")

        if deleted_total > 0:
            print(
                f"✅ Se eliminaron {deleted_total} documentos antiguos de '{collection_name}'."
            )
        else:
            print(
                f"✅ No se encontraron documentos antiguos para eliminar en '{collection_name}'."
            )

    except Exception as e:
        print(f"❌ Error al limpiar documentos antiguos de '{collection_name}': {e}")


def delete_old_trends(days_to_keep):
    """
    Elimina documentos de la colección 'trends' que son más antiguos que un número de días.
    """
    collection_name = "trends"
    if not days_to_keep or days_to_keep <= 0:
        print(f"⚠️ La retención de '{collection_name}' está desactivada (días <= 0).")
        return

    print(
        f"🧹 Limpiando tendencias antiguas de '{collection_name}' (retención: {days_to_keep} días)..."
    )

    try:
        cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(
            days=days_to_keep
        )
        cutoff_iso = cutoff_date.isoformat()

        deleted_total = 0

        while True:
            docs_to_delete = list(
                db.collection(collection_name)
                .where(filter=FieldFilter("date_saved", "<", cutoff_iso))
                .limit(500)
                .stream()
            )

            if not docs_to_delete:
                break

            batch = db.batch()
            for doc in docs_to_delete:
                batch.delete(doc.reference)

            batch.commit()
            deleted_total += len(docs_to_delete)

            print(f"  Eliminadas {len(docs_to_delete)} tendencias...")

        if deleted_total > 0:
            print(
                f"✅ Se eliminaron {deleted_total} tendencias antiguas de '{collection_name}'."
            )
        else:
            print(f"✅ No se encontraron tendencias antiguas para eliminar.")

    except Exception as e:
        print(f"❌ Error al limpiar tendencias antiguas de '{collection_name}': {e}")
