import requests
from bs4 import BeautifulSoup
from utils import safe_parse_date_to_ISO
from config import EDUCACIONIT_BASE_URL as BASE_URL


def fetch_educacionit():
    all_jobs = []
    try:
        req = requests.get(BASE_URL, timeout=15)
        req.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching EducaciónIT: {e}")
        return all_jobs

    soup = BeautifulSoup(req.text, "html.parser")
    job_cards = soup.select("div.itemEmpleo")

    for card in job_cards:
        try:
            job_id = f"educacionit-{card.get('id', '').strip()}"

            title_el = card.select_one("h3 a")
            title = title_el.text.strip() if title_el else "Sin título"

            url_el = card.select_one("p.fs12 a")
            url = url_el.get("href").strip() if url_el else ""

            company_el = card.select_one("h3").find_next_sibling("span")
            company = company_el.text.strip() if company_el else "No especificada"

            desc_el = card.select_one("p.fs12")
            description = desc_el.text.strip() if desc_el else ""

            salary_el = card.select_one("span.fs10")
            salary = salary_el.text.strip() if salary_el else "No especificado"
            salary = salary.replace("\n", "").strip()

            date_el = card.select_one("p.fechaEmpleo")
            published_at = safe_parse_date_to_ISO(
                date_el.text.strip() if date_el else None
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
                    "published_at": published_at,
                }
            )

        except Exception as e:
            print(f"⚠️ Error normalizing job from EducaciónIT: {e}")
            continue
    return all_jobs
