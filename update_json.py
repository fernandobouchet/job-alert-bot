import json
import os
from datetime import datetime, timedelta, timezone
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
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_monthly_history_path(date_str):
    # Formato AAAA_MM
    month_str = datetime.strptime(date_str[:10], "%Y-%m-%d").strftime("%Y_%m")
    return os.path.join(DATA_DIR, f"jobs_{month_str}.json")


def aggregate_trends(jobs_list):

    trends = defaultdict(lambda: {"total_jobs": 0, "tags": defaultdict(int)})

    for job in jobs_list:
        # Usamos solo la parte de la fecha (AAAA-MM-DD) para la clave de agregación
        date_key = job["date_scraped"][:10]

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


def update_json(recent_jobs):
    if not recent_jobs:
        return []

    print("⚙️ Applying filters and enriching data...")

    # La fecha de escaneo (AAAA-MM-DD)
    current_date_str = recent_jobs[0].get(
        "date_scraped", datetime.now(timezone.utc).isoformat()
    )[:10]

    # a. Determinar el path del archivo mensual y cargarlo
    monthly_path = get_monthly_history_path(current_date_str)
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

    # d. Guardar la lista de los últimos trabajos nuevos (para el frontend)
    save_json(jobs_to_send, LATEST_JOBS_FILE)

    # e. Actualizar Historial de Tendencias
    trends_history = load_json(TRENDS_HISTORY_FILE)

    # f. Calcular las tendencias para el día de hoy con los trabajos nuevos
    today_trends = aggregate_trends(jobs_to_send)

    if today_trends:
        # g. Encontrar el índice del registro de hoy si existe
        today_index = next(
            (
                i
                for i, item in enumerate(trends_history)
                if item["date"] == current_date_str
            ),
            -1,
        )

        if today_index != -1:
            # Sobrescribir el registro de hoy (Si el bot corre varias veces al día)
            trends_history[today_index] = today_trends[0]
        else:
            # Agregar un nuevo registro diario
            trends_history.extend(today_trends)

        # h. Podar Historial de Tendencias (eliminar entradas de hace más de 365 días)
        one_year_ago = datetime.now() - timedelta(days=365)
        trends_history = [
            item
            for item in trends_history
            if datetime.strptime(item["date"], "%Y-%m-%d") > one_year_ago
        ]

        # i. Guardar el archivo de tendencias actualizado
        save_json(trends_history, TRENDS_HISTORY_FILE)

    print(f"💾 {len(jobs_to_send)} jobs guardados en {monthly_path}.")
    print(f"💾 {LATEST_JOBS_FILE} y {TRENDS_HISTORY_FILE} actualizados.")

    return jobs_to_send
