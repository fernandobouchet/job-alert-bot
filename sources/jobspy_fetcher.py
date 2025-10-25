from jobspy import scrape_jobs
from config import FETCHER_CONFIG
from utils.dates_utils import safe_parse_date_to_ISO


def fetch_jobspy():
    config = FETCHER_CONFIG.get("JobSpyFetcher", {})

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
    except Exception as e:
        print(f"Error fetching Jobspy: {e}")
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
            print(f"⚠️ Error normalizing job from Jobspy: {e}")
            continue
    return all_jobs
