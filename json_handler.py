import json
import os

try:
    from config import TIMEZONE
except ImportError:
    TIMEZONE = "UTC"
import zoneinfo
from datetime import datetime, timedelta
from collections import defaultdict


DATA_DIR = "data"
LATEST_JOBS_FILE = os.path.join(DATA_DIR, "latest_jobs.json")
TRENDS_HISTORY_FILE = os.path.join(DATA_DIR, "trends_history.json")


def load_json(filepath):
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(
            f"Advertencia: No se pudo cargar {filepath}. Creando lista vacía. Error: {e}"
        )
        return []


def save_json(data, filepath):
    dir_name = os.path.dirname(filepath)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    # Si es el archivo de rechazados, manejar la actualización
    if "rejected_jobs.json" in filepath:
        existing_jobs = load_json(filepath)
        existing_ids = {job["id"] for job in existing_jobs}

        new_jobs = [job for job in data if job["id"] not in existing_ids]

        if not new_jobs:
            # print("No new rejected jobs to add.")
            return

        updated_jobs = existing_jobs + new_jobs

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(updated_jobs, f, indent=2, ensure_ascii=False)
        # print(f"Added {len(new_jobs)} new jobs to {filepath}. Total: {len(updated_jobs)}.")

    else:
        # Comportamiento original para otros archivos
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def get_monthly_history_path(date_str):
    # Formato AAAA_MM
    month_str = datetime.strptime(date_str[:7], "%Y-%m").strftime("%Y_%m")
    return os.path.join(DATA_DIR, f"jobs_{month_str}.json")


def aggregate_trends(jobs_list):

    trends = defaultdict(lambda: {"total_jobs": 0, "tags": defaultdict(int)})

    for job in jobs_list:
        # Usamos solo la parte de la fecha (AAAA-MM) para la clave de agregación
        date_key = job["date_scraped"][:7]

        trends[date_key]["total_jobs"] += 1

        for tag in job.get("tags", []):
            trends[date_key]["tags"][tag] += 1

    # Convierte los defaultdicts a dicts normales para la serialización JSON
    final_trends = []
    for date, data in trends.items():
        final_trends.append(
            {
                "date": date,
                "total_jobs": data["total_jobs"],
                "tags": dict(data["tags"]),
            }
        )

    return final_trends


