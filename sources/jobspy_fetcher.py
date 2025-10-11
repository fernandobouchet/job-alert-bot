from jobspy import scrape_jobs
from utils import safe_parse_date

def fetch_jobspy():
    jobs = []

    area_exclude_terms = [
    'marketing', 'ventas', 'sales',
    'recursos', 'recruiter',
    'diseñador', 'designer',
    'contador', 'accountant',
    'administrativo', 'administrative',
    'finanzas', 'finance',
    'comercial', 'commercial',
    'teacher', 'profesor', 'professor',
    'arquitecto', 'architect'
    ]

    exclude_query_str = " ".join(f"-{term}" for term in area_exclude_terms)

    try:
        df = scrape_jobs(
            site_name=["indeed", "linkedin"],
            search_term = (
                '("junior" OR "jr" OR "trainee" OR "intern" OR "entry-level") '
                'AND ("programacion" OR "programming" OR '
                '"desarrollo-mobile" OR "mobile development" OR '
                '"data-science-analytics" OR "data analyst" OR "data scientist" OR '
                '"sysadmin-devops-qa" OR "sysadmin" OR "devops" OR "QA" OR "quality assurance" OR '
                '"cybersecurity" OR "security analyst" OR '
                '"machine-learning-ai" OR "AI" OR "machine learning" OR '
                '"technical-support" OR "help desk" OR "support") '
                f"{exclude_query_str}"
            ),    
            location="Buenos Aires, AR",
            country_indeed="Argentina",
            results_wanted=30,
            hours_old=24,
            linkedin_fetch_description=False
        )

        
    except Exception as e:
        print(f"❌ Error al obtener jobs con JobSpy: {e}")
        return jobs

    jobs_list = df.to_dict(orient="records")

    for j in jobs_list:
        try:
            title = str(j.get("title") or "").strip()
            description = str(j.get("description") or "").strip()

            title_lower = title.lower()
            if any(s in title_lower for s in ["senior", "sr", "lead", "manager", "director", "head"]):
                continue

            published_at = safe_parse_date(j.get("date_posted"))

            jobs.append({
                "id": str(j.get("id")).strip(),
                "title": title,
                "company": str(j.get("company") or "").strip(),
                "description": description,
                "source": str(j.get("site") or "").capitalize(),
                "salary": j.get("salary", "No especificado"),
                "url": j.get("job_url", ""),
                "published_at": published_at
            })

        except Exception as e:
            print(f"⚠️ Error normalizando job {j.get('title', '')}: {e}")
            continue

    return jobs
