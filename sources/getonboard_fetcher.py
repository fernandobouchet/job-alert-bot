import requests
import logging
from dates import its_job_days_old, safe_parse_date_to_ISO
from config import FETCHER_CONFIG

logger = logging.getLogger(__name__)


def fetch_getonboard():
    config = FETCHER_CONFIG.get("GetOnBoardFetcher", {})
    logger.info("Iniciando fetch de GetOnBoard...")

    all_jobs = []
    for category in config.get("categories", []):
        try:
            req = requests.get(
                config.get("base_url").format(category=category),
                params={
                    "per_page": config.get("per_page", 10),
                    "page": config.get("page", 1),
                    "expand": '["company"]',
                },
                timeout=config.get("timeout", 15),
            )
            req.raise_for_status()
            data = req.json().get("data", [])
            logger.info(f"GetOnBoard: {len(data)} trabajos encontrados en la categoría '{category}'.")
        except requests.RequestException as e:
            logger.error(f"Error en fetch de GetOnBoard ({category}): {e}")
            continue

        for job in data:
            try:
                jobData = job.get("attributes", {})
                job_id = f"getonboard-{job.get('id', '').strip()}"
                published_at_ts = jobData.get("published_at")
                published_at_iso = safe_parse_date_to_ISO(published_at_ts)

                if its_job_days_old(published_at_iso):
                    continue

                seniority_id = jobData.get("seniority", {}).get("data", {}).get("id")
                if seniority_id not in config.get("seniority_ids", []):
                    continue

                if not jobData.get("remote"):
                    continue

                if jobData.get("remote_modality") != "fully_remote":
                    continue

                salary_min = jobData.get("min_salary")
                salary_max = jobData.get("max_salary")
                salary = (
                    f"${salary_min} - ${salary_max}"
                    if salary_min and salary_max
                    else f"Mínimo ${salary_min}"
                    if salary_min
                    else f"Máximo ${salary_max}"
                    if salary_max
                    else "No especificado"
                )

                all_jobs.append(
                    {
                        "id": job_id,
                        "title": jobData.get("title", ""),
                        "company": jobData.get("company", {})
                        .get("data", {})
                        .get("attributes", {})
                        .get("name", ""),
                        "description": jobData.get("description", ""),
                        "source": "GetOnBoard",
                        "salary": salary,
                        "url": job.get("links", {}).get("public_url", ""),
                        "published_at": published_at_iso,
                    }
                )
            except Exception as e:
                logger.warning(f"⚠️ Error normalizando job de Getonboard: {e}")
                continue

    logger.info(f"GetOnBoard: Fetch finalizado. Total de trabajos procesados: {len(all_jobs)}")
    return all_jobs
