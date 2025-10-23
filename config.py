UPLOAD_TO_FIREBASE = True

LOG_JSON_TO_GIT = True

DAYS_OLD_TRHESHOLD = 1

HOURS_OLD_THRESHOLD = 14

TIMEZONE = "America/Argentina/Buenos_Aires"

SOURCES_BYPASS_SCORING = ["EducaciónIT", "GetOnBoard"]

JOBSPY_SEARCH_TERMS = (
    '(junior OR jr OR trainee OR "entry level" OR pasante OR intern OR graduate OR asociado OR associate OR graduado OR becario) '
    "("
    "IT OR sistemas OR developer OR desarrollador OR engineer OR ingeniero OR programmer OR programador OR "
    "software OR technology OR tecnología OR informática OR computing OR computación OR "
    "frontend OR backend OR fullstack OR devops OR sysadmin OR "
    '"data analyst" OR "data engineer" OR "data science" OR '
    "qa OR tester OR security OR ciberseguridad OR cybersecurity OR "
    'cloud OR redes OR network OR "technical support" OR "soporte técnico" OR '
    '"ux/ui" OR "ux designer" OR "ui designer" OR '
    '"machine learning" OR "inteligencia artificial"'
    ")"
)

FETCHER_CONFIG = {
    "GetOnBoardFetcher": {
        "base_url": "https://www.getonbrd.com/api/v0/categories/{category}/jobs",
        "per_page": 10,
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
        "site_name": ["indeed", "linkedin"],
        "location": "Buenos Aires, AR",
        "country_indeed": "Argentina",
        "results_wanted": 50,
        "hours_old": HOURS_OLD_THRESHOLD,
        "linkedin_fetch_description": True,
        "search_terms": JOBSPY_SEARCH_TERMS,
    },
    "EducacionITFetcher": {
        "base_url": "https://empleos.educacionit.com/trabajos?nivel=junior",
        "timeout": 15,
    },
}
