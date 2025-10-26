import requests
import logging
from dates import its_job_days_old, safe_parse_date_to_ISO
from bs4 import BeautifulSoup
from config import FETCHER_CONFIG

logger = logging.getLogger(__name__)


def fetch_educacionit():
    config = FETCHER_CONFIG.get("EducacionITFetcher", {})
    logger.info("Iniciando fetch de EducaciónIT...")

    all_jobs = []
    try:
        req = requests.get(config.get("base_url"), timeout=config.get("timeout", 15))
        req.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error en fetch de EducaciónIT: {e}")
        return all_jobs

    soup = BeautifulSoup(req.text, "html.parser")
    job_cards = soup.select("div.itemEmpleo")
    logger.info(f"EducaciónIT: {len(job_cards)} trabajos encontrados.")

    for card in job_cards:
        try:
            date_el = card.select_one("p.fechaEmpleo")
            published_at_iso = safe_parse_date_to_ISO(
                date_el.text.strip() if date_el else None
            )

            if its_job_days_old(published_at_iso):
                continue

            job_id = f"educacionit-{card.get('id', '').strip()}"
            title_el = card.select_one("h3 a")
            title = title_el.text.strip() if title_el else "Sin título"
            url_el = card.select_one("p.fs12 a")
            url = url_el.get("href").strip() if url_el else ""
            company_el = card.select_one("h3").find_next_sibling("span")
            company = company_el.text.strip() if company_el else "No especificada"
            desc_el = card.select_one("p.fs12")
            description = desc_el.text.strip() if desc_el else ""

            salary_div = card.select_one("div[style*='color:#ff7700']")
            salary = (
                salary_div.text.strip().replace("Remuneración:", "").strip()
                if salary_div
                else "No especificado"
            )

            all_jobs.append(
                {
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "description": description,
                    "source": "EducaciónIT",
                    "salary": salary,
                    "url": url,
                    "published_at": published_at_iso,
                }
            )
        except Exception as e:
            logger.warning(f"⚠️ Error normalizando job de EducaciónIT: {e}")
            continue

    logger.info(f"EducaciónIT: Fetch finalizado. Total de trabajos procesados: {len(all_jobs)}")
    return all_jobs
