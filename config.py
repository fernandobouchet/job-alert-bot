GETONBOARD_BASE_URL = "https://www.getonbrd.com/api/v0/categories/{category}/jobs"
EDUCACIONIT_BASE_URL = "https://empleos.educacionit.com/trabajos?nivel=junior"

GETONBOARD_CATEGORIES_IT = [
    "programacion",
    "desarrollo-mobile",
    "data-science-analytics",
    "sysadmin-devops-qa",
    "cybersecurity",
    "machine-learning-ai",
    "technical-support",
]

EXCLUDED_SENIORITYS = ["senior", "sr", "lead", "manager", "director", "head"]

AREA_EXCLUDED_TERMS = [
    "marketing",
    "ventas",
    "sales",
    "recursos",
    "recruiter",
    "diseñador",
    "designer",
    "contador",
    "accountant",
    "administrativo",
    "administrative",
    "finanzas",
    "finance",
    "comercial",
    "commercial",
    "teacher",
    "profesor",
    "professor",
    "arquitecto",
    "architect",
]

SEARCH_TERMS = [
    '("junior" OR "jr" OR "trainee" OR "intern" OR "entry-level") '
    'AND ("programacion" OR "programming" OR '
    '"desarrollo-mobile" OR "mobile development" OR '
    '"data-science-analytics" OR "data analyst" OR "data scientist" OR '
    '"sysadmin-devops-qa" OR "sysadmin" OR "devops" OR "QA" OR "quality assurance" OR '
    '"cybersecurity" OR "security analyst" OR '
    '"machine-learning-ai" OR "AI" OR "machine learning" OR '
    '"technical-support" OR "help desk" OR "support") '
]

FETCHER_CONFIG = {
    "GetOnBoardFetcher": {
        "per_page": 10,
        "page": 1,
        "seniority_ids": [1, 2],  # Trainee y Junior
    },
    "JobSpyFetcher": {
        "site_name": ["indeed", "linkedin"],
        "location": "Buenos Aires, AR",
        "country_indeed": "Argentina",
        "results_wanted": 30,
        "hours_old": 24,
        "linkedin_fetch_description": False,
    },
    "EducacionITFetcher": {},
}
