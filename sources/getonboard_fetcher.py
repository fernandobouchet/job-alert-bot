import requests
from config import (
    FETCHER_CONFIG,
    GETONBOARD_CATEGORIES_IT,
    GETONBOARD_BASE_URL as BASE_URL,
)
from utils import safe_parse_date_to_ISO


def fetch_getonboard():
    all_jobs = []
    for category in GETONBOARD_CATEGORIES_IT:
        try:
            req = requests.get(
                BASE_URL.format(category=category),
                params={
                    "per_page": FETCHER_CONFIG["GetOnBoardFetcher"]["per_page"],
                    "page": FETCHER_CONFIG["GetOnBoardFetcher"]["page"],
                    "expand": '["company"]',
                },
                timeout=15,
            )

            req.raise_for_status()
            data = req.json().get("data", [])
        except requests.RequestException as e:
            print(f"Error fetching GetOnBoard ({category}): {e}")
            continue

        for job in data:
            try:
                jobData = job.get("attributes", {})

                # Extraer seniority y filtrar solo Trainee y Junior
                seniority_id = jobData.get("seniority", {}).get("data", {}).get("id")
                if (
                    seniority_id
                    not in FETCHER_CONFIG["GetOnBoardFetcher"]["seniority_ids"]
                ):
                    continue

                if jobData.get("remote") is False:
                    continue

                if jobData.get("remote_modality") not in ["fully_remote"]:
                    continue

                published_at_ts = jobData.get("published_at")
                published_at_iso = safe_parse_date_to_ISO(published_at_ts)

                salary_min = jobData.get("min_salary")
                salary_max = jobData.get("max_salary")
                salary = (
                    f"${salary_min} - ${salary_max}"
                    if salary_min and salary_max
                    else "No especificado"
                )

                all_jobs.append(
                    {
                        "id": job.get("id"),
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
                print(f"⚠️ Error normalizing job from Getonboard: {e}")
                continue
    return all_jobs
