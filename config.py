import os
from sources.getonboard_fetcher import fetch_getonboard
from sources.educacionit_fetcher import fetch_educacionit
from sources.jobspy_fetcher import fetch_jobspy
from sources.empleosit_fetcher import fetch_empleosit

TIMEZONE = "America/Argentina/Buenos_Aires"

UPLOAD_TO_FIREBASE = True

REVALIDATE_CACHE = True

ACCEPTED_JOBS_RETENTION_DAYS = 7

REJECTED_JOBS_RETENTION_DAYS = 7

DAYS_OLD_THRESHOLD = 1

JOBSPY_HOURS_OLD = 11

JOBSPY_SEARCH_TERMS = (
    '(junior OR jr OR trainee OR "entry level" OR pasante OR intern OR graduate) '
    "AND "
    "("
    "IT OR sistemas OR software OR technology OR tecnología OR informática OR "
    "developer OR desarrollador OR engineer OR ingeniero OR programmer OR programador OR "
    "frontend OR backend OR fullstack OR devops OR sysadmin OR "
    "qa OR tester OR security OR cybersecurity OR ciberseguridad OR "
    "cloud OR network OR redes OR "
    '"data analyst" OR "data engineer" OR "data science" OR '
    '"machine learning" OR '
    '"technical support" OR "soporte técnico" OR '
    '"ux/ui" OR "ux designer" OR "ui designer"'
    ")"
)

FETCHER_CONFIG = {
    "GetOnBoardFetcher": {
        "base_url": "https://www.getonbrd.com/api/v0/categories/{category}/jobs",
        "per_page": 20,
        "page": 1,
        "timeout": 15,
        "seniority_ids": [1, 2],
        "categories": [
            "programacion",
            "desarrollo-mobile",
            "data-science-analytics",
            "sysadmin-devops-qa",
            "cybersecurity",
            "machine-learning-ai",
            "technical-support",
        ],
    },
    "JobSpyFetcher": {
        "name": "Argentina (LinkedIn & Indeed)",
        "site_name": ["linkedin", "indeed"],
        "location": "Buenos Aires, AR",
        "country_indeed": "Argentina",
        "results_wanted": 50,
        "hours_old": JOBSPY_HOURS_OLD,
        "linkedin_fetch_description": True,
        "search_terms": JOBSPY_SEARCH_TERMS,
    },
    "EducacionITFetcher": {
        "base_url": "https://empleos.educacionit.com/trabajos?nivel=junior",
        "timeout": 15,
    },
    "EmpleosITFetcher": {
        "base_url": "https://www.empleosit.com.ar/search-results-jobs/?searchId=1762136439.6851&action=search&page=1&listings_per_page=20&view=list&sorting_field=activation_date&sorting_order=DESC",
        "timeout": 15,
    },
}

AVAILABLE_SOURCES = {
    "getonboard": fetch_getonboard,
    "educacionit": fetch_educacionit,
    "jobspy": fetch_jobspy,
    "empleosit": fetch_empleosit,
}


def get_sources():
    source_names = os.getenv("JOB_SOURCES", "").split(",")
    if not source_names or source_names == [""]:
        print("No JOB_SOURCES environment variable found, using all available sources.")
        return list(AVAILABLE_SOURCES.values())

    sources = []
    print(f"JOB_SOURCES found, using: {source_names}")
    for name in source_names:
        fetcher = AVAILABLE_SOURCES.get(name.strip())
        if fetcher:
            sources.append(fetcher)
        else:
            print(f"Warning: Source '{name}' not found. It will be ignored.")
    return sources