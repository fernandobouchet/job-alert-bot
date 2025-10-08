import json
from datetime import datetime, timezone

def update_json(new_jobs, path="jobs.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            old_jobs = json.load(f)
    except FileNotFoundError:
        old_jobs = []

    now = datetime.now(timezone.utc)

    for job in new_jobs:
        job['id'] = job.get('id', job['id'])
        job['date_scraped'] = now.isoformat()
        if job['id'] not in [j['id'] for j in old_jobs]:
            old_jobs.append(job)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(old_jobs, f, indent=2, ensure_ascii=False)
