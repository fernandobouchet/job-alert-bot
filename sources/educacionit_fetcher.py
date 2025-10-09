import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils import parse_date_to_iso_utc

BASE_URL = "https://empleos.educacionit.com/trabajos?nivel=junior"

def fetch_educacionit():
    jobs = []

    try:
        r = requests.get(BASE_URL, timeout=15)
        r.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error al obtener EducaciónIT: {e}")
        return jobs

    soup = BeautifulSoup(r.text, "html.parser")
    job_cards = soup.select("div.itemEmpleo")

    for card in job_cards:
        try:
            job_id = f"educacionit-{card.get('id', '').strip()}"

            title_el = card.select_one("h3 a")
            title = title_el.text.strip() if title_el else "Sin título"
            url = urljoin(BASE_URL, title_el["href"]) if title_el else ""

            h3_el = card.select_one("h3")
            company_el = h3_el.find_next_sibling("span") if h3_el else None
            company = company_el.text.strip() if company_el else "No especificada"

            desc_el = card.select_one("p.fs12")
            description = desc_el.text.strip() if desc_el else ""

            fecha_el = card.select_one("p.fechaEmpleo")
            published_at = None
            if fecha_el:
                published_at = parse_date_to_iso_utc(fecha_el.text.strip(), "%d-%m-%Y")

            jobs.append({
                "id": job_id,
                "title": title,
                "company": company,
                "description": description,
                "source": "EducacionIT",
                "seniority": "Junior",
                "salary": "No especificado",
                "url": url,
                "published_at": published_at
            })

        except Exception as e:
            print(f"⚠️ Error al parsear una oferta de EducaciónIT: {e}")
            continue
    return jobs
