import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import zoneinfo
from google.cloud.firestore_v1.field_path import FieldPath

from config import (
    TIMEZONE,
    ACCEPTED_JOBS_RETENTION_DAYS,
    REJECTED_JOBS_RETENTION_DAYS,
)

if not firebase_admin._apps:
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        print("✅ Firebase Admin SDK inicializado.")
    except Exception as e:
        print(f"❌ Error al inicializar Firebase Admin SDK: {e}")
        print(
            "Asegúrate de que GOOGLE_APPLICATION_CREDENTIALS esté configurado correctamente."
        )

db = firestore.client()

def get_new_jobs(jobs_list):
    """
    Filtra una lista de trabajos, devolviendo solo aquellos que no existen en Firestore.
    Utiliza consultas 'in' en lotes para mayor eficiencia.
    """
    if not jobs_list:
        return []

    print("🔍 Verificando nuevos trabajos en Firestore por ID...")
    job_ids_to_check = {str(job["id"]) for job in jobs_list if job.get("id")}

    if not job_ids_to_check:
        return jobs_list

    existing_ids = set()
    
    # Convert set to list to be able to chunk it
    job_ids_list = list(job_ids_to_check)

    try:
        # Process in chunks of 10 for the 'in' operator limitation
        for i in range(0, len(job_ids_list), 10):
            chunk = job_ids_list[i:i + 10]

            # Check in 'jobs_today'
            docs_today = db.collection("jobs_today").where(FieldPath.documentId(), "in", chunk).stream()
            for doc in docs_today:
                existing_ids.add(doc.id)

            # Check in 'jobs_previous'
            docs_previous = db.collection("jobs_previous").where(FieldPath.documentId(), "in", chunk).stream()
            for doc in docs_previous:
                existing_ids.add(doc.id)

    except Exception as e:
        print(f"❌ Error al verificar trabajos en Firestore: {e}")
        # In case of error, assume all jobs are new to avoid losing data.
        return jobs_list

    new_job_ids = job_ids_to_check - existing_ids
    new_jobs = [job for job in jobs_list if str(job.get("id")) in new_job_ids]

    print(f"✨ {len(new_jobs)} trabajos nuevos encontrados.")
    return new_jobs

def save_jobs_to_firestore(jobs_list):
    if not jobs_list:
        return

    print(f"💾 Guardando {len(jobs_list)} jobs en Firestore...")
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
            print(f"⚠️ Job sin ID encontrado, no se guardará: {job.get('title', 'N/A')}")
            continue

        try:
            published_date = datetime.fromisoformat(
                job["published_at"].replace("Z", "+00:00")
            ).date()
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
            print(f"✅ {today_jobs_count} jobs de hoy guardados en 'jobs_today'.")
        if previous_jobs_count > 0:
            previous_batch.commit()
            print(
                f"✅ {previous_jobs_count} jobs anteriores guardados en 'jobs_previous'."
            )
    except Exception as e:
        print(f"❌ Error al guardar jobs en Firestore: {e}")

def save_rejected_jobs_to_firestore(jobs_list):
    if not jobs_list:
        return

    print(f"🗑️ Guardando {len(jobs_list)} jobs rechazados en Firestore...")
    batch = db.batch()
    rejected_jobs_collection = db.collection("rejected_jobs")

    for job in jobs_list:
        job_id = job.get("id")
        if job_id:
            doc_ref = rejected_jobs_collection.document(str(job_id))
            batch.set(doc_ref, job)
        else:
            print(
                f"⚠️ Job rechazado sin ID encontrado, no se guardará: {job.get('title', 'N/A')}"
            )

    try:
        batch.commit()
        print(f"✅ {len(jobs_list)} jobs rechazados guardados en Firestore.")
    except Exception as e:
        print(f"❌ Error al guardar jobs rechazados en Firestore: {e}")

def save_trend_data_to_firestore(trend_data, month_key):
    if not trend_data:
        return

    trends_collection = db.collection("trends")
    doc_ref = trends_collection.document(month_key)

    try:
        doc_ref.set(trend_data, merge=True)
        print(f"📈 Tendencias para {month_key} actualizadas en Firestore.")
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

        docs_to_delete = (
            db.collection(collection_name)
            .where("date_scraped", "<", cutoff_iso)
            .limit(500)
            .stream()
        )

        batch = db.batch()
        deleted_count = 0
        for doc in docs_to_delete:
            batch.delete(doc.reference)
            deleted_count += 1

        if deleted_count > 0:
            batch.commit()
            print(
                f"✅ Se eliminaron {deleted_count} documentos antiguos de '{collection_name}'."
            )
        else:
            print(f"No se encontraron documentos antiguos para eliminar en '{collection_name}'.")

    except Exception as e:
        print(f"❌ Error al limpiar documentos antiguos de '{collection_name}': {e}")