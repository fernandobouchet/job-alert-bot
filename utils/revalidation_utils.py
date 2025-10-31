import asyncio
import os
import httpx

REVALIDATION_SECRET = os.getenv("REVALIDATION_SECRET")
BASE_URL = os.getenv("BASE_URL")


async def revalidate_path(path: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            params = {"secret": REVALIDATION_SECRET, "path": path}
            r = await client.get(BASE_URL, params=params)
            if r.status_code != 200:
                print(f"⚠️ Error revalidando {path}: {r.status_code} - {r.text}")
            else:
                print(f"✅ Revalidado {path} correctamente")
    except asyncio.CancelledError:
        print(f"⚠️ Revalidación de {path} cancelada")
        raise
    except Exception as e:
        print(f"❌ Error en revalidación de {path}: {e}")
