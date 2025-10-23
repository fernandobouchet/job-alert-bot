import firebase_admin
from firebase_admin import credentials, firestore

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


def save_jobs_to_firestore(jobs_list):
    if not jobs_list:
        return

    print(f"💾 Guardando {len(jobs_list)} jobs en Firestore...")
    batch = db.batch()
    jobs_collection = db.collection("jobs")

    for job in jobs_list:
        job_id = job.get("id")
        if job_id:
            # Usamos el ID del job como ID del documento en Firestore
            doc_ref = jobs_collection.document(str(job_id))
            batch.set(doc_ref, job)
        else:
            print(f"⚠️ Job sin ID encontrado, no se guardará: {job.get('title', 'N/A')}")

    try:
        batch.commit()
        print(f"✅ {len(jobs_list)} jobs guardados/actualizados en Firestore.")
    except Exception as e:
        print(f"❌ Error al guardar jobs en Firestore: {e}")


def get_all_job_ids_from_firestore():
    """
    Obtiene todos los IDs de jobs existentes en Firestore.
    Útil para la deduplicación.
    """
    try:
        job_ids = set()
        docs = db.collection("jobs").select(["id"]).stream()
        for doc in docs:
            job_ids.add(doc.id)
        return job_ids
    except Exception as e:
        print(f"❌ Error al obtener IDs de jobs de Firestore: {e}")
        return set()


def save_rejected_job_to_firestore(job_data):
    if not job_data:
        return

    rejected_jobs_collection = db.collection("rejected_jobs")
    job_id = job_data.get("id")
    if job_id:
        doc_ref = rejected_jobs_collection.document(str(job_id))
        try:
            doc_ref.set(job_data)
            print(f"🗑️ Job rechazado con ID {job_id} guardado en Firestore.")
        except Exception as e:
            print(f"❌ Error al guardar job rechazado en Firestore: {e}")
    else:
        print(f"⚠️ Job rechazado sin ID, no se guardará: {job_data.get('title', 'N/A')}")


def save_trend_data_to_firestore(trend_data, month_key):
    if not trend_data:
        return

    trends_collection = db.collection("trends")
    doc_ref = trends_collection.document(month_key)  # month_key como 'YYYY_MM'

    try:
        # Obtener el documento actual si existe
        current_trend = doc_ref.get().to_dict()
        if current_trend:
            # Actualizar el documento existente
            current_trend["total_jobs"] += trend_data["total_jobs"]
            for tag, count in trend_data["tags"].items():
                current_trend["tags"][tag] = current_trend["tags"].get(tag, 0) + count
            doc_ref.set(current_trend)
            print(f"📈 Tendencias para {month_key} actualizadas en Firestore.")
        else:
            # Crear un nuevo documento
            doc_ref.set(trend_data)
            print(f"📈 Tendencias para {month_key} creadas en Firestore.")
    except Exception as e:
        print(f"❌ Error al guardar tendencias en Firestore: {e}")
