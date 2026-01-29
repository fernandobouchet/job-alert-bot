from jobspy import scrape_jobs


def fetch_google(config):
    """
    Fetcher specifically for Google Jobs via JobSpy.
    """
    print("🔍 Iniciando búsqueda en Google Jobs...")
    all_jobs = []

    try:
        # Google specific mapping
        # We use the generic 'search_terms' from config but pass it to scrape_jobs
        # We can also explicitly pass google_search_term if needed, but search_term works.

        df = scrape_jobs(
            site_name=["google"],
            search_term=config.get("search_terms"),
            location=config.get("location"),
            results_wanted=config.get("results_wanted", 20),
            hours_old=config.get("hours_old", 72),
            verbose=1 # Helpful for debugging Google specifically
        )
    except Exception as e:
        print(f"❌ Error fetching Google Jobs: {e}")
        return all_jobs

    if df.empty:
        print("⚠️ No se encontraron trabajos en Google Jobs.")
        return all_jobs

    jobs_list = df.to_dict(orient="records")
    print(f"✅ Se obtuvieron {len(jobs_list)} trabajos crudos de Google Jobs.")

    for job in jobs_list:
        try:
            title = str(job.get("title") or "").strip()
            description = str(job.get("description") or "").strip()
            published_at = job.get("date_posted")

            # Google Jobs sometimes returns 'Google' or 'google', we capitalize.
            source = "Google"

            # Validate essential fields
            if not title or not job.get("job_url"):
                continue

            all_jobs.append(
                {
                    "id": str(job.get("id")).strip(),
                    "title": title,
                    "company": str(job.get("company") or "").strip(),
                    "description": description,
                    "source": source,
                    "url": job.get("job_url", ""),
                    "published_at": published_at,
                }
            )
        except Exception as e:
            print(f"⚠️ Error normalizing job from Google Jobs: {e}")
            continue

    return all_jobs
