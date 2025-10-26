import firebase_admin
from firebase_admin import credentials, firestore
import logging
from datetime import datetime, timedelta, date
import zoneinfo
from google.cloud.firestore_v1.field_path import FieldPath
from google.cloud.firestore_v1.base_query import FieldFilter

from config import TIMEZONE, UPLOAD_TO_FIREBASE

logger = logging.getLogger(__name__)

db = None
if UPLOAD_TO_FIREBASE:
    if not firebase_admin._apps:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK inicializado.")
            db = firestore.client()
        except Exception as e:
            logger.error(f"❌ Error al inicializar Firebase Admin SDK: {e}")
            logger.error(
                "Asegúrate de que GOOGLE_APPLICATION_CREDENTIALS esté configurado correctamente."
            )

def get_new_jobs(jobs_list):
    if not jobs_list:
        return []

    logger.info("🔍 Verificando nuevos trabajos en Firestore por ID...")
    job_ids_to_check = {str(job["id"]) for job in jobs_list if job.get("id")}
    if not job_ids_to_check:
        return jobs_list

    existing_ids = set()
    job_ids_list = list(job_ids_to_check)

    try:
        for i in range(0, len(job_ids_list), 10):
            chunk = job_ids_list[i : i + 10]
            today_refs = [db.collection("jobs_today").document(doc_id) for doc_id in chunk]
            previous_refs = [db.collection("jobs_previous").document(doc_id) for doc_id in chunk]

            docs_today = db.collection("jobs_today").where(filter=FieldFilter(FieldPath.document_id(), "in", today_refs)).stream()
            existing_ids.update(doc.id for doc in docs_today)

            docs_previous = db.collection("jobs_previous").where(filter=FieldFilter(FieldPath.document_id(), "in", previous_refs)).stream()
            existing_ids.update(doc.id for doc in docs_previous)

    except Exception as e:
        logger.error(f"❌ Error al verificar trabajos en Firestore: {e}")
        return jobs_list

    new_job_ids = job_ids_to_check - existing_ids
    new_jobs = [job for job in jobs_list if str(job.get("id")) in new_job_ids]
    logger.info(f"✨ {len(new_jobs)} trabajos nuevos encontrados.")
    return new_jobs

def save_jobs_to_firestore(jobs_list):
    if not jobs_list:
        return
    logger.info(f"💾 Guardando {len(jobs_list)} jobs en Firestore...")

    today_batch = db.batch()
    previous_batch = db.batch()
    today_collection = db.collection("jobs_today")
    previous_collection = db.collection("jobs_previous")
    today_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).date()
    today_jobs_count = 0
    previous_jobs_count = 0

    for job in jobs_list:
        job_id = job.get("id")
        if not job_id:
            logger.warning(f"⚠️ Job sin ID encontrado, no se guardará: {job.get('title', 'N/A')}")
            continue

        try:
            published_date = datetime.fromisoformat(job["published_at"].replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            published_date = today_date

        doc_ref_today = today_collection.document(str(job_id))
        doc_ref_previous = previous_collection.document(str(job_id))

        if published_date == today_date:
            today_batch.set(doc_ref_today, job)
            today_jobs_count += 1
        else:
            previous_batch.set(doc_ref_previous, job)
            previous_jobs_count += 1

    try:
        if today_jobs_count > 0:
            today_batch.commit()
            logger.info(f"✅ {today_jobs_count} jobs de hoy guardados en 'jobs_today'.")
        if previous_jobs_count > 0:
            previous_batch.commit()
            logger.info(f"✅ {previous_jobs_count} jobs anteriores guardados en 'jobs_previous'.")
    except Exception as e:
        logger.error(f"❌ Error al guardar jobs en Firestore: {e}")

def save_rejected_jobs_to_firestore(jobs_list):
    if not jobs_list:
        return
    logger.info(f"🗑️ Guardando {len(jobs_list)} jobs rechazados en Firestore...")
    batch = db.batch()
    rejected_jobs_collection = db.collection("rejected_jobs")

    for job in jobs_list:
        job_id = job.get("id")
        if job_id:
            doc_ref = rejected_jobs_collection.document(str(job_id))
            batch.set(doc_ref, job)
        else:
            logger.warning(f"⚠️ Job rechazado sin ID encontrado, no se guardará: {job.get('title', 'N/A')}")

    try:
        batch.commit()
        logger.info(f"✅ {len(jobs_list)} jobs rechazados guardados en Firestore.")
    except Exception as e:
        logger.error(f"❌ Error al guardar jobs rechazados en Firestore: {e}")

def save_trend_data_to_firestore(trend_data, month_key):
    if not trend_data:
        return
    trends_collection = db.collection("trends")
    doc_ref = trends_collection.document(month_key)
    try:
        doc_ref.set(trend_data, merge=True)
        logger.info(f"📈 Tendencias para {month_key} actualizadas en Firestore.")
    except Exception as e:
        logger.error(f"❌ Error al guardar tendencias en Firestore: {e}")

def delete_old_documents(collection_name, days_to_keep):
    if not days_to_keep or days_to_keep <= 0:
        logger.warning(f"⚠️ La retención de '{collection_name}' está desactivada (días <= 0).")
        return
    logger.info(f"🧹 Limpiando docs antiguos de '{collection_name}' (retención: {days_to_keep} días)...")

    try:
        cutoff_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(days=days_to_keep)
        cutoff_iso = cutoff_date.isoformat()
        docs_to_delete = db.collection(collection_name).where(filter=FieldFilter("date_scraped", "<", cutoff_iso)).limit(500).stream()

        batch = db.batch()
        deleted_count = 0
        for doc in docs_to_delete:
            batch.delete(doc.reference)
            deleted_count += 1

        if deleted_count > 0:
            batch.commit()
            logger.info(f"✅ Se eliminaron {deleted_count} docs antiguos de '{collection_name}'.")
        else:
            logger.info(f"No se encontraron docs antiguos para eliminar en '{collection_name}'.")
    except Exception as e:
        logger.error(f"❌ Error al limpiar docs antiguos de '{collection_name}': {e}")