def update_job_data(recent_jobs):
    if not recent_jobs:
        return []

    print("⚙️ Applying filters and enriching data...")

    # La fecha de escaneo (AAAA-MM)
    current_month_str = recent_jobs[0].get(
        "date_scraped", datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).isoformat()
    )[:7]

    # a. Determinar el path del archivo mensual y cargarlo
    monthly_path = get_monthly_history_path(current_month_str)
    monthly_history = load_json(monthly_path)

    # b. Identificar trabajos nuevos y crear la lista de envío
    # Usamos el 'id' para la desduplicación en el historial
    historical_ids = {j["id"] for j in monthly_history}
    jobs_to_send = []

    # --- PROCESAMIENTO Y FILTRADO ---
    for job in recent_jobs:

        # 1. Deduplicación (vs. historial mensual)
        if job["id"] in historical_ids:
            continue

        # Es un trabajo nuevo.
        monthly_history.append(job)
        jobs_to_send.append(job)

    # c. Guardar el historial mensual actualizado
    save_json(monthly_history, monthly_path)

    # d. Guardar la lista de trabajos de HOY (acumulativo)
    try:
        existing_jobs_today = load_json(LATEST_JOBS_FILE)
    except json.JSONDecodeError:
        existing_jobs_today = []

    # Filtrar por si quedaron jobs de dias anteriores
    today_cutoff = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Usamos un diccionario para manejar la unicidad y la actualización
    all_today_jobs = {
        job["id"]: job
        for job in existing_jobs_today
        if datetime.fromisoformat(job["published_at"]) >= today_cutoff
    }

    # Agregamos los nuevos trabajos, sobreescribiendo duplicados
    for job in jobs_to_send:
        all_today_jobs[job["id"]] = job

    # Convertimos de nuevo a una lista y guardamos
    save_json(list(all_today_jobs.values()), LATEST_JOBS_FILE)

    # e. Actualizar Historial de Tendencias
    trends_history = load_json(TRENDS_HISTORY_FILE)

    # f. Calcular las tendencias para el mes actual con los trabajos nuevos
    current_month_trends = aggregate_trends(jobs_to_send)

    if current_month_trends:
        # g. Encontrar el índice del registro de este mes si existe
        month_index = next(
            (
                i
                for i, item in enumerate(trends_history)
                if item["date"] == current_month_str
            ),
            -1,
        )

        if month_index != -1:
            # Actualizar el registro existente
            existing_entry = trends_history[month_index]
            new_entry = current_month_trends[0]

            existing_entry["total_jobs"] += new_entry["total_jobs"]
            for tag, count in new_entry["tags"].items():
                existing_entry["tags"][tag] = existing_entry["tags"].get(tag, 0) + count
        else:
            # Agregar un nuevo registro mensual
            trends_history.extend(current_month_trends)

        # h. Podar Historial de Tendencias (eliminar entradas de hace más de 12 meses)
        current_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE))
        twelve_months_ago = current_date.replace(
            year=current_date.year - 1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

        trends_history = [
            item
            for item in trends_history
            if datetime.strptime(item["date"], "%Y-%m")
            >= twelve_months_ago.replace(tzinfo=None)
        ]

        # i. Guardar el archivo de tendencias actualizado
        save_json(trends_history, TRENDS_HISTORY_FILE)

    print(f"💾 {len(jobs_to_send)} jobs guardados en {monthly_path}.")
    print(f"💾 {LATEST_JOBS_FILE} y {TRENDS_HISTORY_FILE} actualizados.")

    return jobs_to_send


def delete_jobs_by_ids(job_ids):
    job_ids_to_delete = set(job_ids)
    deleted_count = 0

    # Eliminar de latest_jobs.json
    latest_jobs = load_json(LATEST_JOBS_FILE)
    filtered_latest_jobs = [
        job for job in latest_jobs if job["id"] not in job_ids_to_delete
    ]
    if len(latest_jobs) != len(filtered_latest_jobs):
        save_json(filtered_latest_jobs, LATEST_JOBS_FILE)
        deleted_count += len(latest_jobs) - len(filtered_latest_jobs)

    # Eliminar de los archivos de historial mensual
    for i in range(13):
        current_date = datetime.now(zoneinfo.ZoneInfo(TIMEZONE)) - timedelta(
            days=i * 30
        )
        monthly_path = get_monthly_history_path(current_date.strftime("%Y-%m"))

        if os.path.exists(monthly_path):
            monthly_history = load_json(monthly_path)
            filtered_monthly_history = [
                job for job in monthly_history if job["id"] not in job_ids_to_delete
            ]

            if len(monthly_history) != len(filtered_monthly_history):
                save_json(filtered_monthly_history, monthly_path)
                deleted_count += len(monthly_history) - len(filtered_monthly_history)

    if deleted_count > 0:
        print(f"🗑️ {deleted_count} trabajos eliminados.")
    else:
        print("No se encontraron trabajos con los IDs proporcionados.")

    return deleted_count


def handle_rejected_jobs_file(log_rejected_jobs, verbose=True):
    """
    Deletes the rejected_jobs.json file if log_rejected_jobs is False.
    """
    if not log_rejected_jobs:
        rejected_jobs_path = os.path.join(DATA_DIR, "rejected_jobs.json")
        if os.path.exists(rejected_jobs_path):
            os.remove(rejected_jobs_path)
            if verbose:
                print(f"🗑️ Deleted {rejected_jobs_path} as LOG_REJECTED_JOBS is False.")
