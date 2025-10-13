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
    "comercial",
    "commercial",
    "finanzas",
    "finance",
    "contador",
    "accountant",
    "administrativo",
    "administrative",
    "gestion",
    "logistica",
    "recursos",
    "recruiter",
    "rrhh",
    "diseñador",
    "designer",
    "arquitecto",
    "architect",
    "teacher",
    "profesor",
    "professor",
    "cliente",
]

SEARCH_TERMS = '(junior OR jr OR trainee OR intern OR "entry-level" OR "associate") AND (developer OR "software engineer" OR "web developer" OR "mobile developer" OR "data analyst" OR "data scientist" OR "sysadmin" OR devops OR "cloud engineer" OR QA OR "quality assurance" OR "cyber security" OR "machine learning" OR "AI" OR "technical support" OR "help desk")'

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
