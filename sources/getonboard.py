import requests

# Categorías relevantes de IT
CATEGORIES_IT = [
    "programacion",
    "desarrollo-mobile",
    "data-science-analytics",
    "sysadmin-devops-qa",
    "cybersecurity",
    "machine-learning-ai",
    "technical-support"
]

BASE = "https://www.getonbrd.com/api/v0/categories/{category}/jobs"

def fetch_getonboard():
    all_jobs = []
    for category in CATEGORIES_IT:
        try:
            r = requests.get(
                BASE.format(category=category),
                params={
                    "per_page": 10,                    
                    "page": 1,
                    "expand": '["company"]',
                },
                timeout=15
            )

            r.raise_for_status()
            data = r.json().get("data", [])
        except requests.RequestException as e:
            print(f"Error fetching GetOnBoard ({category}): {e}")
            continue

        for j in data:
            a = j.get("attributes", {})

            # Extraer seniority y filtrar solo Trainee y Junior
            seniority_data = a.get("seniority", {}).get("data", {})
            seniority_id = seniority_data.get("id")
            if seniority_id not in [1, 2]:
                continue
            seniority = "Trainee" if seniority_id == 1 else "Junior"


            min_s = a.get("min_salary")
            max_s = a.get("max_salary")
            if min_s and max_s:
                salary = f"${min_s} - ${max_s}"
            elif min_s:
                salary = f"${min_s}"
            elif max_s:
                salary = f"${max_s}"
            else:
                salary = "No especificado"

            # URL y ID
            url = j.get("links", {}).get("public_url", "")
            job_id = j.get("id")  # único por GetOnBoard

            # Empresa
            company = a.get("company", {}).get("data", {}).get("attributes", {}).get("name", "")

            # Agregar job simplificado
            all_jobs.append({
                "id": job_id,
                "title": a.get("title", ""),
                "company": company,
                "description": a.get("description", ""),
                "source": "GetOnBoard",
                "seniority": seniority,
                "salary": salary,
                "url": url,
                "published_at": a.get("published_at" "")
            })

    return all_jobs
