from jobspy import scrape_jobs
import logging
from dates import safe_parse_date_to_ISO
from config import FETCHER_CONFIG

logger = logging.getLogger(__name__)


def fetch_jobspy():
    config = FETCHER_CONFIG.get("JobSpyFetcher", {})
    logger.info("Iniciando fetch de JobSpy...")

    all_jobs = []

    try:
        df = scrape_jobs(
            site_name=config.get("site_name", []),
            search_term=config.get("search_terms"),
            location=config.get("location"),
            country_indeed=config.get("country_indeed"),
            results_wanted=config.get("results_wanted"),
            hours_old=config.get("hours_old"),
            linkedin_fetch_description=config.get("linkedin_fetch_description", False),
        )
        if df is not None:
            logger.info(f"JobSpy: {len(df)} trabajos encontrados.")
        else:
            logger.info("JobSpy: No se encontraron trabajos.")
            df = pd.DataFrame()

    except Exception as e:
        logger.error(f"Error en fetch de JobSpy: {e}")
        return all_jobs

    jobs_list = df.to_dict(orient="records")

    for job in jobs_list:
        try:
            title = str(job.get("title") or "").strip()
            description = str(job.get("description") or "").strip()
            published_at_iso = safe_parse_date_to_ISO(job.get("date_posted"))

            all_jobs.append(
                {
                    "id": str(job.get("id")).strip(),
                    "title": title,
                    "company": str(job.get("company") or "").strip(),
                    "description": description,
                    "source": str(job.get("site") or "").capitalize(),
                    "salary": job.get("salary", "No especificado"),
                    "url": job.get("job_url", ""),
                    "published_at": published_at_iso,
                }
            )
        except Exception as e:
            logger.warning(f"⚠️ Error normalizando job de JobSpy: {e}")
            continue

    logger.info(f"JobSpy: Fetch finalizado. Total de trabajos procesados: {len(all_jobs)}")
    return all_jobs
