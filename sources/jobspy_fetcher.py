from jobspy import scrape_jobs
from config import (
    AREA_EXCLUDED_TERMS,
    EXCLUDED_SENIORITYS,
    FETCHER_CONFIG,
    SEARCH_TERMS,
)
from utils import safe_parse_date_to_ISO


def fetch_jobspy():
    all_jobs = []

    exclude_query_str = " ".join(f"-{term}" for term in AREA_EXCLUDED_TERMS)
    search_term_str = " ".join(SEARCH_TERMS) + " " + exclude_query_str

    try:
        df = scrape_jobs(
            site_name=["indeed", "linkedin"],
            search_term=search_term_str,
            location=FETCHER_CONFIG["JobSpyFetcher"]["location"],
            country_indeed=FETCHER_CONFIG["JobSpyFetcher"]["country_indeed"],
            results_wanted=FETCHER_CONFIG["JobSpyFetcher"]["results_wanted"],
            hours_old=FETCHER_CONFIG["JobSpyFetcher"]["hours_old"],
            linkedin_fetch_description=FETCHER_CONFIG["JobSpyFetcher"][
                "linkedin_fetch_description"
            ],
        )
    except Exception as e:
        print(f"Error fetching Jobspy: {e}")
        return all_jobs

    jobs_list = df.to_dict(orient="records")

    for job in jobs_list:
        try:
            title = str(job.get("title") or "").strip()
            description = str(job.get("description") or "").strip()

            title_lower = title.lower()
            if any(s in title_lower for s in EXCLUDED_SENIORITYS):
                continue

            published_at = safe_parse_date_to_ISO(job.get("date_posted"))

            all_jobs.append(
                {
                    "id": str(job.get("id")).strip(),
                    "title": title,
                    "company": str(job.get("company") or "").strip(),
                    "description": description,
                    "source": str(job.get("site") or "").capitalize(),
                    "salary": job.get("salary", "No especificado"),
                    "url": job.get("job_url", ""),
                    "published_at": published_at,
                }
            )

        except Exception as e:
            print(f"⚠️ Error normalizing job from Jobspy: {e}")
            continue
    return all_jobs
