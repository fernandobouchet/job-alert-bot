import os
import httpx

REVALIDATION_SECRET = os.environ.get("REVALIDATION_SECRET")
BASE_URL = os.environ.get("BASE_URL")


async def revalidate_path(path: str):
    async with httpx.AsyncClient() as client:
        params = {"secret": REVALIDATION_SECRET, "path": path}
        r = await client.get(BASE_URL, params=params)
        if r.status_code != 200:
            print(f"Error revalidando {path}: {r.text}")
        else:
            print(f"✅ Revalidado {path} correctamente")
