TIMEZONE = "America/Argentina/Buenos_Aires"

JOBSPY_SEARCH_TERMS = '(junior OR jr OR "jr." OR trainee OR "entry level" OR pasante OR intern OR graduate OR grad OR asociado OR associate OR graduado OR becario) (IT OR sistemas OR developer OR desarrollador OR software OR engineer OR ingeniero OR programador OR programmer OR technology OR tecnología OR tech OR informática OR computing OR computación OR redes OR network OR ciberseguridad OR cybersecurity OR security OR front OR frontend OR back OR backend OR "full stack" OR "full-stack" OR qa OR tester OR support OR sysadmin OR data OR datos OR cloud OR analyst OR analista OR devops OR ux OR ui OR designer OR "machine learning" OR "inteligencia artificial")'


DAYS_OLD_TRHESHOLD = 1

HOURS_OLD_THRESHOLD = 14

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
        "results_wanted": 45,
        "hours_old": HOURS_OLD_THRESHOLD,
        "linkedin_fetch_description": True,
        "search_terms": JOBSPY_SEARCH_TERMS,
    },
    "EducacionITFetcher": {
        "base_url": "https://empleos.educacionit.com/trabajos?nivel=junior",
        "timeout": 15,
    },
}


LOG_REJECTED_JOBS = True
