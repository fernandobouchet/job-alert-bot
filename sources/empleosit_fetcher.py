from datetime import datetime
import re

import requests
from bs4 import BeautifulSoup
from config import FETCHER_CONFIG


def fetch_empleosit():
    config = FETCHER_CONFIG.get("EmpleosITFetcher", {})

    all_jobs = []
    try:
        req = requests.get(config.get("base_url"), timeout=config.get("timeout", 15))
        req.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching EmpleosIT: {e}")
        return all_jobs

    soup = BeautifulSoup(req.text, "html.parser")

    job_cards = soup.select("div.listing-section")

    for card in job_cards:
        try:
            title_tag = card.select_one(".listing-title a[href]")

            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            url = title_tag.get("href") if title_tag else "N/A"

            job_id = None

            if url and url != "N/A":
                match = re.search(r"/display-job/(\d+)/", url)

                if match:
                    job_number = match.group(1)
                    job_id = f"empleosit-{job_number}"

            if not job_id:
                job_id = f"empleosit-fallback-{hash(title)}"

            company_el = card.select_one(".captions-field.company-ico")
            company = company_el.text.strip() if company_el else "No especificada"

            description_tag = card.select_one(".show-brief")
            descripcion_full = (
                description_tag.get_text(strip=True) if description_tag else "N/A"
            )

            if descripcion_full != "N/A" and descripcion_full.startswith(
                "Descripción del empleo:"
            ):
                description = descripcion_full.replace(
                    "Descripción del empleo:", "", 1
                ).strip()
            else:
                description = descripcion_full

            if url and url != "N/A":
                try:
                    detail_req = requests.get(url, timeout=config.get("timeout", 15))
                    detail_req.raise_for_status()

                    detail_soup = BeautifulSoup(detail_req.text, "html.parser")
                    main_container = detail_soup.select_one(
                        "#col-wide > div.displayFieldBlock > div.displayField"
                    )

                    if main_container:
                        content_tags = main_container.find_all(["p", "h3", "ul"])

                        full_text_parts = []
                        for tag in content_tags:
                            tag_text = tag.get_text(strip=True)
                            if tag_text:
                                if tag.name == "ul":
                                    li_texts = [
                                        li.get_text(strip=True)
                                        for li in tag.select("li")
                                        if li.get_text(strip=True)
                                    ]
                                    if li_texts:
                                        full_text_parts.append(
                                            "\n" + "\n".join(li_texts)
                                        )
                                else:
                                    full_text_parts.append(tag_text)

                        if full_text_parts:
                            description = "\n\n".join(full_text_parts)
                        else:
                            print(
                                f"No se encontró contenido estructurado para: {title}"
                            )
                            description = descripcion_full
                    else:
                        print(
                            f"No se encontró el contenedor principal (div.displayField) para: {title}"
                        )
                        description = descripcion_full
                except requests.RequestException as e:
                    print(f"⚠️ Error al obtener la página de detalle para {url}: {e}")
                    description = descripcion_full

            print(description)
            salary = "No especificado"

            date_el = card.select_one(".captions-field.posted-ico")

            published_at_str = date_el.get_text(strip=True) if date_el else None

            published_at = None
            if published_at_str:
                try:
                    # Convert from DD-MM-YYYY to YYYY-MM-DD
                    published_at = datetime.strptime(
                        published_at_str, "%d-%m-%Y"
                    ).strftime("%Y-%m-%d")
                except ValueError:
                    # Keep the original string if parsing fails
                    published_at = published_at_str

            all_jobs.append(
                {
                    "id": job_id,
                    "title": title,
                    "company": company,
                    "description": description,
                    "source": "EmpleosIT",
                    "salary": salary,
                    "url": url,
                    "published_at": published_at,
                }
            )

        except Exception as e:
            print(f"⚠️ Error normalizing job from EmpleosIT: {e}")
    return all_jobs
