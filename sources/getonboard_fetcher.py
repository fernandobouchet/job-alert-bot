import requests
from config import FETCHER_CONFIG
from utils.date_utils import get_timestamp_24_hours_ago


def fetch_getonboard():
    config = FETCHER_CONFIG.get("GetOnBoardFetcher", {})

    from_time = get_timestamp_24_hours_ago()

    all_jobs = []
    for category in config.get("categories", []):
        try:
            req = requests.get(
                config.get("base_url").format(category=category),
                params={
                    "per_page": config.get("per_page", 10),
                    "page": config.get("page", 1),
                    "expand": '["company"]',
                    "from": from_time,
                },
                timeout=config.get("timeout", 15),
            )

            req.raise_for_status()
            data = req.json().get("data", [])
        except requests.RequestException as e:
            print(f"Error fetching GetOnBoard ({category}): {e}")
            continue

        for job in data:
            try:
                jobData = job.get("attributes", {})
                job_id = f"getonboard-{job.get('id', '').strip()}"

                published_at_ts = jobData.get("published_at")

                # Extraer seniority y filtrar solo Trainee y Junior
                seniority_id = jobData.get("seniority", {}).get("data", {}).get("id")

                if seniority_id not in config.get("seniority_ids", ["1", "2"]):
                    continue

                if jobData.get("countries") not in ["Argentina", "Remoto"]:
                    continue

                salary_min = jobData.get("min_salary")
                salary_max = jobData.get("max_salary")

                if salary_min and salary_max:
                    salary = f"${salary_min} - ${salary_max}"
                elif salary_min:
                    salary = f"Mínimo ${salary_min}"
                elif salary_max:
                    salary = f"Máximo ${salary_max}"
                else:
                    salary = "No especificado"

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
                        "published_at": published_at_ts,
                    }
                )
            except Exception as e:
                print(f"⚠️ Error normalizing job from Getonboard: {e}")
                continue
    return all_jobs
