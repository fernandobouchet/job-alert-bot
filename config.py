import os
from sources.getonboard_fetcher import fetch_getonboard
from sources.educacionit_fetcher import fetch_educacionit
from sources.jobspy_fetcher import fetch_jobspy
from sources.empleosit_fetcher import fetch_empleosit

UPLOAD_TO_FIREBASE = True

REVALIDATE_CACHE = True

JOBS_RETENTION_DAYS = 5

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

AVAILABLE_SOURCES = {
    "getonboard": fetch_getonboard,
    "educacionit": fetch_educacionit,
    "jobspy": fetch_jobspy,
    "google": fetch_jobspy,
    "empleosit": fetch_empleosit,
}

FETCHER_CONFIG = {
    "getonboard": {
        "base_url": "https://www.getonbrd.com/api/v0/categories/{category}/jobs",
        "per_page": 20,
        "page": 1,
        "timeout": 15,
        "seniority_ids": [1, 2],
        "categories": [
            "programacion",
            "diseno-ux",
            "desarrollo-mobile",
            "data-science-analytics",
            "sysadmin-devops-qa",
            "cybersecurity",
            "machine-learning-ai",
            "technical-support",
        ],
    },
    "jobspy": {
        "name": "Argentina (LinkedIn & Indeed)",
        "site_name": ["linkedin", "indeed"],
        "location": "Buenos Aires, AR",
        "country_indeed": "Argentina",
        "results_wanted": 50,
        "hours_old": JOBSPY_HOURS_OLD,
        "linkedin_fetch_description": True,
        "search_terms": JOBSPY_SEARCH_TERMS,
    },
    "google": {
        "name": "Google Jobs",
        "site_name": ["google"],
        "location": "Argentina",
        "results_wanted": 50,
        "hours_old": JOBSPY_HOURS_OLD,
        "search_terms": JOBSPY_SEARCH_TERMS,
    },
    "educacionit": {
        "base_url": "https://empleos.educacionit.com/trabajos?nivel=junior",
        "timeout": 15,
    },
    "empleosit": {
        "base_url": "https://www.empleosit.com.ar/search-results-jobs/?searchId=1762136439.6851&action=search&page=1&listings_per_page=20&view=list&sorting_field=activation_date&sorting_order=DESC",
        "timeout": 15,
    },
}


def get_sources():
    source_names_str = os.getenv("JOB_SOURCES")

    if not source_names_str:
        print("No JOB_SOURCES environment variable found, using all available sources.")
        source_names = list(AVAILABLE_SOURCES.keys())
    else:
        source_names = [name.strip() for name in source_names_str.split(",")]
        print(f"JOB_SOURCES found, using: {source_names}")

    sources_to_run = []
    for name in source_names:
        fetcher_func = AVAILABLE_SOURCES.get(name)
        fetcher_config = FETCHER_CONFIG.get(name)

        if fetcher_func and fetcher_config:
            sources_to_run.append((fetcher_func, fetcher_config))
        else:
            print(
                f"Warning: Source '{name}' not found or missing config. It will be ignored."
            )

    return sources_to_run
