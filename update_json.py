import json
from datetime import datetime, timezone

def update_json(new_jobs, path="jobs.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            old_jobs = json.load(f)
    except FileNotFoundError:
        old_jobs = []

    now = datetime.now(timezone.utc)
    old_ids = {j['id'] for j in old_jobs}
    jobs_to_send = []

    for job in new_jobs:
        job['date_scraped'] = now.isoformat()
        if job['id'] not in old_ids:
            old_jobs.append(job)
            jobs_to_send.append(job)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(old_jobs, f, indent=2, ensure_ascii=False)

    return jobs_to_send
