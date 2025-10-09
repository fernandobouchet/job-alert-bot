from jobspy import scrape_jobs
from utils import parse_date_to_iso_utc, safe_parse_date

def fetch_jobspy():
    """
    Obtiene ofertas de Indeed y LinkedIn usando Job Spy y las normaliza
    para integrarlas en el bot.
    Solo filtra por seniority en el título, no en la descripción.
    """
    jobs = []

    try:
        df = scrape_jobs(
            site_name=["indeed", "linkedin"],
            search_term=(
                '"junior IT" OR "trainee IT" OR "junior developer" OR "trainee developer" '
                'OR "junior programmer" OR "trainee programmer" OR "junior software" '
                'OR "trainee software" OR "junior QA" OR "trainee QA" OR "junior support" '
                'OR "technical support" OR "help desk" OR "desarrollador junior" '
                'OR "programador junior" OR "desarrollador trainee" OR "programador trainee" '
                'OR "soporte técnico" OR "QA junior" OR "QA trainee" OR "data junior" '
                'OR "infraestructura junior" '
                '-marketing -ventas -recursos -recruiter -diseñador -contador '
                '-administrativo -finanzas -comercial -teacher -profesor'
            ),
            location="Argentina",
            country_indeed="Argentina",
            results_wanted=30,
            hours_old=24,
            linkedin_fetch_description=False
        )

    except Exception as e:
        print(f"❌ Error al obtener jobs con Job Spy: {e}")
        return jobs

    jobs_list = df.to_dict(orient="records")

    for j in jobs_list:
        try:
            title = str(j.get("title") or "").strip().lower()
            if any(s in title for s in ["senior", "sr", "lead", "manager"]):
                continue

            published_at = safe_parse_date(j.get("date_posted"))

            jobs.append({
                "id": str(j.get("id")).strip(),
                "title": str(j.get("title") or "").strip(),
                "company": str(j.get("company") or "").strip(),
                "description": str(j.get("description") or "").strip(),
                "source": str(j.get("site_name") or "").capitalize(),
                "seniority": "Junior",
                "salary": j.get("salary", "No especificado"),
                "url": j.get("job_url", ""),
                "published_at": published_at
            })

        except Exception as e:
            print(f"⚠️ Error normalizando job {j.get('title', '')}: {e}")
            continue

    return jobs
